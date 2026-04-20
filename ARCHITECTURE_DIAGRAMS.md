# Packet Drop Simulator - System Architecture & Flow Diagrams

## System Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                    HOST MACHINE / LINUX VM                          ║
║                   (Ubuntu 20.04 / 22.04 / WSL2)                     ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ┌────────────────────────────────────────────────────────────┐    ║
║  │                  MININET VIRTUAL NETWORK                   │    ║
║  │                                                            │    ║
║  │  ┌──────────────────────────────────────────────────────┐ │    ║
║  │  │          OpenFlow Virtual Switch (s1)               │ │    ║
║  │  │         DPID: 0000000000000001                      │ │    ║
║  │  │         Protocol: OpenFlow 1.3                      │ │    ║
║  │  │         Backend: Open vSwitch (ovs-vswitchd)       │ │    ║
║  │  │                                                      │ │    ║
║  │  │  ┌─────────────────────────────────────────────┐   │ │    ║
║  │  │  │       Flow Tables (Pipelined Processing)    │   │ │    ║
║  │  │  │  ┌─────────────────────────────────────┐    │   │ │    ║
║  │  │  │  │ Priority 100: DROP Rules            │    │   │ │    ║
║  │  │  │  │   Match: ipv4_src, ipv4_dst         │    │   │ │    ║
║  │  │  │  │   Action: DROP                      │    │   │ │    ║
║  │  │  │  └─────────────────────────────────────┘    │   │ │    ║
║  │  │  │  ┌─────────────────────────────────────┐    │   │ │    ║
║  │  │  │  │ Priority 1: Learning Rules          │    │   │ │    ║
║  │  │  │  │   Match: dl_dst (MAC address)       │    │   │ │    ║
║  │  │  │  │   Action: OUTPUT:<PORT>             │    │   │ │    ║
║  │  │  │  └─────────────────────────────────────┘    │   │ │    ║
║  │  │  │  ┌─────────────────────────────────────┐    │   │ │    ║
║  │  │  │  │ Priority 0: Table-Miss              │    │   │ │    ║
║  │  │  │  │   Match: ALL packets                │    │   │ │    ║
║  │  │  │  │   Action: CONTROLLER (packet_in)    │    │   │ │    ║
║  │  │  │  └─────────────────────────────────────┘    │   │ │    ║
║  │  │  └─────────────────────────────────────────────┘    │ │    ║
║  │  │                                                      │ │    ║
║  │  └──────────────────────────────────────────────────────┘ │    ║
║  │       ↑                  ↑                  ↑             │    ║
║  │    veth0               veth1              veth2           │    ║
║  │       │                  │                  │             │    ║
║  │  ┌────┴────┐        ┌────┴────┐        ┌────┴────┐       │    ║
║  │  │   h1    │        │   h2    │        │   h3    │ ...   │    ║
║  │  │10.0.0.1 │        │10.0.0.2 │        │10.0.0.3 │       │    ║
║  │  └─────────┘        └─────────┘        └─────────┘       │    ║
║  │  (Host 1)           (Host 2)           (Host 3)          │    ║
║  │                                                            │    ║
║  └────────────────────────────────────────────────────────────┘    ║
║                          ↑                                          ║
║                     OpenFlow Port 6633                             ║
║                          │                                          ║
║  ┌──────────────────────┴──────────────────────────────────────┐  ║
║  │              RYU OpenFlow Controller                         │  ║
║  │            (Localhost:6633 TCP Connection)                  │  ║
║  │                                                              │  ║
║  │  ┌────────────────────────────────────────────────────────┐│  ║
║  │  │      PacketDropController App                          ││  ║
║  │  │                                                        ││  ║
║  │  │  • switch_features_handler()     [Table-miss setup]  ││  ║
║  │  │  • packet_in_handler()           [Packet processing] ││  ║
║  │  │  • _should_drop_flow()           [Drop logic]        ││  ║
║  │  │  • add_flow()                    [Rule installation] ││  ║
║  │  │  • enable/disable_drop_rule()    [API methods]       ││  ║
║  │  │                                                        ││  ║
║  │  └────────────────────────────────────────────────────────┘│  ║
║  │                                                              │  ║
║  │  ┌────────────────────────────────────────────────────────┐│  ║
║  │  │     REST API Layer (Optional - Port 8080)             ││  ║
║  │  │  • GET  /dropcontrol/flows      [Get status]         ││  ║
║  │  │  • POST /dropcontrol/flows/enable     [Enable rule]  ││  ║
║  │  │  • POST /dropcontrol/flows/disable    [Disable rule] ││  ║
║  │  │  • GET  /dropcontrol/stats            [Get stats]    ││  ║
║  │  └────────────────────────────────────────────────────────┘│  ║
║  │                                                              │  ║
║  └──────────────────────────────────────────────────────────────┘  ║
║                          ↑ (HTTP/REST)                            ║
║                          │ (Port 8080)                             ║
║  ┌──────────────────────┴──────────────────────────────────────┐  ║
║  │   REST API Client (Optional)                               │  ║
║  │   CLI Tool for Control & Monitoring                        │  ║
║  │   rest_api_client.py                                       │  ║
║  └──────────────────────────────────────────────────────────────┘  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Packet Flow Diagram - Normal Operation (No Drop)

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCENARIO: h1 → h2 with NO drop rule enabled                        │
└─────────────────────────────────────────────────────────────────────┘

TIME    EVENT                                    LOCATION
════════════════════════════════════════════════════════════════════════

T0      h1 sends ICMP Echo Request               [h1:10.0.0.1]
        to 10.0.0.2                              
        └─→ Ethernet dest: 00:00:00:00:00:02
            Destination: 10.0.0.2
                                                 
T1      Packet enters switch port 1              [s1 - ingress port 1]
        
T2      Switch flow table lookup:                [s1 - Table pipeline]
        Priority 100 (DROP rules)?  → NO MATCH
        Priority 1 (Learning)?      → NO MATCH (first packet)
        Priority 0 (Table-miss)?    → MATCH ✓
        
T3      Execute Priority 0 action:               [s1 internal]
        "Send to CONTROLLER"
        └─→ packet_in event generated
        
T4      Send packet_in to Ryu                    [TCP 127.0.0.1:6633]
        message includes:
        - Full packet contents
        - Ingress port (1)
        - Switch DPID
        
T5      Controller receives packet_in             [Ryu controller]
        
T6      Controller processing:                    [Ryu processing]
        ├─ Parse packet
        ├─ Extract source MAC: 00:00:00:00:00:01
        ├─ Learn: MAC[01] on port 1
        ├─ Check drop rules:
        │  └─ Is src=10.0.0.1 AND dst=10.0.0.2?
        │     (Check drop_rules_config)
        │     → NO, not configured to drop
        ├─ Look up dest MAC: 00:00:00:00:00:02
        │  └─ Not in MAC table, FLOOD
        └─ Create flow_mod message
        
T7      Controller installs learning rule:        [Switch port 1→2]
        Priority: 1
        Match: eth_dst = 00:00:00:00:00:02
        Action: OUTPUT port 2
        
T8      Controller sends packet out:              [s1 egress port 2]
        Action: OUTPUT port 2
        └─→ Packet sent to h2
        
T9      h2 receives ICMP Echo Request             [h2:10.0.0.2]
        └─→ Responds with ICMP Echo Reply
        
T10     Reply packet enters switch port 2         [s1 - ingress port 2]
        
T11     Switch lookup (Priority 1):              [s1 - Table pipeline]
        Match: eth_dst = 00:00:00:00:00:01
        Found! (installed at T7)
        Action: OUTPUT port 1
        
T12     Reply packet exits port 1               [s1 egress port 1]
        └─→ Packet sent to h1
        
T13     h1 receives ICMP Echo Reply              [h1:10.0.0.1]
        
RESULT: ✅ Ping succeeds, 0% packet loss
        Latency: ~1-2ms
        
FLOW RULES ON SWITCH:
Priority 1, eth_dst=00:00:00:00:00:02 → OUTPUT:2
Priority 1, eth_dst=00:00:00:00:00:01 → OUTPUT:1
Priority 0, all packets → CONTROLLER
```

---

## Packet Flow Diagram - With Drop Rule Enabled

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCENARIO: h1 → h2 WITH drop rule enabled for (10.0.0.1→10.0.0.2) │
└─────────────────────────────────────────────────────────────────────┘

SETUP:
  controller.drop_rules_config = {
      ('10.0.0.1', '10.0.0.2'): True  ← ENABLED
  }

TIME    EVENT                                    LOCATION
════════════════════════════════════════════════════════════════════════

T0      h1 sends ICMP Echo Request               [h1:10.0.0.1]
        to 10.0.0.2
        └─→ Ethernet dest: 00:00:00:00:00:02
            IPv4 src: 10.0.0.1
            IPv4 dst: 10.0.0.2
                                                 
T1      Packet enters switch port 1              [s1 - ingress port 1]
        
T2      Switch flow table lookup:                [s1 - Table pipeline]
        Priority 100 (DROP rules)?  
        ├─ Check Match: ipv4_src=10.0.0.1, ipv4_dst=10.0.0.2
        ├─ Check eth_type=0x0800 (IPv4)
        └─→ MATCH FOUND! ✓✓✓
        
T3      Execute Priority 100 action:             [s1 internal]
        Actions: (empty/DROP)
        └─→ DROP the packet immediately
        
T4      Packet discarded                         [s1 - dropped]
        No forwarding, no packet_in sent
        
RESULT: ✅ Packet dropped, 100% packet loss
        No reply sent to h1
        h1 ping times out after 3 seconds
        
FLOW RULES ON SWITCH:
Priority 100, ip,nw_src=10.0.0.1,nw_dst=10.0.0.2 → DROP
Priority 0, all packets → CONTROLLER

TIMING:
  Drop latency: <0.1ms (handled in data plane, no controller involvement)
  Subsequent packets: Also dropped immediately (no packet_in needed)
```

---

## Drop Rule Installation Flow

```
┌────────────────────────────────────────────────────────────────────┐
│ HOW DROP RULES ARE INSTALLED                                       │
└────────────────────────────────────────────────────────────────────┘

METHOD 1: Automatic on First Packet (When Drop Enabled)

  packet_in received (h1 → h2 traffic)
           ↓
  Check if drop_rules_config[('10.0.0.1', '10.0.0.2')] == True
           ↓ YES
  Create OFPMatch:
    eth_type=0x0800
    ipv4_src=10.0.0.1
    ipv4_dst=10.0.0.2
           ↓
  Create flow_mod with:
    datapath = s1
    priority = 100 (high priority)
    match = above
    instructions = [] (empty = DROP)
    idle_timeout = 60
    hard_timeout = 60
           ↓
  Send flow_mod message to switch
           ↓
  Switch installs rule
           ↓
  ✅ Subsequent packets processed by switch (data plane)
     No more controller involvement

METHOD 2: REST API Enable

  curl -X POST http://localhost:8080/dropcontrol/flows/enable \
    -H "Content-Type: application/json" \
    -d '{"src_ip": "10.0.0.1", "dst_ip": "10.0.0.2"}'
           ↓
  REST API receives request
           ↓
  Set drop_rules_config[('10.0.0.1', '10.0.0.2')] = True
           ↓
  Return JSON response: {"success": true, ...}
           ↓
  ⏳ Waiting for next packet from h1 → h2
           ↓
  When next packet arrives → install rule (same as METHOD 1)

RULE TIMEOUT BEHAVIOR:
  ┌─────────────────────────────────────────────────────────┐
  │ Drop Rule Active Timeline                               │
  ├─────────────────────────────────────────────────────────┤
  │ T=0s    Rule installed (idle_timeout=60, hard_timeout=60)
  │ T=1-60s Rule active, all matching packets dropped
  │ T=60s   hard_timeout expires → Rule removed
  │ T=61s+  Packets go to controller again (packet_in)
  │         If drop rule still enabled in config:
  │         → New rule installed
  │         If drop rule disabled in config:
  │         → Normal forwarding
  └─────────────────────────────────────────────────────────┘

REGRESSION TEST (Persistence):
  
  Enable drop rule → ping -c 100 10.0.0.2
           ↓
  100 packets, all dropped
           ↓
  Wait 30 seconds
           ↓
  ping -c 50 10.0.0.2
           ↓
  50 packets, all dropped (rule still active)
           ↓
  Wait 35 seconds (total 65 > hard_timeout)
           ↓
  ping -c 10 10.0.0.2
           ↓
  10 packets received (rule expired, new one installed if still enabled)
```

---

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ COMPONENT INTERACTION & MESSAGE FLOW                         │
└──────────────────────────────────────────────────────────────┘

User
  │
  ├─► packet_drop_simulator.py (Mininet)
  │       │
  │       ├─ Creates topology (h1, h2, s1)
  │       ├─ Starts network
  │       ├─ Provides interactive menu
  │       ├─ Shows flow tables
  │       └─ Enters Mininet CLI
  │
  ├─► rest_api_client.py (CLI Control)
  │       │
  │       └─ HTTP/REST Requests → Ryu Controller REST API
  │
  └─► mininet CLI (Direct Control)
          │
          ├─ h1 ping h2 → Network traffic
          ├─ pingall → Test all connectivity
          └─ net → Show topology

Mininet Network (Virtual)
  │
  ├─ Hosts: h1, h2, h3, h4
  │
  └─ Switch: s1 (ovs-vswitchd)
      │
      ├─ Ingress: Receives packets
      ├─ Table Processing: Check flow rules (priority ordered)
      ├─ Egress: Forward or drop
      └─ Controller Port: packet_in events to controller

RYU Controller
  │
  ├─ app_manager.RyuApp
  │   │
  │   ├─ ryu_packet_drop_controller.py
  │   │   │
  │   │   ├─ switch_features_handler()
  │   │   │   └─ Called when switch connects
  │   │   │      └─ Install table-miss rule
  │   │   │
  │   │   ├─ packet_in_handler()
  │   │   │   └─ Called when packet_in from switch
  │   │   │      ├─ Parse packet
  │   │   │      ├─ Check drop rules
  │   │   │      ├─ Install flow rule if drop
  │   │   │      └─ Forward if no drop
  │   │   │
  │   │   └─ add_flow()
  │   │       └─ Send OFPFlowMod to switch
  │   │
  │   └─ ryu_packet_drop_controller_rest.py (Advanced)
  │       │
  │       ├─ REST API endpoints
  │       │   ├─ GET /dropcontrol/flows
  │       │   ├─ POST /dropcontrol/flows/enable
  │       │   ├─ POST /dropcontrol/flows/disable
  │       │   └─ GET /dropcontrol/stats
  │       │
  │       └─ HTTP interface (Port 8080)
  │           └─ Listens for HTTP requests

OpenFlow Protocol (TCP Port 6633)
  │
  ├─► OF Messages: Switch → Controller
  │   ├─ OFPT_FEATURES_REPLY (hello)
  │   ├─ OFPT_PACKET_IN (packet_in)
  │   └─ OFPT_STATS_REPLY (statistics)
  │
  └─► OF Messages: Controller → Switch
      ├─ OFPT_FLOW_MOD (add/modify/delete rule)
      ├─ OFPT_STATS_REQUEST (query flows)
      └─ OFPT_PACKET_OUT (send packet out)
```

---

## Data Structure Relationships

```
┌────────────────────────────────────────────────────────┐
│ Controller Data Structures                             │
├────────────────────────────────────────────────────────┤

drop_rules_config:
  ┌─────────────────────────────────────────┐
  │ Dict[Tuple[str, str], bool]             │
  │ Key: (src_ip, dst_ip)                   │
  │ Value: enabled/disabled                 │
  ├─────────────────────────────────────────┤
  │ ('10.0.0.1', '10.0.0.2'): False        │ ← Not dropping
  │ ('10.0.0.3', '10.0.0.4'): True         │ ← Dropping
  └─────────────────────────────────────────┘

mac_to_port:
  ┌─────────────────────────────────────────┐
  │ Dict[int, Dict[str, int]]               │
  │ outer key: DPID (switch ID)             │
  │ inner: MAC address → port number        │
  ├─────────────────────────────────────────┤
  │ 1 (DPID 0x0001):                        │
  │   '00:00:00:00:00:01': 1 (h1→port 1)   │
  │   '00:00:00:00:00:02': 2 (h2→port 2)   │
  │   '00:00:00:00:00:03': 3 (h3→port 3)   │
  │   '00:00:00:00:00:04': 4 (h4→port 4)   │
  └─────────────────────────────────────────┘

drop_rules (statistics):
  ┌─────────────────────────────────────────┐
  │ Dict[int, Dict]                         │
  │ key: DPID                               │
  │ value: {                                │
  │   'src': source IP                      │
  │   'dst': destination IP                 │
  │   'action': 'DROP'                      │
  │   'timestamp': time.time()              │
  │ }                                       │
  └─────────────────────────────────────────┘

switch_list:
  ┌─────────────────────────────────────────┐
  │ Dict[int, Datapath]                     │
  │ key: DPID                               │
  │ value: Datapath object for sending msgs │
  └─────────────────────────────────────────┘
```

---

## Priority & Rule Processing

```
OpenFlow Table Processing (Priority-Based):

  ┌─ Incoming Packet
  │
  ├─► Priority 100+ Rules
  │   └─ Drop Rules (DROP traffic)
  │      Match: ip_src, ip_dst, eth_type
  │      Action: (empty) = DROP
  │      IF MATCH → Drop packet, no further processing
  │      IF NO MATCH → Continue
  │
  ├─► Priority 50-99 Rules
  │   └─ (Reserved for future use)
  │      IF MATCH → Execute action, no further processing
  │      IF NO MATCH → Continue
  │
  ├─► Priority 1 Rules
  │   └─ Learning Switch Rules
  │      Match: eth_dst (MAC address)
  │      Action: OUTPUT:<port>
  │      IF MATCH → Forward to port, no further processing
  │      IF NO MATCH → Continue
  │
  └─► Priority 0 Rule (Table-Miss)
      └─ Default Catch-All
         Match: ALL packets
         Action: CONTROLLER (send packet_in to controller)
         ALWAYS MATCHES → Send to controller

EXECUTION GUARANTEE:
  - Rules evaluated in order of priority (highest first)
  - First matching rule is executed
  - No further rules evaluated after match
  - This is hardware-assisted data plane processing
```

---

## Testing Workflow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ COMPLETE TESTING WORKFLOW                                    │
└──────────────────────────────────────────────────────────────┘

START
  │
  ├─ Setup Phase
  │   ├─ Terminal 1: sudo mn -c
  │   ├─ Terminal 2: ryu-manager ryu_packet_drop_controller.py
  │   ├─ Terminal 3: sudo python3 packet_drop_simulator.py
  │   └─ ✅ Wait for "Network started!"
  │
  ├─ Baseline Test (No Drop Rules)
  │   ├─ Select: Option 1 (Test Normal Connectivity)
  │   ├─ Or run: mininet> h1 ping -c 5 10.0.0.2
  │   ├─ Expected: 0% packet loss
  │   ├─ Verify: All pings reply with ~1-2ms latency
  │   └─ ✅ PASS: Document as Test Case 1
  │
  ├─ View Baseline Rules
  │   ├─ Select: Option 4 (Show Switch Flow Tables)
  │   ├─ Or run: sudo ovs-ofctl dump-flows s1
  │   └─ ✅ Verify: Priority 0 table-miss rule exists
  │
  ├─ Enable Drop Rule
  │   ├─ Method 1: Edit ryu controller, restart Ryu
  │   │   └─ Set drop_rules_config[('10.0.0.1', '10.0.0.2')] = True
  │   │
  │   ├─ Method 2: Use REST API
  │   │   └─ python3 rest_api_client.py --action enable --src 10.0.0.1 --dst 10.0.0.2
  │   │
  │   └─ ✅ Verify: controller logs show "DROP RULE ENABLED"
  │
  ├─ Drop Rule Test (Drop Rules Enabled)
  │   ├─ Select: Option 2 (Enable DROP Rule)
  │   ├─ Or run: mininet> h1 ping -c 5 10.0.0.2
  │   ├─ Expected: 100% packet loss
  │   ├─ Verify: No pings reply, "100% packet loss"
  │   └─ ✅ PASS: Document as Test Case 2
  │
  ├─ Verify Drop Rule in Table
  │   ├─ Select: Option 4 (Show Switch Flow Tables)
  │   ├─ Or run: sudo ovs-ofctl dump-flows s1
  │   └─ ✅ Verify: Priority 100 DROP rule visible
  │
  ├─ Regression Test (Rule Persistence)
  │   ├─ Run: mininet> h1 ping -c 10 10.0.0.2
  │   ├─ Observe: All packets dropped (10 timeouts)
  │   ├─ Wait: 30 seconds
  │   ├─ Run: mininet> h1 ping -c 5 10.0.0.2
  │   ├─ Observe: All packets still dropped
  │   ├─ Check flow table: Rule still present
  │   ├─ Wait: Until 60 seconds (hard_timeout)
  │   ├─ Run: mininet> h1 ping -c 5 10.0.0.2
  │   ├─ Observe: Packets now pass (rule expired)
  │   └─ ✅ PASS: Drop rule persists correctly
  │
  ├─ Disable Drop Rule
  │   ├─ Select: Option 3 (Disable DROP Rule)
  │   ├─ Or REST: python3 rest_api_client.py --action disable --src 10.0.0.1 --dst 10.0.0.2
  │   └─ ✅ Verify: controller logs show "DROP RULE DISABLED"
  │
  ├─ Verify Recovery
  │   ├─ Run: mininet> h1 ping -c 5 10.0.0.2
  │   ├─ Expected: 0% packet loss
  │   ├─ Verify: Pings working again
  │   └─ ✅ PASS: System recovered
  │
  └─ END - All Tests Passed ✅

DOCUMENTATION REQUIRED:
  ✓ Screenshots of normal ping (0% loss)
  ✓ Screenshots of drop rule ping (100% loss)
  ✓ Flow table dumps (with and without drop rule)
  ✓ Controller logs (showing DROP events)
  ✓ Regression test results
  ✓ README with setup instructions
  ✓ Source code in GitHub repo
```

---

## Performance Metrics

```
PERFORMANCE BASELINE (No Drop Rule)
┌──────────────────────┬─────────┬──────────┐
│ Metric               │ Min     │ Max      │
├──────────────────────┼─────────┼──────────┤
│ Latency (ping)       │ 0.8 ms  │ 5.2 ms   │
│ Throughput (iperf)   │ 900 Mbps│ 1000 Mbps│
│ Packet Loss          │ 0%      │ 0%       │
│ Controller Latency   │ 10 ms   │ 50 ms    │
│ Flow Table Size      │ 3 rules │ 10 rules │
└──────────────────────┴─────────┴──────────┘

WITH DROP RULE ENABLED
┌──────────────────────┬─────────┬──────────┐
│ Metric               │ Value   │ Status   │
├──────────────────────┼─────────┼──────────┤
│ Latency              │ N/A     │ No reply │
│ Throughput           │ 0 Mbps  │ No flow  │
│ Packet Loss          │ 100%    │ Dropped  │
│ Drop Latency         │ <0.1 ms │ Fast     │
│ Flow Table Size      │ 4 rules │ +1 rule  │
└──────────────────────┴─────────┴──────────┘

Controller Performance
┌──────────────────────┬──────────┐
│ Operation            │ Duration │
├──────────────────────┼──────────┤
│ packet_in processing │ 5-10 ms  │
│ Flow rule install    │ 2-5 ms   │
│ Rule matching        │ <0.1 ms  │
└──────────────────────┴──────────┘
```

---

**Diagrams Complete** - These visualizations help understand the complete architecture, data flow, and testing procedures of the Packet Drop Simulator.
