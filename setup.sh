#!/bin/bash

# কালার কোড
G='\033[92m'
Y='\033[93m'
R='\033[91m'
C='\033[96m'
W='\033[0m'

clear
echo -e "${C}===================================================="
echo -e "          AS-RECON v20.3 - Installer                "
echo -e "       Built for Elite Recon & Bug Hunting          "
echo -e "====================================================${W}"

# ১. সিস্টেম ডিপেন্ডেন্সি চেক ও ইন্সটল
echo -e "\n${Y}[*] Detecting System & Installing Base Dependencies...${W}"
if [ -d "$HOME/.termux" ]; then
    # Termux Setup
    pkg update -y && pkg upgrade -y
    pkg install -y python python-pip sqlite nodejs-lts git libffi libcrypt
    PIP_CMD="pip"
else
    # Linux Setup (Ubuntu/Kali/Debian)
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv sqlite3 git libgraphviz-dev build-essential
    PIP_CMD="pip3"
fi

# ২. পাইথন ভার্চুয়াল এনভায়রনমেন্ট তৈরি
echo -e "${Y}[*] Creating Isolated Python Environment (venv)...${W}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# ৩. পাইথন লাইব্রেরি ইন্সটল (Code v20.3 Requirements)
echo -e "${Y}[*] Installing Specialized Python Libraries...${W}"
$PIP_CMD install --upgrade pip
$PIP_CMD install aiohttp aiodns networkx

# ৪. ফাইল পারমিশন ও ডিরেক্টরি সেটআপ
echo -e "${Y}[*] Finalizing File Permissions...${W}"
chmod +x *.py

# ৫. সাকসেস মেসেজ ও ইউজার গাইড
echo -e "\n${G}===================================================="
echo -e "        INSTALLATION COMPLETED SUCCESSFULLY!         "
echo -e "====================================================${W}"

echo -e "\n${C}কিভাবে ব্যবহার করবেন (How to Use):${W}"
echo -e "১. এনভায়রনমেন্ট চালু করুন: ${G}source venv/bin/activate${W}"
echo -e "২. টুলটি রান করুন: ${G}python3 as_recon.py yourdomain.com${W}"
echo -e "\n${Y}বিঃদ্রঃ: .graphml ফাইলটি দেখার জন্য 'Gephi' সফটওয়্যার ব্যবহার করুন।${W}\n"
