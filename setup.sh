#!/usr/bin/env bash

# =============================================================================
# AS-RECON v20.3 Setup Script - Commercial-Grade, Cross-Platform
# Developed by Hakspare (@hakspare)
# Supports: Termux, Linux (Debian/Ubuntu/Fedora/Arch), macOS, WSL
# =============================================================================

set -euo pipefail

# ----------------------------
# Colors
# ----------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
   █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
  ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
  ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
  ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
  ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
       AS-RECON v20.3 - 50+ Passive Sources
       Subdomain Recon Engine - 2026 Edition
EOF
echo -e "${NC}\n"

echo -e "${YELLOW}→ Starting Commercial-Grade Setup...${NC}"

# ----------------------------
# Detect OS
# ----------------------------
OS_TYPE="$(uname -s)"
echo -e "${BLUE}Detected OS: ${OS_TYPE}${NC}"

# ----------------------------
# Check Python 3.8+
# ----------------------------
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}✗ Python 3.8+ required. Detected ${PY_MAJOR}.${PY_MINOR}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python ${PY_MAJOR}.${PY_MINOR} OK${NC}"

# ----------------------------
# Install system packages
# ----------------------------
install_pkg() {
    PKG="$1"
    if ! command -v "$PKG" &>/dev/null; then
        echo -e "${YELLOW}→ Installing ${PKG}...${NC}"
        if command -v pkg &>/dev/null; then
            pkg install -y "$PKG"
        elif command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y "$PKG"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y "$PKG"
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm "$PKG"
        elif command -v brew &>/dev/null; then
            brew install "$PKG"
        else
            echo -e "${RED}✗ Could not install ${PKG}. Please install manually.${NC}"
        fi
    else
        echo -e "${GREEN}✓ ${PKG} already installed${NC}"
    fi
}

install_pkg git
install_pkg curl
install_pkg jq

# ----------------------------
# Ensure ~/.local/bin in PATH
# ----------------------------
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ PATH updated${NC}"
fi

# ----------------------------
# Install pipx
# ----------------------------
if ! command -v pipx &>/dev/null; then
    echo -e "${YELLOW}→ Installing pipx...${NC}"
    python3 -m pip install --user --upgrade pip pipx
    python3 -m pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi
echo -e "${GREEN}✓ pipx ready${NC}"

# ----------------------------
# Install Poetry
# ----------------------------
pipx install poetry --force 2>/dev/null || pipx upgrade poetry 2>/dev/null
echo -e "${GREEN}✓ Poetry ready${NC}"

# ----------------------------
# Clone / Update Repo
# ----------------------------
REPO_DIR="as-recon"
REPO_URL="https://github.com/hakspare/as-recon.git"

if [ -d "$REPO_DIR" ] && [ -d "$REPO_DIR/.git" ]; then
    echo -e "${YELLOW}→ Repo exists. Pulling latest changes...${NC}"
    cd "$REPO_DIR"
    git pull origin main || echo -e "${YELLOW}Git pull failed. Continuing...${NC}"
else
    echo -e "${BLUE}→ Cloning AS-RECON repo...${NC}"
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ----------------------------
# Install dependencies via Poetry
# ----------------------------
echo -e "${BLUE}→ Installing Python dependencies...${NC}"
poetry install --no-root --sync || {
    echo -e "${RED}Poetry install failed. Run 'poetry install' manually.${NC}"
    exit 1
}

# ----------------------------
# Global install AS-RECON
# ----------------------------
echo -e "${BLUE}→ Installing AS-RECON globally via pipx...${NC}"
pipx install . --force || {
    echo -e "${RED}pipx install failed. Run manually: pipx install .${NC}"
    exit 1
}

# ----------------------------
# API keys check
# ----------------------------
API_FILE="api_keys.json"
if [ -f "$API_FILE" ]; then
    if command -v jq &>/dev/null && ! jq . "$API_FILE" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ ${API_FILE} invalid JSON. Please fix it.${NC}"
    else
        echo -e "${GREEN}✓ API keys file detected and valid${NC}"
    fi
else
    echo -e "${YELLOW}Note: ${API_FILE} not found. Some sources may not work without keys.${NC}"
fi

# ----------------------------
# Final Message
# ----------------------------
echo -e "\n${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     AS-RECON Setup Completed! ✅     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}\n"

echo -e "Run AS-RECON globally:"
echo -e "  ${YELLOW}as-recon example.com${NC}"
echo -e "Advanced usage:"
echo -e "  ${YELLOW}as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json${NC}"
echo -e "${YELLOW}If 'as-recon' not found, open a new terminal or run 'source ~/.bashrc' / 'source ~/.zshrc'${NC}"
echo -e "${GREEN}🎯 Happy Recon! 🔍${NC}"
