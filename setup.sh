#!/bin/bash

# Colors
G='\033[92m'
Y='\033[93m'
B='\033[1m'
W='\033[0m'

echo -e "${G}${B}[*] AS-RECON v10.2: Professional Installation Start...${W}"

# Removing old versions
echo -e "${Y}[*] Cleaning old bin files...${W}"
rm -rf $PREFIX/bin/as-recon /usr/local/bin/as-recon

# Installing dependencies
echo -e "${G}[*] Installing requirements (requests, urllib3)...${W}"
pip install requests urllib3 --quiet

# Setting up global command
chmod +x as-recon.py

if [ -d "$PREFIX/bin" ]; then
    # Termux Setup
    cp as-recon.py $PREFIX/bin/as-recon
    chmod +x $PREFIX/bin/as-recon
    echo -e "${G}[✓] Global command 'as-recon' set in Termux!${W}"
else
    # Linux Setup
    sudo cp as-recon.py /usr/local/bin/as-recon
    sudo chmod +x /usr/local/bin/as-recon
    echo -e "${G}[✓] Global command 'as-recon' set in Linux!${W}"
fi

hash -r
echo -e "\n${B}${G}Successfully Updated to v10.2!${W}"
echo -e "Usage: as-recon -d example.com --live"
