#!/bin/bash
G='\033[92m'
B='\033[1m'
W='\033[0m'

echo -e "${G}${B}[*] AS-RECON v10.2 Global Deployment Start...${W}"

# Cleaning
rm -rf $PREFIX/bin/as-recon
rm -rf /usr/local/bin/as-recon

# Install deps
pip install requests urllib3 --quiet

# Permissions & Copy
chmod +x as-recon.py
if [ -d "$PREFIX/bin" ]; then
    cp as-recon.py $PREFIX/bin/as-recon
    chmod +x $PREFIX/bin/as-recon
    echo -e "${G}[✓] Global command created in Termux!${W}"
else
    sudo cp as-recon.py /usr/local/bin/as-recon
    sudo chmod +x /usr/local/bin/as-recon
    echo -e "${G}[✓] Global command created in Linux!${W}"
fi

hash -r
echo -e "\n${G}${B}Deployment Complete! Run with: as-recon -d canva.com${W}"
