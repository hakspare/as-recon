# AS-RECON v20.3  
**Amass-Level Subdomain Reconnaissance Tool (50+ Passive Sources)**
█████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
Passive → Hybrid → Graph | 50+ Sources | 2026 Edition
A powerful, fast, and open-source subdomain enumeration tool designed to achieve parity with Amass, Subfinder, and BBOT — built with 50+ passive intelligence sources, smart resolver rotation, wildcard filtering, aggressive permutation, correlation graph, and checkpoint/resume support.
Features
50+ passive intelligence sources (crt.sh, Chaos, Censys, VirusTotal, SecurityTrails, AlienVault OTX, Sonar Omnisint, AnubisDB, Columbus, ThreatCrowd, CIRCL.lu, and many more)
Intelligent DNS resolver pool with health-based rotation
Wildcard detection & filtering (reduces false positives)
Priority-based queue + aggressive permutation generation
Correlation graph built with NetworkX (export to graphml)
SQLite-based checkpoint/resume (safe for long scans)
Rate limiting & concurrency control
Auto OS detection & dependency installation (Termux, Ubuntu/Debian, Fedora, Arch, macOS)

Quick Installation (1–2 minutes)
git clone https://github.com/YOUR_USERNAME/as-recon.git
cd as-recon
chmod +x setup.sh
./setup.sh

The setup.sh script automatically:
Checks for Python 3.8+

Installs missing system packages (git, jq, curl, etc.)
Installs pipx + Poetry
Clones/updates the repository
Installs project dependencies
Makes as-recon available globally via pipx
Usage
Basic scan
as-recon example.com
Advanced scan
as-recon example.com \
  --threads 300 \
  --rate 150 \
  --depth 6 \
  --api-keys api_keys.json
API Keys File (api_keys.json) — Optional but recommended
Some sources require API keys (Chaos, VirusTotal, Censys, SecurityTrails, etc.).
Example format:
{
  "chaos": "your_chaos_key_here",
  "virustotal": "your_vt_api_key",
  "censys": "your_censys_id:your_censys_secret",
  "securitytrails": "your_st_key",
  "criminalip": "your_criminalip_key"
}
If the file is missing or invalid, the script shows a warning — but free sources continue working.
Output Files
subs_example.com.txt → Sorted list of discovered subdomains
full_example.com.json → Detailed JSON (IPs + timestamp)
graph_example.com.graphml → Network graph (open with Gephi, yEd, etc.)
asrecon_example.com.db → SQLite checkpoint database (for resume)
Troubleshooting
Command not found after install?
→ Close & reopen your terminal
→ Or run:
source \~/.bashrc
# or
source \~/.zshrc
Poetry/pipx issues?
→ Manually run:
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
Development & Contributing
Fork the repository
Create your feature branch: git checkout -b feature/amazing-feature
Commit your changes: git commit -m 'Add amazing feature'
Push to the branch: git push origin feature/amazing-feature
Open a Pull Request
License
MIT License — free to use, modify, and distribute.
Acknowledgments
Inspired by OWASP Amass, ProjectDiscovery Subfinder & Chaos, BBOT
Thanks to all passive source providers
Special thanks to community feedback that made this tool better
Happy hunting! 🔍
