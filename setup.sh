#!/bin/bash
BIN_PATH="/usr/local/bin"
[ -d "$PREFIX/bin" ] && BIN_PATH="$PREFIX/bin"

# পুরাতন ফাইল ডিলিট
rm -f $BIN_PATH/as-recon

# পারমিশন ও লিংক
chmod +x as-recon.py
cp as-recon.py $BIN_PATH/as-recon
chmod +x $BIN_PATH/as-recon

echo -e "\033[92m[✓] AS-RECON v10.1 Deployed. Raw Intel issue fixed.\033[0m"
