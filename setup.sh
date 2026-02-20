#!/bin/bash

# --- Color Palette ---
G='\033[92m'
C='\033[96m'
Y='\033[93m'
R='\033[91m'
W='\033[0m'
B='\033[1m'

clear

echo -e "${C}${B}>> AS-RECON v10.2.1: Critical Syntax Fix <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# 1. Detect Path
BIN_PATH="/usr/local/bin"
if [ -d "$PREFIX/bin" ]; then
    BIN_PATH="$PREFIX/bin"
    OS="Termux"
else
    OS="Linux/Kali"
fi

echo -e "${C}[*] System detected: ${Y}$OS${W}"

# 2. Cleanup
echo -e "${C}[*] Removing legacy binaries...${W}"
rm -f "$BIN_PATH/as-recon"

# 3. Dependency Check
echo -e "${C}[*] Ensuring Python modules...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# 4. Install new version
PY_FILE="as-recon.py"

if [ -f "$PY_FILE" ]; then
    echo -e "${C}[*] Configuring global access...${W}"
    chmod +x "$PY_FILE"
    
    if [ "$OS" == "Termux" ]; then
        cp "$PY_FILE" "$BIN_PATH/as-recon"
        chmod +x "$BIN_PATH/as-recon"
    else
        sudo cp "$PY_FILE" "$BIN_PATH/as-recon"
        sudo chmod +x "$BIN_PATH/as-recon"
    fi
    echo -e "${G}[✓] Binary linked successfully!${W}"
else
    echo -e "${R}[!] Error: $PY_FILE not found!${W}"
    exit 1
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "${G}${B}[✓] v10.2.1 DEPLOYED!${W}"
echo -e "Run: ${C}as-recon -d renesabazar.com --live -o ll.txt${W}"
