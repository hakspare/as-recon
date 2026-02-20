#!/bin/bash

# --- Colors ---
G='\033[92m'
R='\033[91m'
B='\033[1m'
W='\033[0m'

echo -e "${G}${B}[*] AS-RECON v10.2 Global Deployment...${W}"

# ১. পুরনো সব ফাইল পরিষ্কার করা (যাতে কোনো এরর না থাকে)
rm -rf $PREFIX/bin/as-recon
rm -rf /usr/local/bin/as-recon

# ২. পাইথন ডিপেন্ডেন্সি চেক
echo -e "${G}[*] Installing required modules...${W}"
pip install requests urllib3

# ৩. মেইন ফাইলকে এক্সিকিউটেবল করা
chmod +x as-recon.py

# ৪. ইউজারের সিস্টেম অনুযায়ী কমান্ড সেট করা
if [ -d "$PREFIX/bin" ]; then
    # টারমাক্স (Termux) ইউজারদের জন্য
    cp as-recon.py $PREFIX/bin/as-recon
    chmod +x $PREFIX/bin/as-recon
    echo -e "${G}[✓] AS-RECON is now a global command in Termux!${W}"
else
    # লিনাক্স (Linux/Kali) ইউজারদের জন্য
    sudo cp as-recon.py /usr/local/bin/as-recon
    sudo chmod +x /usr/local/bin/as-recon
    echo -e "${G}[✓] AS-RECON is now a global command in Linux!${W}"
fi

echo -e "\n${B}${G}Successfully Updated to v10.2!${W}"
echo -e "${B}Usage: as-recon -d domain.com${W}"
