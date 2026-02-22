#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AS-RECON Commercial-Grade Installer${NC}"

# ----------------------------
# OS & Python Check
# ----------------------------
OS_TYPE="$(uname -s)"
echo -e "${BLUE}Detected OS: ${OS_TYPE}${NC}"

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python3 not found!${NC}"
    exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}✗ Python 3.8+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python OK: ${PY_MAJOR}.${PY_MINOR}${NC}"

# ----------------------------
# System Packages
# ----------------------------
for pkg in git curl jq; do
    if ! command -v $pkg &>/dev/null; then
        echo -e "${YELLOW}Installing $pkg...${NC}"
        if command -v pkg &>/dev/null; then pkg install -y $pkg
        elif command -v apt &>/dev/null; then sudo apt install -y $pkg
        elif command -v dnf &>/dev/null; then sudo dnf install -y $pkg
        elif command -v pacman &>/dev/null; then sudo pacman -S --noconfirm $pkg
        elif command -v brew &>/dev/null; then brew install $pkg
        else echo -e "${RED}Install $pkg manually${NC}"; fi
    else
        echo -e "${GREEN}✓ $pkg OK${NC}"
    fi
done

# ----------------------------
# Clone/Update Repo
# ----------------------------
REPO_DIR="$HOME/as-recon"
REPO_URL="https://github.com/hakspare/as-recon.git"

if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}→ Repo exists, updating...${NC}"
    cd "$REPO_DIR"
    git pull origin main || echo -e "${YELLOW}Git pull failed, continuing...${NC}"
else
    echo -e "${BLUE}→ Cloning repo...${NC}"
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ----------------------------
# Make script globally executable
# ----------------------------
INSTALL_BIN="$HOME/.local/bin"
mkdir -p "$INSTALL_BIN"

cp as-recon "$INSTALL_BIN/"
chmod +x "$INSTALL_BIN/as-recon"

if [[ ":$PATH:" != *":$INSTALL_BIN:"* ]]; then
    echo "export PATH=\"$INSTALL_BIN:\$PATH\"" >> ~/.bashrc
    echo "export PATH=\"$INSTALL_BIN:\$PATH\"" >> ~/.zshrc 2>/dev/null || true
    export PATH="$INSTALL_BIN:$PATH"
fi

echo -e "${GREEN}✓ AS-RECON installed globally!${NC}"
echo -e "Run it anywhere: ${YELLOW}as-recon example.com${NC}"
echo -e "${GREEN}🎯 Happy Recon! 🔍${NC}"
