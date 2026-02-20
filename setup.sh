#!/bin/bash

# --- Colors for Professional UI ---
G='\033[92m'
C='\033[96m'
Y='\033[93m'
R='\033[91m'
W='\033[0m'
B='\033[1m'

clear

echo -e "${C}${B}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ "
echo -e "  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█"
echo -e "  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌"
echo -e "  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌"
echo -e "   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪${W}"
echo -e "${Y}      >> The Hunter Edition v7.0 Installer <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# ১. সিস্টেম ডিটেকশন ও আপডেট
echo -e "${C}[*] Identifying environment & updating packages...${W}"
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    pkg update -y && pkg upgrade -y &>/dev/null
else
    OS="linux"
    sudo apt update -y &>/dev/null
fi

# ২. পাইথন ও ডিপেন্ডেন্সি চেক
echo -e "${C}[*] Checking for Python3 and required modules...${W}"
if ! command -v python3 &>/dev/null; then
    echo -e "${Y}[!] Python3 not found. Installing...${W}"
    [ "$OS" == "termux" ] && pkg install python -y || sudo apt install python3 -y
fi

# ৩. লাইব্রেরি ইনস্টলেশন
echo -e "${C}[*] Installing power-libraries (requests, argparse)...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# ৪. গ্লোবাল কমান্ড সেটআপ (The Magic Part)
echo -e "${C}[*] Integrating 'as-recon' into global path...${W}"

# পাইথন ফাইলের নাম যদি as-recon.py হয়, তবে সেটা চেক করা
SCRIPT_NAME="as-recon.py"
if [ ! -f "$SCRIPT_NAME" ]; then
    # যদি ফাই
