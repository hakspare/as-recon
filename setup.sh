#!/bin/bash

echo "[*] Starting Fast Installation for AS-RECON Pro..."

# প্রয়োজনীয় প্যাকেজ চেক এবং ইনস্টল
if command -v python3 &>/dev/null; then
    echo "[✓] Python3 found."
else
    echo "[!] Installing Python3..."
    pkg install python -y || apt install python3 -y
fi

# শুধু প্রয়োজনীয় লাইব্রেরি ইনস্টল (Storage সাশ্রয় করতে)
echo "[*] Installing Lightweight Dependencies..."
pip install requests urllib3 --no-cache-dir

# গ্লোবাল কমান্ড সেটআপ (যাতে যেকোনো জায়গা থেকে 'as-recon' লিখলেই চলে)
cp as-recon.py $PREFIX/bin/as-recon
chmod +x $PREFIX/bin/as-recon

echo "[✓] Installation Complete in < 60 Seconds!"
echo "[*] Usage: as-recon -d google.com"
