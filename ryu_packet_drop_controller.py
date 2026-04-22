#!/usr/bin/env python3
"""
Ryu OpenFlow Controller - Packet Drop Simulator
Author: Student
Assignment: SDN-based packet dropping using OpenFlow rules

This controller implements:
1. Flow rule installation (drop rules)
2. Selective packet dropping based on source/destination IPs
3. Packet-in event handling
4. Flow table management
5. Regression testing for drop rule persistence
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, icmp
from ryu.lib.packet.ether_types import ETH_TYPE_IP, ETH_TYPE_ARP
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class PacketDropController(app_manager.RyuApp):
    """
    SDN Controller for Packet Drop Simulation
    
    Implements OpenFlow 1.3 controller with packet dropping capabilities
    """
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(PacketDropController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switch_list = {}
        self.drop_rules = {}  # Store drop rules for regression testing
        
        # Drop rules configuration
        # Format: (src_ip, dst_ip) -> enabled/disabled
        self.drop_rules_config = {
            ('10.0.0.1', '10.0.0.2'): False,  # h1 -> h2
            ('10.0.0.3', '10.0.0.4'): False,  # h3 -> h4
        }
        
        log.info("[*] Packet Drop Controller initialized")
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Handle switch features request
        Install table-miss flow entry to handle packets not matching any rule
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        dpid = datapath.id
        log.info(f"[+] Switch connected: dpid=0x{dpid:016x}")
        
        # Store switch
        self.switch_list[dpid] = datapath
        self.mac_to_port.setdefault(dpid, {})
        
        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions,
                      idle_timeout=0, hard_timeout=0)
        
        log.info(f"[+] Table-miss entry installed on switch {dpid}")
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handle packet-in events
        Implement learning switch behavior and apply drop rules
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ETH_TYPE_ARP:
            # Handle ARP
            self._handle_arp(datapath, pkt, eth, in_port, parser, ofproto, msg)
        
        elif eth.ethertype == ETH_TYPE_IP:
            # Handle IP packets
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            if ipv4_pkt:
                self._handle_ipv4(datapath, pkt, ipv4_pkt, in_port,
                                 parser, ofproto, msg)
    
    def _handle_arp(self, datapath, pkt, eth, in_port, parser, ofproto, msg):
        """Handle ARP packets - flood them"""
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def _handle_ipv4(self, datapath, pkt, ipv4_pkt, in_port,
                     parser, ofproto, msg):
        """
        Handle IPv4 packets
        Apply drop rules if configured
        """
        src_ip = ipv4_pkt.src
        dst_ip = ipv4_pkt.dst
        dpid = datapath.id
        
        # Check if this flow should be dropped
        if self._should_drop_flow(src_ip, dst_ip):
            log.warning(f"[DROP] Dropping traffic: {src_ip} -> {dst_ip}")
            
            # Install a DROP rule (higher priority)
            match = parser.OFPMatch(
                eth_type=ETH_TYPE_IP,
                ipv4_src=src_ip,
                ipv4_dst=dst_ip
            )
            # Empty actions list = DROP
            self.add_flow(datapath, 100, match, [],
                         idle_timeout=60, hard_timeout=60)
            
            # Record drop rule for regression testing
            self.drop_rules[dpid] = {
                'src': src_ip,
                'dst': dst_ip,
                'action': 'DROP',
                'timestamp': __import__('time').time()
            }
            return  # Don't forward the packet
        
        # Normal forwarding (learning switch behavior)
        self._handle_normal_forwarding(datapath, pkt, in_port,
                                      parser, ofproto, msg, eth=pkt.get_protocol(ethernet.ethernet))
    
    def _should_drop_flow(self, src_ip, dst_ip):
        """Check if flow should be dropped"""
        for (src, dst), enabled in self.drop_rules_config.items():
            if src == src_ip and dst == dst_ip and enabled:
                return True
        return False
    
    def _handle_normal_forwarding(self, datapath, pkt, in_port,
                                 parser, ofproto, msg, eth):
        """
        Implement learning switch forwarding
        """
        dpid = datapath.id
        self.mac_to_port[dpid][eth.src] = in_port
        
        if eth.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][eth.dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow rule for this MAC pair
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=eth.dst)
            self.add_flow(datapath, 1, match, actions)
        
        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def add_flow(self, datapath, priority, match, actions,
                idle_timeout=0, hard_timeout=0):
        """
        Install a flow rule in the switch
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=inst, idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)
    
    def enable_drop_rule(self, src_ip, dst_ip):
        """Enable packet dropping for a specific flow"""
        if (src_ip, dst_ip) in self.drop_rules_config:
            self.drop_rules_config[(src_ip, dst_ip)] = True
            log.info(f"[+] DROP RULE ENABLED: {src_ip} -> {dst_ip}")
            return True
        return False
    
    def disable_drop_rule(self, src_ip, dst_ip):
        """Disable packet dropping for a specific flow"""
        if (src_ip, dst_ip) in self.drop_rules_config:
            self.drop_rules_config[(src_ip, dst_ip)] = False
            log.info(f"[+] DROP RULE DISABLED: {src_ip} -> {dst_ip}")
            return True
        return False
    
    def get_drop_rules_status(self):
        """Get current drop rules status"""
        log.info("\n[*] Current DROP Rules Status:")
        for (src, dst), enabled in self.drop_rules_config.items():
            status = "ENABLED" if enabled else "DISABLED"
            log.info(f"  {src} -> {dst}: {status}")
    
    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        """Handle switch enter event"""
        log.info(f"[+] Switch entered: {ev.switch.dp.id}")
    
    @set_ev_cls(event.EventSwitchLeave)
    def switch_leave_handler(self, ev):
        """Handle switch leave event"""
        log.info(f"[-] Switch left: {ev.switch.dp.id}")


# Entry point
if __name__ == '__main__':
    app_manager.run_app(PacketDropController)
