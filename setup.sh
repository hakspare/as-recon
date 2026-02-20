#!/bin/bash

# --- Color Definitions ---
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
echo -e "${Y}      >> v9.1 God-Eye (Fixed): Deployment Script <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# 1. Environment Check
echo -e "${C}[*] Detecting system architecture...${W}"
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    echo -e "${G}[✓] Termux detected.${W}"
else
    OS="linux"
    echo -e "${G}[✓] Linux/Kali detected.${W}"
fi

# 2. Dependency Installation
echo -e "${C}[*] Installing
