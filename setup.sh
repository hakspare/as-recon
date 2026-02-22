#!/bin/bash

# Colors for UI
G='\033[92m'
Y='\033[93m'
R='\033[91m'
C='\033[96m'
W='\033[0m'

echo -e "${C}===================================================="
echo -e "          AS-RECON PRO: GLOBAL INSTALLER            "
echo -e "====================================================${W}"

# 1. Dependency Install
echo -e "${Y}[*] Installing dependencies...${W}"
sudo apt update -y && sudo apt install -y python3 python3-pip python3-venv sqlite3 git

# 2. Setup Directory & Venv
INSTALL_DIR="/opt/as-recon"
echo -e "${Y}[*] Setting up system directory: $INSTALL_DIR${W}"
sudo mkdir -p $INSTALL_DIR
sudo cp -r . $INSTALL_DIR
cd $INSTALL_DIR

# 3. Virtual Environment Creation
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install aiohttp aiodns networkx rich pyyaml

# 4. Creating Global Binary Wrapper (Amass/Subfinder Style)
# Etai main kaj: User jeno sorasori 'asrecon' likhle run hoy
echo -e "${Y}[*] Creating global command executable...${W}"
cat <<EOF | sudo tee /usr/local/bin/asrecon > /dev/null
#!/bin/bash
source $INSTALL_DIR/venv/bin/activate
python3 $INSTALL_DIR/as_recon.py "\$@"
EOF

# 5. Permission Set
sudo chmod +x /usr/local/bin/asrecon
sudo chmod +x $INSTALL_DIR/as_recon.py

echo -e "\n${G}===================================================="
echo -e "        SUCCESSFULLY INSTALLED GLOBALLY!            "
echo -e "====================================================${W}"

echo -e "\n${C}Usage (Commercial Style):${W}"
echo -e "Just type: ${G}asrecon google.com${W}"
echo -e "For help:  ${G}asrecon -h${W}"
echo -e "\n${Y}Note: App data & DB saved in: $INSTALL_DIR${W}\n"
