#!/usr/bin/env bash
# =============================================================================
# AS-RECON Commercial Installer v22.0
# Fully automated, cross-platform, zero user confusion
# =============================================================================

set -euo pipefail

# ----------------------------
# Colors
# ----------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}"
cat << "EOF"
   █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
  ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
  ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
  ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
  ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝

        AS-RECON v20.3 - 55+ Passive Sources
        Subdomain Recon Engine - Commercial Edition
EOF
echo -e "${NC}"

echo -e "${YELLOW}[*] Starting Installer...${NC}"

# ----------------------------
# Detect OS
# ----------------------------
OS="$(uname -s)"
echo -e "${GREEN}[*] Detected OS: $OS${NC}"

# ----------------------------
# Check Python 3.8+
# ----------------------------
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✗] Python3 not found. Install Python 3.8+ first.${NC}"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)

if [[ $PY_MAJOR -lt 3 || ( $PY_MAJOR -eq 3 && $PY_MINOR -lt 8 ) ]]; then
    echo -e "${RED}[✗] Python 3.8+ required. Found $PY_VER${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Python OK: $PY_VER${NC}"

# ----------------------------
# Check/Install dependencies: git, curl, jq
# ----------------------------
for cmd in git curl jq; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${YELLOW}[*] Installing $cmd...${NC}"
        if [[ "$OS" == "Linux" ]]; then
            if command -v apt &> /dev/null; then sudo apt install -y $cmd
            elif command -v dnf &> /dev/null; then sudo dnf install -y $cmd
            elif command -v pacman &> /dev/null; then sudo pacman -S --noconfirm $cmd
            fi
        elif [[ "$OS" == "Darwin" ]]; then
            brew install $cmd
        fi
    else
        echo -e "${GREEN}[✓] $cmd OK${NC}"
    fi
done

# ----------------------------
# Ensure ~/.local/bin in PATH
# ----------------------------
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
    SHELLRC="$HOME/.bashrc"
    [[ -f "$HOME/.zshrc" ]] && SHELLRC="$HOME/.zshrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELLRC"
    echo -e "${GREEN}[✓] Added ~/.local/bin to PATH in $SHELLRC${NC}"
fi

# ----------------------------
# Install pipx + poetry
# ----------------------------
echo -e "${BLUE}[*] Installing/updating pipx & poetry...${NC}"
python3 -m pip install --user --upgrade pip pipx >/dev/null 2>&1 || true
python3 -m pipx ensurepath >/dev/null 2>&1 || true
pipx install --force poetry >/dev/null 2>&1 || pipx upgrade poetry >/dev/null 2>&1
echo -e "${GREEN}[✓] pipx & poetry ready${NC}"

# ----------------------------
# Clone/Update Repo
# ----------------------------
REPO_DIR="$HOME/as-recon"
REPO_URL="https://github.com/hakspare/as-recon.git"

if [ -d "$REPO_DIR/.git" ]; then
    echo -e "${YELLOW}[*] Repo exists. Pulling latest...${NC}"
    cd "$REPO_DIR"
    git pull origin main
else
    echo -e "${BLUE}[*] Cloning AS-RECON...${NC}"
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ----------------------------
# Create Virtual Environment
# ----------------------------
VENV_DIR="$HOME/.as-recon-venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}[*] Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# ----------------------------
# Install Dependencies
# ----------------------------
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}[!] requirements.txt not found, skipping dependency install.${NC}"
fi

# ----------------------------
# Install global command
# ----------------------------
CMD_PATH="$HOME/.local/bin/as-recon"
cp "$REPO_DIR/as-recon.py" "$CMD_PATH"
chmod +x "$CMD_PATH"

echo -e "${GREEN}[✓] AS-RECON installed successfully!${NC}"
echo -e "${BLUE}[*] Ensure ~/.local/bin is in PATH or run 'source ~/.bashrc'/'source ~/.zshrc'${NC}"

# ----------------------------
# Final Message
# ----------------------------
echo -e "${BOLD}${GREEN}╔══════════════════════════════════╗"
echo -e "║       AS-RECON Setup Completed ✅     ║"
echo -e "╚══════════════════════════════════╝${NC}"
echo -e "Run AS-RECON globally:"
echo -e "  as-recon example.com"
echo -e "Advanced:"
echo -e "  as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"
echo -e "Happy Recon! 🔍"
