#!/bin/bash
echo -e "\e[1;36m[+] Installing Advanced Recon Tools...\e[0m"

sudo apt update
sudo apt install golang git python3 -y

go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/tomnomnom/assetfinder@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/tomnomnom/gf@latest

# বাইনারি কপি
sudo cp ~/go/bin/* /usr/bin/

# কমান্ড সেটআপ
chmod +x as-recon.py
sudo cp as-recon.py /usr/bin/as-recon

echo -e "\e[1;32m[✓] Advanced Setup Finished! Now your tool has Subfinder & HTTPX.\e[0m"
