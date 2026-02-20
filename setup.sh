#!/bin/bash

# --- কালার এবং স্টাইল ---
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

# ১. এনভায়রনমেন্ট ডিটেকশন
echo -e "${C}[*] Identifying environment...${W}"
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    echo -e "${G}[✓] Termux detected.${W}"
else
    OS="linux"
    echo -e "${G}[✓] Linux detected.${W}"
fi

# ২. পাইথন লাইব্রেরি ইনস্টল
echo -e "${C}[*] Installing dependencies...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# ৩. গ্লোবাল কমান্ড সেটআপ
echo -e "${C}[*] Integrating 'as-recon' into system path...${W}"

# ফাইলের নাম ঠিক করা (v7.0 কোডটি যে ফাইলে আছে)
SCRIPT_NAME="as-recon.py"

if [ -f "$SCRIPT_NAME" ]; then
    chmod +x "$SCRIPT_NAME"
    if [ "$OS" == "termux" ]; then
        cp "$SCRIPT_NAME" "$PREFIX/bin/as-recon"
        chmod +x "$PREFIX/bin/as-recon"
    else
        sudo cp "$SCRIPT_NAME" "/usr/local/bin/as-recon"
        sudo chmod +x "/usr/local/bin/as-recon"
    fi
    echo -e "${G}[✓] Global command 'as-recon' is ready!${W}"
else
    echo -e "${R}[!] Error: $SCRIPT_NAME not found in this folder!${W}"
    exit 1
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "${G}${B}[✓] INSTALLATION SUCCESSFUL!${W}"
echo -e "${Y}Now you can run the tool by just typing: ${C}as-recon${W}"
echo -e "${G}--------------------------------------------------------${W}"
