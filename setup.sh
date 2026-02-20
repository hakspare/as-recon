#!/bin/bash

# ১. ওএস এবং পাথ ডিটেকশন
if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="$PREFIX/bin"
    OS="android"
    ARCH="arm64"
else
    BIN_DIR="/usr/bin"
    OS="linux"
    ARCH="amd64"
    SUDO="sudo"
fi

# ২. পাইথন লাইব্রেরি ইনস্টল (ইউজারের কোনো এরর আসবে না)
if [ "$OS" = "android" ]; then
    pkg install python python-pip -y
    pip install requests
else
    $SUDO apt update && $SUDO apt install python3 python3-pip -y
    $SUDO pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
fi

# ৩. বাইনারি টুলস ইনস্টল ফাংশন
install_tool() {
    curl -sL "$2" -o "${1}.zip" || curl -sL "$2" -o "${1}.tar.gz"
    if [[ "$2" == *.zip ]]; then unzip -oq "${1}.zip"; else tar -xzf "${1}.tar.gz"; fi
    find . -maxdepth 1 -type f -name "$1*" -not -name "*.md" -exec $SUDO mv {} $BIN_DIR/$1 \;
    $SUDO chmod +x $BIN_DIR/$1
    rm "${1}.zip" "${1}.tar.gz" 2>/dev/null
}

# ৪. প্যারালাল ইনস্টলেশন
install_tool "subfinder" "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_${OS}_${ARCH}.zip" &
install_tool "httpx" "https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_${OS}_${ARCH}.zip" &
install_tool "gau" "https://github.com/lc/gau/releases/download/v2.2.3/gau_2.2.3_${OS}_${ARCH}.tar.gz" &
wait

# ৫. ফাইনাল লিঙ্ক ফিক্স (ইউজারের জন্য স্থায়ী সমাধান)
$SUDO cp as-recon.py $BIN_DIR/as-recon
$SUDO chmod +x $BIN_DIR/as-recon

echo -e "\e[1;32m[✓] AS-RECON Pro has been successfully installed for you!\e[0m"
