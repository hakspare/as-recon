#!/bin/bash

# কালার
G='\033[92m' ; W='\033[0m' ; C='\033[96m'

echo -e "${C}[*] AS-RECON Ultimate v5.0 Installer Initializing...${W}"

# Python & Depedencies
pkg install python -y &>/dev/null
pip install requests urllib3 --no-cache-dir &>/dev/null

# কমান্ড হিসেবে সেটআপ করা
sed -i '1i #!/usr/bin/env python3' as-recon.py
chmod +x as-recon.py
cp as-recon.py $PREFIX/bin/as-recon

echo -e "${G}[✓] Global Command 'as-recon' Installed Successfully!${W}"
echo -e "${C}[*] Type 'as-recon -h' for help menu.${W}"
