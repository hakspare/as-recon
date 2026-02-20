#!/bin/bash

echo -e "\e[1;32m[+] AS-RECON Extreme Fast Setup (Speed Optimized)\e[0m"

if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="$PREFIX/bin"
    OS="android"
    ARCH="arm64"
    SUDO=""
else
    BIN_DIR="/usr/bin"
    OS="linux"
    ARCH="amd64"
    SUDO="sudo"
fi

echo -e "\e[1;34m[*] Checking dependencies...\e[0m"
if [ "$OS" = "android" ]; then
    pkg install curl unzip tar -y
else
    $SUDO apt update && $SUDO apt install curl unzip tar -y
fi

install_binary() {
    local name=$1
    local url=$2
    echo -e "\e[1;34m[*] Installing $name...\e[0m"
    
    if [[ "$url" == *.zip ]]; then
        curl -sL "$url" -o "${name}.zip"
        unzip -oq "${name}.zip"
        rm "${name}.zip"
    else
        curl -sL "$url" -o "${name}.tar.gz"
        tar -xzf "${name}.tar.gz"
        rm "${name}.tar.gz"
    fi

    find . -maxdepth 1 -type f -name "$name*" -not -name "*.md" -exec $SUDO mv {} $BIN_DIR/$name \;
    $SUDO chmod +x $BIN_DIR/$name
    echo -e "\e[1;32m[✓] $name ready!\e[0m"
}

echo -e "\e[1;33m[!] Instant Installation starting (Parallel Mode)...\e[0m"

install_binary "subfinder" "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_${OS}_${ARCH}.zip" &
install_binary "httpx" "https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_${OS}_${ARCH}.zip" &
install_binary "gau" "https://github.com/lc/gau/releases/download/v2.2.3/gau_2.2.3_${OS}_${ARCH}.tar.gz" &
install_binary "katana" "https://github.com/projectdiscovery/katana/releases/download/v1.1.0/katana_1.1.0_${OS}_${ARCH}.zip" &

wait

if [ -f "as-recon.py" ]; then
    $SUDO cp as-recon.py $BIN_DIR/as-recon
    $SUDO chmod +x $BIN_DIR/as-recon
fi

echo -e "\e[1;32m\n[★] Success! AS-RECON is now installed and faster than light.\e[0m"
echo -e "\e[1;33m[Usage] as-recon -d example.com\e[0m"
