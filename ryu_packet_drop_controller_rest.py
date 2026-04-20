#!/usr/bin/env python3
"""
Advanced Ryu Controller with REST API Support
Author: Student
Assignment: Packet Drop Simulator with REST API Control

This controller adds:
1. REST API endpoints for controlling drop rules
2. Real-time statistics and monitoring
3. Flow rule persistence management
4. JSON configuration support
"""

from ryu.base import app_manager
from ryu.controller import ofp_event, rest
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, icmp
from ryu.lib.packet.ether_types import ETH_TYPE_IP, ETH_TYPE_ARP
from ryu.topology import event
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
import logging
import json
from webob import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Global reference to controller app
_PACKET_DROP_CONTROLLER = None


class PacketDropControllerREST(ControllerBase):
    """REST API for controlling packet drop simulator"""
    
    def __init__(self, req, link, data, **config):
        super(PacketDropControllerREST, self).__init__(req, link, data, **config)
        self.packet_drop_app = data['packet_drop_app']
    
    @route('dropcontrol/flows', methods=['GET'])
    def get_flows(self, req, **kwargs):
        """Get current drop rules status"""
        body = json.dumps(self.packet_drop_app.get_drop_rules_status_json(),
                         indent=2)
        return Response(content_type='application/json', body=body)
    
    @route('dropcontrol/flows/enable', methods=['POST'])
    def enable_drop_rule(self, req, **kwargs):
        """Enable drop rule"""
        try:
            data = json.loads(req.body.decode('utf-8'))
            src_ip = data.get('src_ip')
            dst_ip = data.get('dst_ip')
            
            result = self.packet_drop_app.enable_drop_rule(src_ip, dst_ip)
            
            response_data = {
                'success': result,
                'message': f'Drop rule enabled: {src_ip} -> {dst_ip}' if result
                          else f'Drop rule not found: {src_ip} -> {dst_ip}',
                'src_ip': src_ip,
                'dst_ip': dst_ip
            }
            body = json.dumps(response_data, indent=2)
            return Response(content_type='application/json', body=body)
        except Exception as e:
            response_data = {'success': False, 'error': str(e)}
            body = json.dumps(response_data, indent=2)
            return Response(content_type='application/json', body=body, status=400)
    
    @route('dropcontrol/flows/disable', methods=['POST'])
    def disable_drop_rule(self, req, **kwargs):
        """Disable drop rule"""
        try:
            data = json.loads(req.body.decode('utf-8'))
            src_ip = data.get('src_ip')
            dst_ip = data.get('dst_ip')
            
            result = self.packet_drop_app.disable_drop_rule(src_ip, dst_ip)
            
            response_data = {
                'success': result,
                'message': f'Drop rule disabled: {src_ip} -> {dst_ip}' if result
                          else f'Drop rule not found: {src_ip} -> {dst_ip}',
                'src_ip': src_ip,
                'dst_ip': dst_ip
            }
            body = json.dumps(response_data, indent=2)
            return Response(content_type='application/json', body=body)
        except Exception as e:
            response_data = {'success': False, 'error': str(e)}
            body = json.dumps(response_data, indent=2)
            return Response(content_type='application/json', body=body, status=400)
    
    @route('dropcontrol/stats', methods=['GET'])
    def get_statistics(self, req, **kwargs):
        """Get flow statistics"""
        stats = self.packet_drop_app.get_statistics_json()
        body = json.dumps(stats, indent=2)
        return Response(content_type='application/json', body=body)


class PacketDropControllerAdvanced(app_manager.RyuApp):
    """Advanced Packet Drop Controller with REST API"""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}
    
    def __init__(self, *args, **kwargs):
        super(PacketDropControllerAdvanced, self).__init__(*args, **kwargs)
        
        self.mac_to_port = {}
        self.switch_list = {}
        self.drop_rules = {}
        self.flow_stats = {}
        
        # Drop rules configuration
        self.drop_rules_config = {
            ('10.0.0.1', '10.0.0.2'): False,
            ('10.0.0.3', '10.0.0.4'): False,
        }
        
        # Setup REST API
        wsgi = kwargs['wsgi']
        wsgi.register_instance(PacketDropControllerREST)
        mapper = wsgi.mapper
        mapper.connect('dropcontrol', '/dropcontrol/{action}',
                      controller=PacketDropControllerREST, action='get_flows')
        
        global _PACKET_DROP_CONTROLLER
        _PACKET_DROP_CONTROLLER = self
        
        log.info("[+] Advanced Packet Drop Controller initialized with REST API")
        log.info("[+] REST API available at http://localhost:8080/dropcontrol/flows")
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection"""
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        log.info(f"[+] Switch connected: dpid=0x{dpid:016x}")
        
        self.switch_list[dpid] = datapath
        self.mac_to_port.setdefault(dpid, {})
        self.flow_stats.setdefault(dpid, {})
        
        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions,
                     idle_timeout=0, hard_timeout=0)
        
        log.info(f"[+] Table-miss entry installed")
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle packet-in events"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        if eth.ethertype == ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            if ipv4_pkt:
                src_ip = ipv4_pkt.src
                dst_ip = ipv4_pkt.dst
                
                # Check drop rules
                if self._should_drop_flow(src_ip, dst_ip):
                    log.warning(f"[DROP] Dropping: {src_ip} -> {dst_ip}")
                    
                    # Install DROP rule
                    match = parser.OFPMatch(
                        eth_type=ETH_TYPE_IP,
                        ipv4_src=src_ip,
                        ipv4_dst=dst_ip
                    )
                    self.add_flow(datapath, 100, match, [],
                                 idle_timeout=60, hard_timeout=60)
                    
                    # Record statistics
                    if 'dropped_flows' not in self.flow_stats[dpid]:
                        self.flow_stats[dpid]['dropped_flows'] = {}
                    
                    key = f"{src_ip}->{dst_ip}"
                    if key not in self.flow_stats[dpid]['dropped_flows']:
                        self.flow_stats[dpid]['dropped_flows'][key] = 0
                    self.flow_stats[dpid]['dropped_flows'][key] += 1
                    
                    return  # Don't forward
        
        # Normal learning switch forwarding
        self._handle_normal_forwarding(datapath, pkt, eth, in_port,
                                      parser, ofproto, msg)
    
    def _should_drop_flow(self, src_ip, dst_ip):
        """Check if flow should be dropped"""
        for (src, dst), enabled in self.drop_rules_config.items():
            if src == src_ip and dst == dst_ip and enabled:
                return True
        return False
    
    def _handle_normal_forwarding(self, datapath, pkt, eth, in_port,
                                 parser, ofproto, msg):
        """Handle normal packet forwarding"""
        dpid = datapath.id
        self.mac_to_port[dpid][eth.src] = in_port
        
        if eth.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][eth.dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=eth.dst)
            self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def add_flow(self, datapath, priority, match, actions,
                idle_timeout=0, hard_timeout=0):
        """Install flow rule"""
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
        """Enable drop rule via API"""
        if (src_ip, dst_ip) in self.drop_rules_config:
            self.drop_rules_config[(src_ip, dst_ip)] = True
            log.info(f"[+] DROP RULE ENABLED: {src_ip} -> {dst_ip}")
            return True
        return False
    
    def disable_drop_rule(self, src_ip, dst_ip):
        """Disable drop rule via API"""
        if (src_ip, dst_ip) in self.drop_rules_config:
            self.drop_rules_config[(src_ip, dst_ip)] = False
            log.info(f"[+] DROP RULE DISABLED: {src_ip} -> {dst_ip}")
            
            # Clear any existing drop flows from switch
            for dpid, datapath in self.switch_list.items():
                parser = datapath.ofproto_parser
                match = parser.OFPMatch(ipv4_src=src_ip, ipv4_dst=dst_ip)
                ofproto = datapath.ofproto
                mod = parser.OFPFlowMod(
                    datapath=datapath, priority=100, match=match,
                    command=ofproto.OFPFC_DELETE
                )
                datapath.send_msg(mod)
            
            return True
        return False
    
    def get_drop_rules_status_json(self):
        """Get drop rules status as JSON"""
        status = {
            'drop_rules': [],
            'total_rules': len(self.drop_rules_config),
            'enabled_count': sum(1 for v in self.drop_rules_config.values() if v)
        }
        
        for (src, dst), enabled in self.drop_rules_config.items():
            status['drop_rules'].append({
                'src_ip': src,
                'dst_ip': dst,
                'enabled': enabled,
                'status': 'ACTIVE' if enabled else 'INACTIVE'
            })
        
        return status
    
    def get_statistics_json(self):
        """Get statistics as JSON"""
        stats = {
            'switches': len(self.switch_list),
            'flow_stats': {}
        }
        
        for dpid, flow_data in self.flow_stats.items():
            stats['flow_stats'][f"0x{dpid:016x}"] = flow_data
        
        return stats


# Entry point
if __name__ == '__main__':
    app_manager.run_app(PacketDropControllerAdvanced)
