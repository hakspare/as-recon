#!/bin/bash

# কালার কোডস
G='\033[92m'
C='\033[96m'
Y='\033[93m'
R='\033[91m'
W='\033[0m'

clear

echo -e "${C}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ "
echo -e "  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█"
echo -e "  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌"
echo -e "  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌"
echo -e "   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪${W}"
echo -e "${Y}      >> HyperDrive Framework v6.2 Installer <<${W}"
echo -e "${G}--------------------------------------------------------${W}"

# ১. সিস্টেম আপডেট ও পাইথন চেক
echo -e "${C}[*] Updating system & checking dependencies...${W}"
pkg update -y && pkg upgrade -y &>/dev/null || apt update -y && apt upgrade -y &>/dev/null

if command -v python3 &>/dev/null; then
    echo -e "${G}[✓] Python3 is already installed.${W}"
else
    echo -e "${Y}[!] Installing Python3...${W}"
    pkg install python -y || apt install python3 -y
fi

# ২. প্রয়োজনীয় লাইব্রেরি ইনস্টল
echo -e "${C}[*] Installing professional python libraries...${W}"
pip install requests urllib3 argparse --no-cache-dir &>/dev/null

# ৩. কমান্ড লাইন কনফিগারেশন
echo -e "${C}[*] Configuring global command 'as-recon'...${W}"

# Shebang লাইন যোগ করা (যদি না থাকে)
if ! grep -q "#!/usr/bin/env python3" as-recon.py; then
    sed -i '1i #!/usr/bin/env python3' as-recon.py
fi

# পারমিশন ও কপি করা
chmod +x as-recon.py
if [ -d "$PREFIX/bin" ]; then
    # Termux এর জন্য
    cp as-recon.py $PREFIX/bin/as-recon
else
    # Linux এর জন্য
    sudo cp as-recon.py /usr/local/bin/as-recon
fi

echo -e "${G}--------------------------------------------------------${W}"
echo -e "${G}[✓] AS-RECON HyperDrive Setup Successfully!${W}"
echo -e "${Y}[*] You can now run the tool from anywhere by typing:${W} ${C}as-recon${W}"
echo -e "${G}--------------------------------------------------------${W}"
echo -e "${Y}Usage: ${W}as-recon -d google.com"
echo -e "${Y}Help:  ${W}as-recon -h"
