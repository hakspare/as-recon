#!/bin/bash

# =========================================
# AS-RECON Commercial Installer v21.1
# =========================================

# Colors
GREEN='\033[92m'
YELLOW='\033[93m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${GREEN}${BOLD}[*] AS-RECON v21.1 Installer Starting...${RESET}"

# Detect OS
OS="$(uname -s)"
echo -e "${YELLOW}[*] Detected OS: $OS${RESET}"

# Ensure Python 3
if ! command -v python3 &>/dev/null; then
    echo "[✗] Python3 not found. Please install Python3."
    exit 1
fi
PYTHON_VERSION=$(python3 -V | awk '{print $2}')
echo -e "${GREEN}[✓] Python OK: $PYTHON_VERSION${RESET}"

# Ensure git
if ! command -v git &>/dev/null; then
    echo "[✗] git not found. Please install git."
    exit 1
fi
echo -e "${GREEN}[✓] git OK${RESET}"

# Ensure curl
if ! command -v curl &>/dev/null; then
    echo "[✗] curl not found. Please install curl."
    exit 1
fi
echo -e "${GREEN}[✓] curl OK${RESET}"

# Ensure jq
if ! command -v jq &>/dev/null; then
    echo "[✗] jq not found. Please install jq."
    exit 1
fi
echo -e "${GREEN}[✓] jq OK${RESET}"

# Set bin directory
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:$PATH"

# Create virtual environment
VENV="$HOME/.as-recon-venv"
if [ ! -d "$VENV" ]; then
    echo -e "${YELLOW}[*] Creating virtual environment at $VENV...${RESET}"
    python3 -m venv "$VENV"
fi

# Activate venv
source "$VENV/bin/activate"

# Upgrade pip inside venv
pip install --upgrade pip &>/dev/null

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}[*] Installing Python dependencies...${RESET}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}[!] requirements.txt not found. Skipping dependency install.${RESET}"
fi

# Clone/update repo
if [ ! -d "$HOME/as-recon" ]; then
    echo -e "${YELLOW}[*] Cloning AS-RECON repository...${RESET}"
    git clone https://github.com/hakspare/as-recon.git "$HOME/as-recon"
else
    echo -e "${YELLOW}[*] Repository exists. Pulling latest changes...${RESET}"
    cd "$HOME/as-recon" || exit
    git pull
fi

# Create global wrapper command
WRAPPER="$BIN_DIR/as-recon"
cat > "$WRAPPER" << 'EOL'
#!/usr/bin/env bash
VENV="$HOME/.as-recon-venv"
SCRIPT="$HOME/as-recon/as-recon.py"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: $SCRIPT not found!"
    exit 1
fi

# Activate venv
source "$VENV/bin/activate"

# Help support
if [[ "$1" == "-h" || "$1" == "--help" || $# -eq 0 ]]; then
    python3 "$SCRIPT" --help
else
    python3 "$SCRIPT" "$@"
fi
EOL

chmod +x "$WRAPPER"
echo -e "${GREEN}[✓] Global command 'as-recon' created at $WRAPPER${RESET}"

echo -e "${YELLOW}[*] Ensure $BIN_DIR is in your PATH. Run 'source ~/.bashrc' or 'source ~/.zshrc' if needed.${RESET}"

echo -e "${GREEN}${BOLD}[*] AS-RECON Setup Completed! ✅${RESET}"
echo -e "Usage: as-recon example.com"
echo -e "Advanced: as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"
echo -e "Happy Recon! 🔍"
