#!/usr/bin/env bash

# =============================================================================
# AS-RECON Setup Script - v20.3 (Auto OS Detect + Dependencies)
# দ্রুত, নিরাপদ ও সব OS-এ কাজ করার জন্য
# =============================================================================

set -euo pipefail

# Colors
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
echo -e "${NC}"

echo -e "\n${YELLOW}Setup শুরু হচ্ছে...${NC}\n"

# ────────────────────────────────────────────────
# 0. Auto detect OS
# ────────────────────────────────────────────────
OS_TYPE=""
if [ "$(uname)" == "Darwin" ]; then
    OS_TYPE="macOS"
elif [ -f "/etc/os-release" ]; then
    . /etc/os-release
    OS_TYPE=$ID
else
    OS_TYPE="unknown"
fi
echo -e "${BLUE}→ Detected OS: ${OS_TYPE}${NC}"

# ────────────────────────────────────────────────
# 1. Install common dependencies: git, python3, jq, curl
# ────────────────────────────────────────────────
install_pkg() {
    PKG_NAME=$1
    if command -v pkg &> /dev/null; then
        pkg install "$PKG_NAME" -y
    elif command -v apt &> /dev/null; then
        sudo apt update && sudo apt install "$PKG_NAME" -y
    elif command -v dnf &> /dev/null; then
        sudo dnf install "$PKG_NAME" -y
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm "$PKG_NAME"
    elif command -v brew &> /dev/null; then
        brew install "$PKG_NAME"
    else
        echo -e "${YELLOW}⚠️ Cannot auto install ${PKG_NAME}, please install manually.${NC}"
    fi
}

for dep in git python3 jq curl; do
    if ! command -v $dep &> /dev/null; then
        echo -e "${BLUE}→ Installing ${dep}...${NC}"
        install_pkg $dep
    else
        echo -e "${GREEN}✓ ${dep} already installed${NC}"
    fi
done

# ────────────────────────────────────────────────
# 2. Python 3.8+ check
# ────────────────────────────────────────────────
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])' 2>/dev/null || echo 0)
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])' 2>/dev/null || echo 0)
PY_VERSION="${PY_MAJOR}.${PY_MINOR}"

if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}✗ Python 3.8+ দরকার। বর্তমান: ${PY_VERSION}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python OK (${PY_VERSION})${NC}"

# ────────────────────────────────────────────────
# 3. pipx + poetry install
# ────────────────────────────────────────────────
python3 -m pip install --user --upgrade pip pipx 2>/dev/null || true
python3 -m pipx ensurepath 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

if ! command -v pipx &> /dev/null; then
    echo -e "${RED}pipx ইনস্টল ব্যর্থ।${NC}"
    exit 1
fi

pipx install poetry --force 2>/dev/null || pipx upgrade poetry 2>/dev/null

# ────────────────────────────────────────────────
# 4. Clone/update repo
# ────────────────────────────────────────────────
REPO_DIR="as-recon"
REPO_URL="https://github.com/YOUR_USERNAME/as-recon.git"

if [ -d "$REPO_DIR/.git" ]; then
    echo -e "${YELLOW}→ Updating existing repo...${NC}"
    cd "$REPO_DIR"
    git pull origin main || git reset --hard origin/main
else
    echo -e "${BLUE}→ Cloning repo...${NC}"
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ────────────────────────────────────────────────
# 5. Install project dependencies
# ────────────────────────────────────────────────
poetry install --no-root --sync

# ────────────────────────────────────────────────
# 6. Global install
# ────────────────────────────────────────────────
pipx install --force .

# ────────────────────────────────────────────────
# 7. API key check (optional)
# ────────────────────────────────────────────────
API_KEYS_FILE="api_keys.json"
if [ -f "$API_KEYS_FILE" ]; then
    if command -v jq &> /dev/null && jq . "$API_KEYS_FILE" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ API keys file valid JSON${NC}"
    else
        echo -e "${YELLOW}⚠️ API keys invalid or jq missing${NC}"
    fi
else
    echo -e "${YELLOW}Note: API keys file not found${NC}"
fi

# ────────────────────────────────────────────────
# 8. Success message
# ────────────────────────────────────────────────
echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      SETUP SUCCESSFULLY COMPLETED!     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}\n"
echo -e "Run: ${YELLOW}as-recon example.com${NC}"
echo -e "Run with options: ${YELLOW}as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json${NC}"
