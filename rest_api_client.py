#!/usr/bin/env python3
"""
REST API Client for Packet Drop Simulator
Author: Student
Assignment: Control drop rules via REST API

Usage:
    python3 rest_api_client.py --action enable --src 10.0.0.1 --dst 10.0.0.2
    python3 rest_api_client.py --action disable --src 10.0.0.1 --dst 10.0.0.2
    python3 rest_api_client.py --action status
    python3 rest_api_client.py --action stats
"""

import requests
import json
import argparse
import sys
from tabulate import tabulate

BASE_URL = "http://localhost:8080/dropcontrol"

def get_controller_status():
    """Get current drop rules status"""
    try:
        response = requests.get(f"{BASE_URL}/flows", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to controller. Is it running?"
    except Exception as e:
        return False, str(e)

def enable_drop_rule(src_ip, dst_ip):
    """Enable drop rule"""
    try:
        payload = {
            'src_ip': src_ip,
            'dst_ip': dst_ip
        }
        response = requests.post(
            f"{BASE_URL}/flows/enable",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def disable_drop_rule(src_ip, dst_ip):
    """Disable drop rule"""
    try:
        payload = {
            'src_ip': src_ip,
            'dst_ip': dst_ip
        }
        response = requests.post(
            f"{BASE_URL}/flows/disable",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def get_statistics():
    """Get flow statistics"""
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def display_status(data):
    """Display drop rules status in table format"""
    if 'drop_rules' not in data:
        print("[!] Invalid response format")
        return
    
    print("\n" + "="*70)
    print("PACKET DROP SIMULATOR - Drop Rules Status")
    print("="*70)
    
    print(f"\nTotal Rules: {data['total_rules']}")
    print(f"Enabled Rules: {data['enabled_count']}")
    print(f"Disabled Rules: {data['total_rules'] - data['enabled_count']}")
    
    print("\n" + "-"*70)
    print("Drop Rules Configuration:")
    print("-"*70)
    
    table_data = []
    for rule in data['drop_rules']:
        table_data.append([
            rule['src_ip'],
            "→",
            rule['dst_ip'],
            rule['status']
        ])
    
    headers = ['Source IP', '', 'Dest IP', 'Status']
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()

def display_stats(data):
    """Display statistics"""
    print("\n" + "="*70)
    print("PACKET DROP SIMULATOR - Statistics")
    print("="*70)
    
    print(f"\nConnected Switches: {data['switches']}")
    
    if data['flow_stats']:
        print("\nFlow Statistics by Switch:")
        for switch, stats in data['flow_stats'].items():
            print(f"\n  Switch: {switch}")
            print(f"    Dropped Flows: {len(stats.get('dropped_flows', {}))}")
            for flow, count in stats.get('dropped_flows', {}).items():
                print(f"      {flow}: {count} packets")
    print()

def main():
    parser = argparse.ArgumentParser(
        description='Control Packet Drop Simulator via REST API'
    )
    parser.add_argument('--action', required=True,
                       choices=['enable', 'disable', 'status', 'stats'],
                       help='Action to perform')
    parser.add_argument('--src', help='Source IP address')
    parser.add_argument('--dst', help='Destination IP address')
    
    args = parser.parse_args()
    
    if args.action == 'status':
        print("[*] Retrieving drop rules status...")
        success, data = get_controller_status()
        
        if success:
            display_status(data)
        else:
            print(f"[!] Error: {data}")
            sys.exit(1)
    
    elif args.action == 'stats':
        print("[*] Retrieving statistics...")
        success, data = get_statistics()
        
        if success:
            display_stats(data)
        else:
            print(f"[!] Error: {data}")
            sys.exit(1)
    
    elif args.action == 'enable':
        if not args.src or not args.dst:
            print("[!] Error: --src and --dst required for enable action")
            sys.exit(1)
        
        print(f"[*] Enabling drop rule: {args.src} -> {args.dst}...")
        success, data = enable_drop_rule(args.src, args.dst)
        
        if success:
            print(f"[+] {data['message']}")
            print(f"    Source: {data['src_ip']}")
            print(f"    Destination: {data['dst_ip']}")
        else:
            print(f"[!] Error: {data}")
            sys.exit(1)
    
    elif args.action == 'disable':
        if not args.src or not args.dst:
            print("[!] Error: --src and --dst required for disable action")
            sys.exit(1)
        
        print(f"[*] Disabling drop rule: {args.src} -> {args.dst}...")
        success, data = disable_drop_rule(args.src, args.dst)
        
        if success:
            print(f"[+] {data['message']}")
            print(f"    Source: {data['src_ip']}")
            print(f"    Destination: {data['dst_ip']}")
        else:
            print(f"[!] Error: {data}")
            sys.exit(1)

if __name__ == '__main__':
    main()
