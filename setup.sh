
#!/bin/bash

echo "[+] Fast Installing AS-RECON Dependencies..."

# Sudo check and command fix for Termux/Kali
if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Go install logic
if ! command -v go &> /dev/null; then
    echo "[!] Installing Go..."
    pkg install golang -y || $SUDO apt install golang -y
fi

echo "[+] Downloading Subfinder, HTTPX, Gau, Katana..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest &
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest &
go install -v github.com/lc/gau/v2/cmd/gau@latest &
go install -v github.com/projectdiscovery/katana/cmd/katana@latest &

wait

echo "[✓] Fast Setup Finished!"
