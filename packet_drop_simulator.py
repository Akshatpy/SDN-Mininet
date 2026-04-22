#!/usr/bin/env python3
"""
Packet Drop Simulator - SDN Flow Rules based Packet Loss Simulation
Author: Student
Assignment: Implement packet dropping using OpenFlow rules in Mininet

This script implements:
1. Mininet topology (2 hosts, 1 switch)
2. Packet dropping logic based on flow rules
3. Flow rule installation and management
4. Packet loss measurement
"""

from mininet.net import Mininet
from mininet.node import OVSController, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import subprocess
import time


def enable_drop_rule_on_switch(src_ip='10.0.0.1', dst_ip='10.0.0.2'):
    """Install a high-priority OpenFlow drop rule for a specific IPv4 flow."""
    flow = f"priority=200,ip,nw_src={src_ip},nw_dst={dst_ip},actions=drop"
    result = subprocess.run(
        ['ovs-ofctl', '-O', 'OpenFlow13', 'add-flow', 's1', flow],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, (result.stderr or result.stdout).strip()


def disable_drop_rule_on_switch(src_ip='10.0.0.1', dst_ip='10.0.0.2'):
    """Remove only the previously installed drop rule, keep other rules intact."""
    flow_match = f"priority=200,ip,nw_src={src_ip},nw_dst={dst_ip}"
    result = subprocess.run(
        ['ovs-ofctl', '-O', 'OpenFlow13', '--strict', 'del-flows', 's1', flow_match],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, (result.stderr or result.stdout).strip()

def create_topology():
    """
    Create a simple network topology:
    - 4 hosts (h1, h2, h3, h4)
    - 1 OpenFlow switch (s1)
    - Connect to Ryu controller
    """
    print("[*] Creating network topology...")
    
    # Create Mininet object with remote controller
    net = Mininet(
        controller=RemoteController,
        link=TCLink
    )
    
    # Add controller (Ryu running on localhost:6633)
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    
    # Add switch
    s1 = net.addSwitch('s1', dpid='0000000000000001')
    
    # Add hosts
    h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
    h3 = net.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
    h4 = net.addHost('h4', ip='10.0.0.4/24', mac='00:00:00:00:00:04')
    
    # Connect hosts to switch
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)
    
    print("[+] Topology created successfully!")
    print("[+] Hosts: h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)")
    print("[+] Switch: s1 (dpid=0000000000000001)")
    
    return net


def start_network(net):
    """Start the network"""
    print("[*] Starting network...")
    net.start()
    print("[+] Network started!")
    print("[*] Controller IP: 127.0.0.1:6633")
    
    # Give time for controller to connect
    time.sleep(2)
    
    return net


def display_menu():
    """Display interactive menu"""
    print("\n" + "="*60)
    print("SDN PACKET DROP SIMULATOR - Control Menu")
    print("="*60)
    print("1. Test Normal Connectivity (no drops)")
    print("2. Enable DROP Rule (h1 -> h2)")
    print("3. Disable DROP Rule")
    print("4. Show Switch Flow Tables")
    print("5. Show Host Information")
    print("6. Exit & Enter Mininet CLI")
    print("="*60)


def test_connectivity(net, drop_enabled=False):
    """Test network connectivity with ping"""
    print("\n[*] Testing connectivity...")
    h1, h2, h3, h4 = net.get('h1', 'h2', 'h3', 'h4')
    
    status = "WITH DROP RULE" if drop_enabled else "WITHOUT DROP RULE"
    print(f"\n[TEST] Ping h1 -> h2 {status}")
    result = h1.cmd('ping -c 4 10.0.0.2')
    print(result)
    
    if drop_enabled:
        # Count packet loss
        if "0% packet loss" in result:
            print("[!] WARNING: Drop rule not working - packets still going through!")
        else:
            print("[+] DROP RULE WORKING: Packets were dropped!")


def show_flow_tables(net):
    """Display OpenFlow flow tables from switch"""
    print("\n[*] Displaying switch flow tables...")
    s1 = net.get('s1')
    
    print("\n" + "="*60)
    print("SWITCH S1 - OpenFlow Rules")
    print("="*60)
    
    # Use ovs-ofctl to display flows
    result = subprocess.run(
        ['ovs-ofctl', '-O', 'OpenFlow13', 'dump-flows', 's1'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("Could not display flows. Make sure switch is running.")


def show_host_info(net):
    """Display host information"""
    print("\n" + "="*60)
    print("HOST INFORMATION")
    print("="*60)
    
    hosts = net.hosts
    for host in hosts:
        print(f"\nHost: {host.name}")
        print(f"  IP Address: {host.IP()}")
        print(f"  MAC Address: {host.MAC()}")
        print(f"  Status: {'Up' if host.cmd('ping -c 1 127.0.0.1') else 'Down'}")


def main():
    """Main function"""
    setLogLevel('info')
    
    # Create topology
    net = create_topology()
    
    # Start network
    net = start_network(net)
    
    print("\n" + "="*60)
    print("IMPORTANT: Start Ryu controller in another terminal with:")
    print("  ryu-manager ryu_packet_drop_controller.py --observe-links")
    print("="*60)
    input("\nPress Enter once Ryu controller is running...")
    
    # Interactive menu
    try:
        while True:
            display_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                test_connectivity(net, drop_enabled=False)
            elif choice == '2':
                print("\n[*] Enabling DROP rule for h1 -> h2 traffic...")
                ok, msg = enable_drop_rule_on_switch('10.0.0.1', '10.0.0.2')
                if ok:
                    print("[+] DROP rule installed on switch s1")
                else:
                    print(f"[!] Failed to install DROP rule: {msg}")
                time.sleep(1)
                test_connectivity(net, drop_enabled=True)
            elif choice == '3':
                print("\n[*] Disabling DROP rule...")
                ok, msg = disable_drop_rule_on_switch('10.0.0.1', '10.0.0.2')
                if ok:
                    print("[+] DROP rule removed")
                else:
                    print(f"[!] Failed to remove DROP rule: {msg}")
            elif choice == '4':
                show_flow_tables(net)
            elif choice == '5':
                show_host_info(net)
            elif choice == '6':
                print("\n[*] Entering Mininet CLI. Type 'exit' to quit.")
                CLI(net)
                break
            else:
                print("[!] Invalid choice. Please try again.")
                
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        net.stop()
        print("[+] Network stopped successfully!")


if __name__ == '__main__':
    main()
