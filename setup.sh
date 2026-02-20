#!/bin/bash

# --- Colors ---
G='\033[92m'
C='\033[96m'
Y='\033[93m'
R='\033[91m'
W='\033[0m'

clear
echo -e "${C}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ "
echo -e "  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█"
echo -e "  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌"
echo -e "  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌"
echo -e "   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪${W}"
echo -e "${Y}      >> Turbo Installer v7.1 <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# এনভায়রনমেন্ট চেক
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
else
    OS="linux"
fi

echo -e "${C}[*] Installing dependencies...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

echo -e "${C}[*] Setting up 'as-recon' command...${W}"

# ফাইলের নাম নিশ্চিত করা
SCRIPT="as-recon.py"

if [ -f "$SCRIPT" ]; then
    chmod +x "$SCRIPT"
    if [ "$OS" == "termux" ]; then
        cp "$SCRIPT" "$PREFIX/bin/as-recon"
        chmod +x "$PREFIX/bin/as-recon"
    else
        sudo cp "$SCRIPT" "/usr/local/bin/as-recon"
        sudo chmod +x "/usr/local/bin/as-recon"
    fi
    echo -e "${G}[✓] Global command established!${W}"
else
    echo -e "${R}[!] Error: $SCRIPT not found!${W}"
    exit 1
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "${G}Setup Complete! Use: ${C}as-recon -d domain.com --live -t 100${W}"
echo -e "${G}--------------------------------------------------------${W}"
