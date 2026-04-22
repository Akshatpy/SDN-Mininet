#!/bin/bash

# Packet Drop Simulator - Automated Setup Script
# Usage: bash setup_environment.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

if [[ $EUID -ne 0 ]]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "======================================"
echo "Packet Drop Simulator Setup"
echo "======================================"
echo ""

echo "[*] Step 1: Updating system packages..."
$SUDO apt update
$SUDO apt upgrade -y

echo "[*] Step 2: Installing build essentials and dependencies..."
$SUDO apt install mininet openvswitch-testcontroller build-essential libssl-dev libffi-dev python3-dev wget curl git -y

echo "[*] Step 3: Installing Ryu SDN Controller..."
$SUDO apt install python3-pip python3-full -y

echo "[*] Step 3b: Creating virtual environment and installing dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# Install dependencies first
pip install --upgrade pip
pip install pbr setuptools wheel
# Python 3.12-compatible runtime deps for Ryu
pip install "eventlet>=0.40.0" "dnspython>=2.0.0" gevent msgpack six pyyaml netaddr lxml
pip install oslo.config oslo.i18n routes webob stevedore "tinyrpc==1.0.4" ovs

# Install from source with Python 3.12 compatibility patch.
echo "[*] Attempting to install Ryu..."
cd /tmp
rm -rf ryu-src ryu-4.34 ryu.tar.gz 2>/dev/null || true

if git clone https://github.com/faucetsdn/ryu.git ryu-src >/dev/null 2>&1; then
    cd ryu-src
else
    curl -L -o ryu.tar.gz https://github.com/faucetsdn/ryu/archive/refs/heads/master.tar.gz >/dev/null 2>&1
    tar xzf ryu.tar.gz
    cd ryu-master
fi

# Python 3.12 compatibility: easy_install.get_script_args may not exist.
sed -i 's/_main_module()._orig_get_script_args = easy_install.get_script_args/_main_module()._orig_get_script_args = getattr(easy_install, "get_script_args", lambda *args, **kwargs: [])/' ryu/hooks.py || true

# Avoid PEP 517 isolation path that triggers incompatible build behavior.
if PIP_USE_PEP517=0 python3 setup.py install >/dev/null 2>&1 || PIP_USE_PEP517=0 pip install --no-build-isolation --no-deps . >/dev/null 2>&1; then
    echo "[+] Ryu installed successfully"
else
    echo "[!] Ryu installation failed"
fi

# Install additional packages
pip install networkx scapy requests tabulate pdfplumber

echo "[*] Step 4: Verifying installations..."

echo ""
echo "Checking versions:"
python3 --version
mn --version
ryu-manager --version 2>/dev/null || python3 -m ryu.cmd.manager --version 2>/dev/null || echo "[!] Ryu not available"

echo ""
echo "======================================"
echo "[+] Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     cd $PROJECT_DIR"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Open Terminal 1: $SUDO mn -c"
echo "  3. Open Terminal 2: cd $PROJECT_DIR"
echo "     source .venv/bin/activate"
echo "     ryu-manager ryu_packet_drop_controller.py --observe-links"
echo "     # fallback if command not found: python3 -m ryu.cmd.manager ryu_packet_drop_controller.py --observe-links"
echo "  4. Open Terminal 3: cd $PROJECT_DIR"
echo "     source .venv/bin/activate"
echo "     sudo python3 packet_drop_simulator.py"
echo "  5. Open Terminal 4 (optional): "
echo "     source .venv/bin/activate"
echo "     python3 rest_api_client.py --action status"
echo ""
echo "See QUICKSTART.md for detailed instructions"
echo ""
