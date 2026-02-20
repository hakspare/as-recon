#!/bin/bash

echo -e "\e[1;32m[+] AS-RECON Ultra-Fast Setup (Professional Edition)\e[0m"

if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="$PREFIX/bin"
    SUDO=""
else
    BIN_DIR="/usr/bin"
    SUDO="sudo"
fi

install_tool() {
    local tool_name=$1
    local url=$2
    echo -e "\e[1;34m[*] Installing $tool_name...\e[0m"
    curl -sL $url | tar -xz
    $SUDO mv $tool_name $BIN_DIR/
    chmod +x $BIN_DIR/$tool_name
}

echo -e "\e[1;33m[!] Downloading Pre-compiled Binaries...\e[0m"


$SUDO apt update -y || pkg update -y
$SUDO apt install python3 golang git curl -y || pkg install python golang git curl -y

echo -e "\e[1;34m[*] Speeding up with Go Binary Caching...\e[0m"
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest &
go install github.com/projectdiscovery/httpx/cmd/httpx@latest &
go install github.com/lc/gau/v2/cmd/gau@latest &
go install github.com/projectdiscovery/katana/cmd/katana@latest &

wait

cp ~/go/bin/* $BIN_DIR/ 2>/dev/null
cp as-recon.py $BIN_DIR/as-recon
chmod +x $BIN_DIR/as-recon

echo -e "\e[1;32m[✓] AS-RECON is now faster than ever!\e[0m"

