#!/bin/bash

# Script to configure CAN-FD interfaces using openarm-can-utils
# Based on 03. OpenArm_모터_CAN_설정.pdf

set -e

if ! command -v openarm-can-configure-socketcan &> /dev/null; then
    echo "Error: openarm-can-configure-socketcan not found."
    echo "Please run './scripts/install_openarm_tools.sh' first."
    exit 1
fi

echo "Configuring can0 (Follower Right)..."
sudo openarm-can-configure-socketcan can0 -fd -b 1000000 -d 5000000

echo "Configuring can1 (Follower Left)..."
sudo openarm-can-configure-socketcan can1 -fd -b 1000000 -d 5000000

echo "CAN interfaces configured successfully."
ip link show can0
ip link show can1
