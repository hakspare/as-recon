#!/bin/bash

# Colors
G='\033[92m'
Y='\033[93m'
R='\033[91m'
C='\033[96m'
W='\033[0m'

clear
echo -e "${C}===================================================="
echo -e "          AS-RECON PRO: GLOBAL INSTALLER            "
echo -e "      (Auto-detect & Global Command Setup)          "
echo -e "====================================================${W}"

# 1. Check for main python file (Auto-detect name)
MAIN_FILE=$(ls | grep -E "as[-_]recon\.py" | head -n 1)

if [ -z "$MAIN_FILE" ]; then
    echo -e "${R}[!] Error: Main python file (as-recon.py) not found!${W}"
    exit 1
fi

echo -e "${G}[+] Found main file: $MAIN_FILE${W}"

# 2. Dependency Install
echo -e "${Y}[*] Installing dependencies...${W}"
sudo apt update -y && sudo apt install -y python3 python3-pip python3-venv sqlite3 git

# 3. Setup Directory
INSTALL_DIR="/opt/as-recon"
sudo mkdir -p $INSTALL_DIR
sudo cp -r . $INSTALL_DIR
cd $INSTALL_DIR

# 4. Virtual Environment Setup
echo -e "${Y}[*] Setting up Virtual Environment...${W}"
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install aiohttp aiodns networkx rich pyyaml

# 5. Creating Global Binary (Dynamic Name Support)
echo -e "${Y}[*] Creating global command: asrecon${W}"
cat <<EOF | sudo tee /usr/local/bin/asrecon > /dev/null
#!/bin/bash
source $INSTALL_DIR/venv/bin/activate
python3 $INSTALL_DIR/$MAIN_FILE "\$@"
EOF

# 6. Final Permissions
sudo chmod +x /usr/local/bin/asrecon
sudo chmod +x $INSTALL_DIR/$MAIN_FILE

echo -e "\n${G}===================================================="
echo -e "        SUCCESSFULLY INSTALLED GLOBALLY!            "
echo -e "====================================================${W}"

echo -e "\n${C}Usage:${W}"
echo -e "Just type: ${G}asrecon google.com${W}"
echo -e "For help:  ${G}asrecon -h${W}\n"
