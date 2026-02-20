#!/bin/bash

G='\033[92m'
C='\033[96m'
Y='\033[93m'
R='\033[91m'
W='\033[0m'
B='\033[1m'

clear

echo -e "${C}${B}>> AS-RECON v9.2: Permanent Fix Installer <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    echo -e "${G}[✓] System: Termux${W}"
else
    OS="linux"
    echo -e "${G}[✓] System: Linux/Kali${W}"
fi

echo -e "${C}[*] Updating dependencies...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

PY_FILE="as-recon.py"

if [ -f "$PY_FILE" ]; then
    chmod +x "$PY_FILE"
    if [ "$OS" == "termux" ]; then
        cp "$PY_FILE" "$PREFIX/bin/as-recon"
        chmod +x "$PREFIX/bin/as-recon"
    else
        sudo cp "$PY_FILE" "/usr/local/bin/as-recon"
        sudo chmod +x "/usr/local/bin/as-recon"
    fi
    echo -e "${G}[✓] Binary updated to v9.2 successfully!${W}"
else
    echo -e "${R}[!] Error: $PY_FILE not found!${W}"
    exit 1
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "Try now: ${C}as-recon -d renesabazar.com --live -o list.txt${W}"
