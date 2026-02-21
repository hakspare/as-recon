#!/bin/bash

# --- Color Definitions ---
G='\033[92m'
R='\033[91m'
Y='\033[93m'
B='\033[1m'
W='\033[0m'

echo -e "${G}${B}"
echo "   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ "
echo "  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█"
echo "  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄  ▐█▐▐▌"
echo "  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌"
echo "   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪"
echo -e "${Y}        >> AS-RECON v10.2 Installer <<${W}"

# ১. পুরনো ফাইল ক্লিন করা
echo -e "\n${Y}[*] Cleaning old installations...${W}"
rm -rf $PREFIX/bin/as-recon
rm -rf /usr/local/bin/as-recon

# ২. পাইথন ডিপেন্ডেন্সি ইন্সটল করা
echo -e "${G}[*] Installing dependencies (requests, urllib3)...${W}"
pip install requests urllib3 --quiet

# ৩. মেইন ফাইলকে এক্সিকিউটেবল করা
if [ -f "as-recon.py" ]; then
    chmod +x as-recon.py
    
    # ৪. সিস্টেম অনুযায়ী পাথ সেট করা (Termux vs Linux)
    if [ -d "$PREFIX/bin" ]; then
        # For Termux
        cp as-recon.py $PREFIX/bin/as-recon
        chmod +x $PREFIX/bin/as-recon
        echo -e "${G}[✓] Global command 'as-recon' created in Termux!${W}"
    else
        # For Linux/Kali
        sudo cp as-recon.py /usr/local/bin/as-recon
        sudo chmod +x /usr/local/bin/as-recon
        echo -e "${G}[✓] Global command 'as-recon' created in Linux!${W}"
    fi
    
    # ৫. ক্যাশ রিফ্রেশ
    hash -r
    echo -e "\n${B}${G}Successfully Deployed AS-RECON v10.2!${W}"
    echo -e "${B}Usage:${W} as-recon -d google.com"
else
    echo -e "${R}[!] Error: as-recon.py not found in this directory!${W}"
    exit 1
fi
