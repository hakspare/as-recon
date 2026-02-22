#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${GREEN}[*] AS-RECON v21.0 Installer Starting...${NC}"

# Detect OS
OS="$(uname -s)"
echo -e "${YELLOW}[*] Detected OS: $OS${NC}"

# Python check
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}[✗] Python 3.8+ required. Found $PY_MAJOR.$PY_MINOR${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Python OK: $PY_MAJOR.$PY_MINOR${NC}"

# Install dependencies (user-local, PEP 668 safe)
echo -e "${YELLOW}[*] Installing Python dependencies locally...${NC}"
python3 -m pip install --user -r requirements.txt --upgrade

# Set global command
SCRIPT="as-recon.py"
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}[✗] Entry script $SCRIPT not found!${NC}"
    exit 1
fi

TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"
cp "$SCRIPT" "$TARGET_DIR/as-recon"
chmod +x "$TARGET_DIR/as-recon"

# Update PATH for current shell session
export PATH="$TARGET_DIR:$PATH"

echo -e "${GREEN}[✓] AS-RECON installed successfully!${NC}"
echo -e "${YELLOW}[*] Make sure $TARGET_DIR is in your PATH.${NC}"
echo -e "Run: source ~/.bashrc or source ~/.zshrc if 'as-recon' is not found"

echo -e "\nUsage example:"
echo -e "  as-recon example.com"
echo -e "Advanced usage:"
echo -e "  as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"
