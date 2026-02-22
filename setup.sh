#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${GREEN}[*] AS-RECON v21.0 Commercial Installer Starting...${NC}"

# Detect OS
OS="$(uname -s)"
echo -e "${YELLOW}[*] Detected OS: $OS${NC}"

# Check Python 3.8+
PY=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}[✗] Python 3.8+ required. Found $PY${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Python OK: $PY${NC}"

# Dependencies
echo -e "${YELLOW}[*] Installing Python dependencies...${NC}"
pip install --user -r requirements.txt >/dev/null

# Determine global bin path
BIN_PATH="$HOME/.local/bin"
mkdir -p "$BIN_PATH"

# Make executable
chmod +x as-recon
cp as-recon "$BIN_PATH/as-recon"

# Add to PATH if needed
if ! echo "$PATH" | grep -q "$BIN_PATH"; then
    SHELLRC="$HOME/.bashrc"
    if [[ -n "$ZSH_VERSION" ]]; then SHELLRC="$HOME/.zshrc"; fi
    echo "export PATH=\"$BIN_PATH:\$PATH\"" >> "$SHELLRC"
    echo -e "${YELLOW}[!] Added $BIN_PATH to PATH. Please 'source $SHELLRC' or reopen terminal.${NC}"
fi

echo -e "${GREEN}[✓] AS-RECON installed successfully!"
echo -e "Run: as-recon -d example.com"
