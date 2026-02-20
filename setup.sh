#!/bin/bash
clear
echo -e "\033[96m[*] Deploying AS-RECON v10.0 Overlord Engine...\033[0m"

# Termux/Linux Fix
BIN_PATH="/usr/local/bin"
[ -d "$PREFIX/bin" ] && BIN_PATH="$PREFIX/bin"

# Cleanup old binaries
rm -f $BIN_PATH/as-recon

# Install dependencies
pip install requests urllib3 --no-cache-dir &>/dev/null

# Make executable and link
chmod +x as-recon.py
cp as-recon.py $BIN_PATH/as-recon
chmod +x $BIN_PATH/as-recon

echo -e "\033[92m[✓] System Armed. Use 'as-recon -d target.com --live'\033[0m"
