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
echo -e "${Y}      >> v8.0 The Sentinel: Deployment Script <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# ১. এনভায়রনমেন্ট ডিটেকশন (Termux vs Linux)
echo -e "${C}[*] Identifying system architecture...${W}"
if [ -d "$PREFIX/bin" ]; then
    OS="termux"
    echo -e "${G}[✓] Termux environment detected.${W}"
else
    OS="linux"
    echo -e "${G}[✓] Linux distribution detected.${W}"
fi

# ২. পাইথন প্যাকেজ এবং নতুন ফিল্টারিং লাইব্রেরি ইনস্টলেশন
echo -e "${C}[*] Installing dependencies & intelligence modules...${W}"
# requests এবং urllib3 ছাড়াও v8.0 এর জন্য আর কিছু এক্সট্রা প্রয়োজন নেই, তবে আপডেট নিশ্চিত করা হচ্ছে
pip install --upgrade pip &>/dev/null
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# ৩. গ্লোবাল কমান্ড কনফিগারেশন
echo -e "${C}[*] Setting up 'as-recon' in system path...${W}"

# পাইথন ফাইলের নাম চেক করা
PY_FILE="as-recon.py"

if [ -f "$PY_FILE" ]; then
    # ফাইলে এক্সিকিউশন পারমিশন দেওয়া
    chmod +x "$PY_FILE"
    
    if [ "$OS" == "termux" ]; then
        # Termux এর জন্য /data/data/com.termux/files/usr/bin এ কপি করা
        cp "$PY_FILE" "$PREFIX/bin/as-recon"
        chmod +x "$PREFIX/bin/as-recon"
    else
        # লিনাক্সের জন্য /usr/local/bin এ কপি করা (Sudo প্রয়োজন হতে পারে)
        sudo cp "$PY_FILE" "/usr/local/bin/as-recon"
        sudo chmod +x "/usr/local/bin/as-recon"
    fi
    echo -e "${G}[✓] Global command established successfully!${W}"
else
    echo -e "${R}[!] Error: $PY_FILE not found in the current directory.${
