#!/bin/bash

# Packet Drop Simulator - Automated Setup Script
# Usage: sudo bash setup_environment.sh

set -e

echo "======================================"
echo "Packet Drop Simulator Setup"
echo "======================================"
echo ""

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "[!] This script must be run as root (use sudo)"
   exit 1
fi

echo "[*] Step 1: Updating system packages..."
apt update
apt upgrade -y

echo "[*] Step 2: Installing Mininet..."
apt install mininet openvswitch-testcontroller -y

echo "[*] Step 3: Installing Ryu SDN Controller..."
apt install python3-pip -y
pip3 install ryu networkx

echo "[*] Step 4: Installing additional dependencies..."
pip3 install scapy requests tabulate pdfplumber

echo "[*] Step 5: Verifying installations..."

echo ""
echo "Checking versions:"
python3 --version
mininet --version
ryu-manager --version

echo ""
echo "======================================"
echo "[+] Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Open Terminal 1: sudo mn -c"
echo "  2. Open Terminal 2: cd ~/Desktop/SDN_Mininet"
echo "     ryu-manager ryu_packet_drop_controller.py --observe-links"
echo "  3. Open Terminal 3: cd ~/Desktop/SDN_Mininet"
echo "     sudo python3 packet_drop_simulator.py"
echo "  4. Open Terminal 4 (optional): python3 rest_api_client.py --action status"
echo ""
echo "See QUICKSTART.md for detailed instructions"
echo ""
