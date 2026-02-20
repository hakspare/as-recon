#!/bin/bash

# Detect OS
if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="$PREFIX/bin"; OS="android"; ARCH="arm64"; SUDO=""
else
    BIN_DIR="/usr/bin"; OS="linux"; ARCH="amd64"; SUDO="sudo"
fi

echo -e "\e[1;32m[*] Installing Dependencies...\e[0m"
if [ "$OS" = "android" ]; then
    pkg install curl unzip tar python python-pip -y
    pip install requests
else
    $SUDO apt update && $SUDO apt install curl unzip tar python3 python3-pip -y
    $SUDO pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
fi

install_tool() {
    local name=$1; local url=$2
    if [[ "$url" == *.zip ]]; then
        curl -sL "$url" -o "${name}.zip" && unzip -oq "${name}.zip" && rm "${name}.zip"
    else
        curl -sL "$url" -o "${name}.tar.gz" && tar -xzf "${name}.tar.gz" && rm "${name}.tar.gz"
    fi
    find . -maxdepth 1 -type f -name "$name*" -not -name "*.md" -exec $SUDO mv {} $BIN_DIR/$name \;
    $SUDO chmod +x $BIN_DIR/$name
}

echo -e "\e[1;33m[*] Downloading Binaries...\e[0m"
install_tool "subfinder" "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_${OS}_${ARCH}.zip" &
install_tool "gau" "https://github.com/lc/gau/releases/download/v2.2.3/gau_2.2.3_${OS}_${ARCH}.tar.gz" &
wait

# Install main script
$SUDO cp as-recon.py $BIN_DIR/as-recon
$SUDO chmod +x $BIN_DIR/as-recon

echo -e "\e[1;32m[✓] AS-RECON Pro Installed Successfully!\e[0m"
