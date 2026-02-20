#!/bin/bash

# প্রসেসর ডিটেকশন (Fix for Exit Status 132)
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH_TYPE="amd64"
elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    ARCH_TYPE="arm64"
else
    ARCH_TYPE="386"
fi

if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="$PREFIX/bin"; OS="android"; SUDO=""
else
    BIN_DIR="/usr/bin"; OS="linux"; SUDO="sudo"
fi

echo -e "\e[1;32m[*] Installing Dependencies for $ARCH_TYPE...\e[0m"
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
    # বাইনারি ফাইল খুঁজে সঠিক জায়গায় মুভ করা
    find . -maxdepth 1 -type f -name "$name*" -not -name "*.md" -exec $SUDO mv {} $BIN_DIR/$name \;
    $SUDO chmod +x $BIN_DIR/$name
}

echo -e "\e[1;33m[*] Downloading Correct Binaries for your CPU...\e[0m"
# Subfinder installation
install_tool "subfinder" "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_${ARCH_TYPE}.zip" &
# GAU installation
install_tool "gau" "https://github.com/lc/gau/releases/download/v2.2.3/gau_2.2.3_linux_${ARCH_TYPE}.tar.gz" &
wait

# Install main as-recon script
$SUDO cp as-recon.py $BIN_DIR/as-recon
$SUDO chmod +x $BIN_DIR/as-recon

echo -e "\e[1;32m[✓] AS-RECON Pro Fixed and Installed Successfully!\e[0m"
