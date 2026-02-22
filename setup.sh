#!/bin/bash

# ═══════════════════════════════════
# AS-RECON Commercial Installer v21.0
# Author: Ajijul Islam Shohan (@hakspare)
# ═══════════════════════════════════

# Colors
G='\033[92m'
Y='\033[93m'
R='\033[91m'
B='\033[1m'
W='\033[0m'

echo -e "${G}${B}[*] AS-RECON v21.0 Commercial Installer Starting...${W}"

# Detect OS
OS=$(uname -s)
echo -e "${Y}[*] Detected OS: $OS${W}"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${R}[✗] Python3 not found! Install Python3 first.${W}"
    exit 1
fi
PYTHON_VERSION=$(python3 -V | awk '{print $2}')
echo -e "${G}[✓] Python OK: $PYTHON_VERSION${W}"

# Check git
if ! command -v git &>/dev/null; then
    echo -e "${R}[✗] git not found! Install git first.${W}"
    exit 1
fi

# Check curl
if ! command -v curl &>/dev/null; then
    echo -e "${R}[✗] curl not found! Install curl first.${W}"
    exit 1
fi

# Check jq
if ! command -v jq &>/dev/null; then
    echo -e "${R}[✗] jq not found! Install jq first.${W}"
    exit 1
fi

# Setup directories
VENV_DIR="$HOME/.as-recon-venv"
SCRIPT_DIR="$HOME/as-recon"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${Y}[*] Creating virtual environment at $VENV_DIR...${W}"
    python3 -m venv "$VENV_DIR"
fi

# Activate venv and install dependencies
echo -e "${Y}[*] Installing Python dependencies...${W}"
source "$VENV_DIR/bin/activate"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
if [ -f "$REQ_FILE" ]; then
    pip install --upgrade pip
    pip install -r "$REQ_FILE"
else
    echo -e "${Y}[!] requirements.txt not found, skipping dependency install.${W}"
fi
deactivate

# Create wrapper script
WRAPPER="$BIN_DIR/as-recon"
echo -e "${Y}[*] Creating global command at $WRAPPER...${W}"
cat > "$WRAPPER" << EOL
#!/usr/bin/env bash
# AS-RECON wrapper

VENV="$VENV_DIR"
SCRIPT="$SCRIPT_DIR/as-recon.py"

if [ ! -f "\$SCRIPT" ]; then
    echo "Error: \$SCRIPT not found!"
    exit 1
fi

source "\$VENV/bin/activate"
python3 "\$SCRIPT" "\$@"
EOL

chmod +x "$WRAPPER"

# Ensure PATH
SHELL_RC="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "$BIN_DIR" "$SHELL_RC"; then
    echo -e "\n# AS-RECON bin path" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
fi

echo -e "${G}[✓] AS-RECON installed successfully!${W}"
echo -e "${B}[*] Make sure to run 'source $SHELL_RC' or reopen your terminal.${W}"
echo -e "${B}[*] Usage: as-recon example.com${W}"
echo -e "${B}[*] Advanced: as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json${W}"
echo -e "${G}Happy Recon! 🔍${W}"
