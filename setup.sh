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

# Check Python 3.8+
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
PY_MAJOR=$(echo $PY_VER | cut -d. -f1)
PY_MINOR=$(echo $PY_VER | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ) ]]; then
    echo -e "${RED}[✗] Python 3.8+ required, found $PY_VER${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Python OK: $PY_VER${NC}"

# Create virtual environment inside repo
VENV_DIR="$HOME/.as-recon-venv"
echo -e "${YELLOW}[*] Creating virtual environment at $VENV_DIR...${NC}"
python3 -m venv "$VENV_DIR"

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip inside venv
pip install --upgrade pip --quiet

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}[*] Installing Python dependencies...${NC}"
    pip install -r requirements.txt --quiet
else
    echo -e "${YELLOW}[!] requirements.txt not found, skipping dependencies.${NC}"
fi

# Set global command
SCRIPT="as-recon.py"
TARGET_BIN="$HOME/.local/bin/as-recon"
mkdir -p "$(dirname "$TARGET_BIN")"
echo -e "${YELLOW}[*] Creating global command at $TARGET_BIN...${NC}"

# Wrapper script to always use venv
cat > "$TARGET_BIN" <<EOL
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
python "$PWD/$SCRIPT" "\$@"
EOL

chmod +x "$TARGET_BIN"

# Update PATH for current shell session
export PATH="$HOME/.local/bin:$PATH"

echo -e "${GREEN}[✓] AS-RECON installed successfully!${NC}"
echo -e "${YELLOW}[*] Ensure $HOME/.local/bin is in your PATH.${NC}"
echo -e "Run: source ~/.bashrc or source ~/.zshrc if 'as-recon' is not found"

echo -e "\nUsage:"
echo -e "  as-recon example.com"
echo -e "Advanced:"
echo -e "  as-recon example.com --threads 300 --rate 150 --depth 6 --api-keys api_keys.json"

deactivate
