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

# -------------------------
# Use pipx for isolation
# -------------------------
echo -e "${YELLOW}[*] Installing/updating pipx...${NC}"
python3 -m pip install --user --upgrade pip pipx >/dev/null 2>&1 || true
python3 -m pipx ensurepath >/dev/null 2>&1 || true
export PATH="$HOME/.local/bin:$PATH"

if ! command -v pipx >/dev/null 2>&1; then
    echo -e "${RED}[✗] pipx not found. Please install manually.${NC}"
    exit 1
fi

# -------------------------
# Install dependencies in venv via pipx
# -------------------------
echo -e "${YELLOW}[*] Installing AS-RECON with pipx (virtual environment)...${NC}"
pipx install . --force || {
    echo -e "${RED}[✗] pipx install failed. Run manually: pipx install .${NC}"
    exit 1
}

# -------------------------
# PATH instructions
# -------------------------
echo -e "${GREEN}[✓] AS-RECON installed successfully!${NC}"
echo -e "${YELLOW}[*] Make sure ~/.local/bin is in your PATH.${NC}"
echo -e "Run: source ~/.bashrc or source ~/.zshrc if command 'as-recon' is not found"

echo -e "\nUsage example:"
echo -e "  as-recon example.com"
echo -e "Advanced usage:"
echo -e "  as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"
