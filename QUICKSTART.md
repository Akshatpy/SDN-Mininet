# QUICKSTART - Packet Drop Simulator

## Quick Setup (5 minutes)

### 1. Prerequisites
```bash
# Check if you have these installed
python3 --version        # Python 3.7+
sudo which mininet       # Mininet
pip3 list | grep ryu     # Ryu
```

### 2. Install Missing Components (if needed)

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install mininet openvswitch-testcontroller -y
pip3 install ryu networkx

# Verify
mininet --version
ryu-manager --version
```

### 3. Download/Setup Project
```bash
cd ~/Desktop/SDN_Mininet
# (Files already present)
```

---

## Running the Simulation (Choose One Method)

### METHOD 1: Quick Test (Simplest - 10 minutes)

**Terminal 1 - Clean Mininet:**
```bash
sudo mn -c
```

**Terminal 2 - Start Controller:**
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

**Terminal 3 - Start Network:**
```bash
cd ~/Desktop/SDN_Mininet
sudo python3 packet_drop_simulator.py
```

You'll see:
```
[*] Creating network topology...
[+] Topology created successfully!
[+] Hosts: h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)
[*] Starting network...
[+] Network started!
```

**When prompted in Terminal 3:**
```
Press Enter once Ryu controller is running...
```
Hit ENTER.

**Use the Menu in Terminal 3:**
```
======================================
SDN PACKET DROP SIMULATOR - Control Menu
======================================
1. Test Normal Connectivity (no drops)
2. Enable DROP Rule (h1 -> h2)
3. Disable DROP Rule
4. Show Switch Flow Tables
5. Show Host Information
6. Exit & Enter Mininet CLI
```

---

### METHOD 2: Direct Mininet CLI Test

**Same Terminals 1-3 as above**, then at the menu choose option 6 or type:

```bash
mininet> h1 ping -c 5 10.0.0.2
```

Output (normal):
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=1.23 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=1.45 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=1.32 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time=1.56 ms
64 bytes from 10.0.0.2: icmp_seq=5 ttl=64 time=1.67 ms

--- 10.0.0.2 statistics ---
5 packets transmitted, 5 received, 0% packet loss
```

---

### METHOD 3: REST API Control (Advanced)

**Same Terminals 1-3 as above**, then:

**Terminal 4 - Control via REST API:**
```bash
# Check status
python3 rest_api_client.py --action status

# Enable drop rule
python3 rest_api_client.py --action enable --src 10.0.0.1 --dst 10.0.0.2

# Check status again
python3 rest_api_client.py --action status

# Disable drop rule
python3 rest_api_client.py --action disable --src 10.0.0.1 --dst 10.0.0.2
```

---

## Seeing the Drop Rule in Action

### Step 1: Check Normal Connectivity
```bash
mininet> h1 ping -c 5 10.0.0.2
# Output: 0% packet loss ✓
```

### Step 2: Enable Drop Rule
Edit `ryu_packet_drop_controller.py`:
```python
# Line ~35, change this:
self.drop_rules_config = {
    ('10.0.0.1', '10.0.0.2'): False,   # ← Change to True
    ('10.0.0.3', '10.0.0.4'): False,
}
```

Restart Terminal 2 (Ryu controller):
```bash
# Ctrl+C to stop
# Then restart:
ryu-manager ryu_packet_drop_controller.py --observe-links
```

### Step 3: Test with Drop Rule
```bash
mininet> h1 ping -c 5 10.0.0.2
# Output: 100% packet loss ✓
```

### Step 4: Verify Flow Rule
```bash
# Terminal 1:
sudo ovs-ofctl dump-flows s1
```

You should see:
```
OFPST_FLOW reply (xid=0x2):
 ...
 priority=100,ip,nw_src=10.0.0.1,nw_dst=10.0.0.2 actions=drop
 ...
```

---

## Common Commands Quick Reference

| Purpose | Command |
|---------|---------|
| List Mininet hosts | `mininet> net` |
| Ping host | `mininet> h1 ping -c 5 10.0.0.2` |
| Exit Mininet | `mininet> exit` |
| View flows | `sudo ovs-ofctl dump-flows s1` |
| Clear flows | `sudo ovs-ofctl del-flows s1` |
| Start fresh | `sudo mn -c` |
| Start controller | `ryu-manager ryu_packet_drop_controller.py --observe-links` |
| Check controller logs | See Terminal 2 output |

---

## Test Scenarios Checklist

### Scenario 1: Normal Connectivity ✓
- [ ] Ping from h1 to h2: 0% loss
- [ ] Ping from h3 to h4: 0% loss
- [ ] All flow tables show forwarding rules (not drop)

### Scenario 2: Packet Dropping ✓
- [ ] Enable drop rule: h1 → h2
- [ ] Ping from h1 to h2: 100% loss
- [ ] Flow table shows priority=100 DROP rule
- [ ] Disable drop rule, ping returns to 0% loss

### Scenario 3: Rule Persistence ✓
- [ ] Enable drop rule
- [ ] Send 100 pings: all dropped
- [ ] Wait 30 seconds
- [ ] Send 50 more pings: all still dropped
- [ ] Rule should expire after 60 seconds (hard_timeout)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Controller not connected" | Is Ryu running? Check Terminal 2 for errors |
| "Cannot connect to switch" | Did you start packet_drop_simulator.py? |
| Pings still work with drop rule | Did you restart Ryu after editing config? |
| "ovs-ofctl: no such device" | Is Mininet running? Check Terminal 3 |
| Permission denied | Use `sudo` for Mininet/ovs commands |

---

## Expected Output Summary

### Normal (No Drops)
```
h1 → h2: ping succeeds (0% loss) ✓
Flow tables: Multiple rules, highest priority = 0-1
Throughput: ~1 Gbps
```

### With Drop Rule Enabled
```
h1 → h2: ping fails (100% loss) ✓
Flow tables: High priority (100) rule with "actions=drop"
Throughput: 0 Mbps
```

### Drop Rule Persisting
```
Multiple pings: all fail (100% loss) ✓
Flow table: Rule persists for 60 seconds
After 60s: Rule expires, pings work again
```

---

## What's Happening Behind the Scenes

```
1. You run: mininet> h1 ping -c 5 10.0.0.2
   ↓
2. h1 sends ICMP Echo Request to 10.0.0.2
   ↓
3. Switch s1 receives packet, queries controller (packet_in)
   ↓
4. Controller checks: "Is this h1→h2? Should I drop it?"
   ↓
5a. If NO drop rule: Forward to h2 normally
    ↓
5b. If drop rule enabled: Install DROP rule (priority=100), stop forwarding
    ↓
6. Future packets matching this flow go straight to DROP rule (no controller needed)
   ↓
7. Result: h2 never receives packet, ping times out, 100% loss
```

---

## File Reference

| File | Purpose |
|------|---------|
| `packet_drop_simulator.py` | Main Mininet topology with interactive CLI |
| `ryu_packet_drop_controller.py` | Simple Ryu controller for drop rules |
| `ryu_packet_drop_controller_rest.py` | Advanced controller with REST API |
| `test_packet_drop.py` | Test suite and procedures |
| `rest_api_client.py` | Tool to control drops via REST API |
| `README.md` | Full documentation |
| `QUICKSTART.md` | This file |

---

## Next Steps

1. ✓ Run all three terminals
2. ✓ Test normal connectivity (Option 1 in menu)
3. ✓ See flow tables (Option 4 in menu)
4. ✓ Enable drop rule and test again
5. ✓ Take screenshots for submission
6. ✓ Verify drop rule persists (regression test)

---

## For Submission

Prepare:
- [ ] Screenshots of normal ping (0% loss)
- [ ] Screenshots of drop rule enabled ping (100% loss)
- [ ] Output of `ovs-ofctl dump-flows s1` showing drop rule
- [ ] Controller logs showing packet drop events
- [ ] Test execution output
- [ ] README on GitHub

---

**Ready? Start with Terminal 1 above!** 🚀
