#!/bin/bash

# Script to install OpenArm CAN utilities and dependencies
# Based on 03. OpenArm_모터_CAN_설정.pdf

set -e

echo "Starting OpenArm CAN Tools Installation..."

# 1. Install software-properties-common
sudo apt install -y software-properties-common

# 2. Add OpenArm PPA
sudo add-apt-repository -y ppa:openarm/main

# 3. Update package list
sudo apt update

# 4. Install CAN utilities and OpenArm libraries
sudo apt install -y can-utils iproute2 libopenarm-can-dev openarm-can-utils

# 5. Install python library in the project venv if it exists
if [ -d "venv" ]; then
    echo "Installing openarm_can in virtual environment..."
    ./venv/bin/pip install openarm-can
fi

echo "Installation complete!"
echo "Next step: Run './scripts/setup_can_fd.sh' to configure your CAN interfaces."
