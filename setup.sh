#!/bin/bash

echo -e "\e[1;32m[+] AS-RECON Pro - Professional Setup Starting...\e[0m"

# ১. ওএস এবং আর্কিটেকচার ডিটেকশন (Termux vs Linux)
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

# ২. প্রয়োজনীয় প্যাকেজ এবং পাইথন লাইব্রেরি ইনস্টল
echo -e "\e[1;34m[*] Installing dependencies...\e[0m"
if [ "$OS" = "android" ]; then
    pkg install curl unzip tar python python-pip -y
    pip install requests
else
    $SUDO apt update && $SUDO apt install curl unzip tar python3 python3-pip -y
    $SUDO pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
fi

# ৩. বাইনারি টুলস ইনস্টল ফাংশন (Error handling সহ)
install_tool() {
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

    # বাইনারি ফাইল খুঁজে বের করা এবং পারমিশন দেওয়া
    find . -maxdepth 1 -type f -name "$name*" -not -name "*.md" -exec $SUDO mv {} $BIN_DIR/$name \;
    $SUDO chmod +x $BIN_DIR/$name
}

# ৪. সব টুলস ডাউনলোড ও সেটআপ (Parallel Mode)
echo -e "\e[1;33m[!] Downloading binaries (Subfinder, GAU, HTTPX)...\e[0m"
install_tool "subfinder" "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_${OS}_${ARCH}.zip" &
install_tool "httpx" "https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_${OS}_${ARCH}.zip" &
install_tool "gau" "https://github.com/lc/gau/releases/download/v2.2.3/gau_2.2.3_${OS}_${ARCH}.tar.gz" &
wait

# ৫. মেইন কমান্ড সেটআপ
if [ -f "as-recon.py" ]; then
    $SUDO cp as-recon.py $BIN_DIR/as-recon
    $SUDO chmod +x $BIN_DIR/as-recon
fi

echo -e "\e[1;32m\n[★] Success! AS-RECON Pro is now ready for your users.\e[0m"
echo -e "\e[1;33m[Usage] as-recon -d example.com -t 20\e[0m"
