#!/usr/bin/env bash

# =============================================================================
# AS-RECON Commercial-Grade Setup Script v21.0
# Fully automated installer for Linux, Termux, macOS, WSL
# =============================================================================

set -euo pipefail

# ──────────────────────────────
# Colors
# ──────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ──────────────────────────────
# Banner
# ──────────────────────────────
echo -e "${BLUE}"
cat << "EOF"
   █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
  ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
  ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
  ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
  ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝

       AS-RECON v21.0 - 50+ Passive Sources
       Subdomain Recon Engine - Commercial Edition
EOF
echo -e "${NC}"

echo -e "${YELLOW}→ Starting Commercial-Grade Setup...${NC}"

# ──────────────────────────────
# Detect OS
# ──────────────────────────────
OS="$(uname -s)"
echo -e "${BLUE}→ Detected OS: ${OS}${NC}"

# ──────────────────────────────
# Function: Install package
# ──────────────────────────────
install_pkg() {
    pkgname="$1"
    if ! command -v "$pkgname" &>/dev/null; then
        echo -e "${YELLOW}→ Installing ${pkgname}...${NC}"
        if command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y "$pkgname"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y "$pkgname"
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm "$pkgname"
        elif command -v brew &>/dev/null; then
            brew install "$pkgname"
        elif command -v pkg &>/dev/null; then
            pkg install "$pkgname" -y
        else
            echo -e "${RED}✗ Cannot install ${pkgname}. Please install manually.${NC}"
        fi
    else
        echo -e "✓ ${pkgname} already installed"
    fi
}

# ──────────────────────────────
# Check / install dependencies
# ──────────────────────────────
install_pkg python3
install_pkg git
install_pkg curl
install_pkg jq

# ──────────────────────────────
# Check Python version
# ──────────────────────────────
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [[ $PY_MAJOR -lt 3 || ( $PY_MAJOR -eq 3 && $PY_MINOR -lt 8 ) ]]; then
    echo -e "${RED}✗ Python 3.8+ required, found ${PY_VER}${NC}"
    exit 1
fi
echo -e "✓ Python OK: ${PY_VER}"

# ──────────────────────────────
# Install pipx & poetry
# ──────────────────────────────
python3 -m pip install --user --upgrade pip pipx 2>/dev/null || true
python3 -m pipx ensurepath 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

if ! command -v pipx &>/dev/null; then
    echo -e "${RED}✗ pipx not found. Please install manually.${NC}"
    exit 1
fi

pipx install poetry --force 2>/dev/null || pipx upgrade poetry 2>/dev/null
echo -e "✓ pipx & Poetry ready"

# ──────────────────────────────
# Clone / update repo
# ──────────────────────────────
REPO_URL="https://github.com/hakspare/as-recon.git"
REPO_DIR="$HOME/as-recon"

if [ -d "$REPO_DIR/.git" ]; then
    echo -e "${YELLOW}→ Repo exists. Pulling latest...${NC}"
    cd "$REPO_DIR"
    git pull origin main
else
    echo -e "${BLUE}→ Cloning AS-RECON repo...${NC}"
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ──────────────────────────────
# Check entrypoint
# ──────────────────────────────
if [ ! -f "as-recon" ]; then
    echo -e "${RED}✗ Entry script 'as-recon' not found!${NC}"
    echo -e "Make sure the repo contains a Python entrypoint named 'as-recon'."
else
    echo -e "✓ Entry script found: as-recon"
fi

# ──────────────────────────────
# Install Python dependencies
# ──────────────────────────────
if [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}→ Installing Python dependencies via Poetry...${NC}"
    poetry install --no-root --sync
    echo -e "✓ Python dependencies installed"
else
    echo -e "${YELLOW}⚠️ pyproject.toml not found, skipping Poetry install.${NC}"
fi

# ──────────────────────────────
# Global installation
# ──────────────────────────────
if [ -f "as-recon" ]; then
    echo -e "${BLUE}→ Installing AS-RECON globally...${NC}"
    chmod +x as-recon
    cp as-recon "$HOME/.local/bin/"
    echo -e "✓ AS-RECON installed globally as 'as-recon'"
fi

# ──────────────────────────────
# Final instructions
# ──────────────────────────────
echo -e "\n${GREEN}╔════════════════════════════════╗${NC}"
echo -e "${GREEN}║     AS-RECON Setup Completed! ✅   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════╝${NC}\n"

echo -e "Run AS-RECON globally:\n  as-recon example.com"
echo -e "Advanced usage:\n  as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"
echo -e "${YELLOW}If 'as-recon' not found, open a new terminal or run:${NC}"
echo -e "  source ~/.bashrc"
echo -e "  # or"
echo -e "  source ~/.zshrc"
echo -e "${GREEN}Happy Recon! 🔍${NC}"
