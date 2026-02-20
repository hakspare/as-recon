#!/bin/bash

# --- Color Palette ---
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
echo -e "${Y}      >> v9.0 God Eye: Intelligence Deployment <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# 1. Platform Detection
echo -e "${C}[*] Probing system environment...${W}"
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    echo -e "${G}[✓] Environment: Termux${W}"
    # টার্মাক্সে dnsutils (nslookup/dig) নিশ্চিত করা
    if ! command -v nslookup &>/dev/null; then
        echo -e "${Y}[!] Installing DNS utilities...${W}"
        pkg install dnsutils -y &>/dev/null
    fi
else
    OS="linux"
    echo -e "${G}[✓] Environment: Linux/Kali${W}"
fi

# 2. Dependency Management
echo -e "${C}[*] Updating core dependencies...${W}"
pip install --upgrade pip &>/dev/null
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# 3. Global Integration
echo -e "${C}[*] Configuring Global Execution Path...${W}"

PY_FILE="as-recon.py"

if [ -f "$PY_FILE" ]; then
    # ফাইল পারমিশন ফিক্স
    chmod +x "$PY_FILE"
    
    if [ "$OS" == "termux" ]; then
        # Termux Binary Setup
        cp "$PY_FILE" "$PREFIX/bin/as-recon"
        chmod +x "$PREFIX/bin/as-recon"
    else
        # Linux Binary Setup
        sudo cp "$PY_FILE" "/usr/local/bin/as-recon"
        sudo chmod +x "/usr/local/bin/as-recon"
    fi
    echo -e "${G}[✓] AS-RECON is now a global command.${W}"
else
    echo -e "${R}[!] Fatal Error: $PY_FILE not found in the current directory.${W}"
    exit 1
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "${G}${B}[✓] GOD EYE ENGINE DEPLOYED SUCCESSFULLY!${W}"
echo -e "${Y}False Positives will now be terminated with extreme prejudice.${W}"
echo -e "${G}--------------------------------------------------------${W}"
echo -e "Command: ${C}as-recon -d target.com --live${W}"
