# Packet Drop Simulator - SDN Flow Rules Implementation

## Project Overview

This project implements a **Packet Drop Simulator** using Software-Defined Networking (SDN) principles. It demonstrates how to selectively drop packets using OpenFlow flow rules in a Mininet network simulation environment.

## Problem Statement

Create an SDN-based solution that allows selective packet dropping based on flow rules. The system must:

1. **Install Drop Rules**: Programmatically install OpenFlow rules that drop packets
2. **Select Specific Flows**: Choose which traffic to drop (e.g., source IP, destination IP, protocol)
3. **Measure Packet Loss**: Quantify the impact of drop rules using ping and throughput tests
4. **Evaluate Behavior**: Demonstrate normal vs. dropped traffic scenarios
5. **Regression Test**: Verify that drop rules persist correctly over time

---
## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Mininet Network Topology                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌───┐    ┌───┐    ┌───┐    ┌───┐               │
│   │h1 │    │h2 │    │h3 │    │h4 │               │
│   │   │    │   │    │   │    │   │               │
│   └─┬─┘    └─┬─┘    └─┬─┘    └─┬─┘               │
│     │        │        │        │                 │
│     └────────┴────────┴────────┘                 │
│              │                                    │
│           ┌──┴──┐                                │
│           │ s1  │ (OpenFlow Switch)             │
│           └──┬──┘                                │
│              │                                    │
│     ┌────────┴────────┐                          │
│     │ Controller      │                          │
│     │ (Ryu/POX)       │                          │
│     │ Port: 6633      │                          │
│     └─────────────────┘                          │
│                                                     │
└─────────────────────────────────────────────────────┘

Drop Rule Example:
Priority: 100
Match: ip_src=10.0.0.1, ip_dst=10.0.0.2, protocol=ICMP
Actions: (empty) → DROP
```

---

## File Structure

```
SDN_Mininet/
├── packet_drop_simulator.py          # Main Mininet topology and CLI
├── ryu_packet_drop_controller.py     # Ryu OpenFlow controller logic
├── test_packet_drop.py               # Comprehensive test suite
├── README.md                         # This file
└── setup_environment.sh              # Setup script (optional)
```

## Running the Project

### Quick Start (4 Terminal Windows)

#### Terminal 1: Clean Mininet
```bash
# Clear any previous Mininet instances
sudo mn -c
```

#### Terminal 2: Start Ryu Controller
```bash
cd ~/Desktop/SDN_Mininet
ryu-manager ryu_packet_drop_controller.py --observe-links
```

Expected output:
```
loading app ryu.topology.switches ...
loading app ryu.topology.lldp ...
loading app packet_drop_controller ...
[*] Packet Drop Controller initialized
```

#### Terminal 3: Start Mininet Simulator
```bash
# Using WSL/Ubuntu
sudo python3 packet_drop_simulator.py

# Or without WSL
python3 packet_drop_simulator.py
```

Expected output:
```
[*] Creating network topology...
[+] Topology created successfully!
[+] Hosts: h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)
[+] Switch: s1 (dpid=0000000000000001)
[*] Starting network...
[+] Network started!
```

#### Terminal 4: Run Test Suite
```bash
python3 test_packet_drop.py
```

---

## Test Scenarios

### Test Scenario 1: Normal Connectivity (No Drops)

**Objective:** Verify normal network behavior without drop rules

**Steps:**
```bash
# In Terminal 3 (Mininet CLI), select option 1 or run:
mininet> h1 ping -c 5 10.0.0.2
mininet> h3 ping -c 5 10.0.0.4
```

**Expected Output:**
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.23 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=1.45 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=1.32 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=1.56 ms

--- 10.0.0.2 statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

**Interpretation:**
- ✅ All packets successfully transmitted and received
- ✅ Latency is stable (1-2 ms range)
- ✅ 0% packet loss confirms normal forwarding


**Steps:**
```bash
# In Terminal 3 (Mininet CLI), run:
mininet> h1 ping -c 5 10.0.0.2
```

**Expected Output:**
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.

--- 10.0.0.2 statistics ---
5 packets transmitted, 0 received, 100% packet loss
```

**Verification:**
```bash
# In Terminal 1, verify flow rules:
sudo ovs-ofctl dump-flows s1
```

Expected flow table:
```
OFPST_FLOW reply (xid=0x2):
 cookie=0x0, duration=45.123s, table=0, n_packets=10, n_bytes=840,
 priority=100,ip,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=drop
```

**Interpretation:**
- ✅ All packets dropped (100% loss)
- ✅ Drop rule installed at priority 100
- ✅ No ICMP replies received (as expected)

---

### Regression Test: Drop Rule Persistence

**Objective:** Verify drop rules remain active and don't disappear

**Steps:**

```bash
# Step 1: Enable drop rule
mininet> h1 ping -c 10 10.0.0.2

# Step 2: Check flows (Terminal 1)
sudo ovs-ofctl dump-flows s1

# Step 3: Wait 30 seconds and send more packets
mininet> h1 ping -c 5 10.0.0.2

# Step 4: Verify drop rule still present (Terminal 1)
sudo ovs-ofctl dump-flows s1

# Step 5: Check idle/hard timeouts (should still show the rule)
# Note: If using hard_timeout=60, rule will expire after 60 seconds
```

## Packet Loss Measurement

### Using Ping

```bash
# Simple loss percentage
mininet> h1 ping -c 100 10.0.0.2 | grep "% packet loss"

# Detailed statistics
mininet> h1 ping -c 100 10.0.0.2
```

### Using iperf (Throughput)

```bash
# Terminal 1: Start iperf server on h2
mininet> h2 iperf -s

## OpenFlow Flow Rules Explained

### Flow Rule Components

```
Priority: 100
├─ Match:
│  ├─ eth_type: 0x0800 (IPv4)
│  ├─ ipv4_src: 10.0.0.1
│  └─ ipv4_dst: 10.0.0.2
└─ Actions: (empty/DROP)
```

### Rule Priority

- **Priority 100**: Drop rules (evaluated first)
- **Priority 1**: Learning switch forwarding rules
- **Priority 0**: Table-miss rule (sends to controller)

Higher priority = evaluated first

### Example Flow Rules

**Rule 1: Drop h1→h2 traffic**
```
priority=100,ip,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=drop
```

**Rule 2: Forward to h2**
```
priority=1,dl_dst=00:00:00:00:00:02 actions=output:2
```

**Rule 3: Table-miss (to controller)**
```
priority=0 actions=CONTROLLER:65535
```

---

## Viewing Flow Tables

### Display All Flows
```bash
sudo ovs-ofctl dump-flows s1
```

### Display Flows with Details
```bash
sudo ovs-ofctl dump-flows s1 -O OpenFlow13
```

### Clear All Flows
```bash
sudo ovs-ofctl del-flows s1
```

### Delete Specific Flow
```bash
sudo ovs-ofctl del-flows s1 "priority=100"
```

---

## Monitoring and Debugging

### View Controller Logs

```bash
# Terminal 2 (where controller runs)
# Logs show:
# [*] Packet Drop Controller initialized
# [+] Switch connected: dpid=0x0000000000000001
# [DROP] Dropping traffic: 10.0.0.1 -> 10.0.0.2
```

### View Switch Statistics

```bash
# Monitor flow statistics
watch -n 1 'sudo ovs-ofctl dump-flows s1'

# Port statistics
sudo ovs-ofctl dump-ports s1

# Flow statistics with more detail
sudo ovs-ofctl dump-flows s1 | grep -E "priority|n_packets|n_bytes"
```
### Controller Flow Handling
