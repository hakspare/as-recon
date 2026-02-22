# AS-RECON v20.3

**Amass‑Level Subdomain Reconnaissance Engine**  
Passive → Hybrid → Graph Intelligence | 50+ Sources | 2026 Edition
█████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗ ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║ ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║ ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║ ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║ ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝


![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Termux-orange)

---

## 🌐 Overview

**AS-RECON** is a high‑performance, open‑source subdomain enumeration framework designed for professional security workflows including:

- Penetration Testing  
- Bug Bounty Hunting  
- Attack Surface Mapping  
- Red Team Reconnaissance  

Built to achieve operational parity with industry tools like **Amass, Subfinder, and BBOT**, it integrates **50+ passive intelligence sources**, smart DNS infrastructure, aggressive permutation strategies, and graph correlation analysis.

The engine prioritizes speed, accuracy, and scalability — suitable for both individual researchers and enterprise pipelines.

---

## ✨ Core Features

- 50+ passive intelligence sources  
  *(crt.sh, Chaos, Censys, VirusTotal, SecurityTrails, OTX, Sonar, etc.)*

- Intelligent DNS resolver pool  
  - Health‑based rotation  
  - Failover handling  

- Wildcard detection & filtering  
  - Reduces false positives  

- Priority queue task scheduling  
- Aggressive permutation engine  
- Correlation graph generation (NetworkX)  
- SQLite checkpoint/resume support  
- Rate limiting & concurrency control  
- Auto OS dependency setup  
  - Termux  
  - Ubuntu/Debian  
  - Fedora  
  - Arch  
  - macOS  

---

## ⚡ Quick Installation (1–2 Minutes)

```bash
git clone https://github.com/YOUR_USERNAME/as-recon.git
cd as-recon
chmod +x setup.sh
./setup.sh
What setup.sh does
Validates Python environment
Installs missing system dependencies
Installs pipx + Poetry
Installs project dependencies
Deploys as-recon globally
Prepares runtime environment
🚀 Usage
Basic Scan
Bash
Copy code
as-recon example.com
Advanced Scan
Bash
Copy code
as-recon example.com \
  --threads 300 \
  --rate 150 \
  --depth 6 \
  --api-keys api_keys.json
Option
Description
--threads
Concurrent workers
--rate
Requests per second
--depth
Permutation depth
--api-keys
Enable premium sources
🔑 API Keys (Optional — Recommended)
Create api_keys.json:
JSON
Copy code
{
  "chaos": "your_key",
  "virustotal": "your_key",
  "censys": "id:secret",
  "securitytrails": "key",
  "criminalip": "key"
}
If missing:
Tool continues using free sources
Displays warning message
📁 Output Artifacts
File
Description
subs_domain.txt
Sorted subdomain list
full_domain.json
Detailed scan output
graph_domain.graphml
Network correlation graph
asrecon_domain.db
Resume checkpoint
🛠 Troubleshooting
Command not found
Bash
Copy code
source ~/.bashrc
# or
source ~/.zshrc
pipx / Poetry issues
Bash
Copy code
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
🤝 Contributing
We welcome professional contributions.
1️⃣ Fork the repo
2️⃣ Create feature branch
Bash
Copy code
git checkout -b feature/new-module
3️⃣ Commit changes
4️⃣ Push branch
5️⃣ Submit Pull Request
📜 License
MIT License
Free for personal and commercial use.
🙏 Acknowledgments
Inspired by:
OWASP Amass
ProjectDiscovery Subfinder
Chaos Dataset
BBOT Framework
Gratitude to all passive data providers and community testers.
🔍 Final Note
AS-RECON is engineered for serious reconnaissance operations where performance, scalability, and extensibility matter.
Run:
Bash
Copy code
as-recon --help
to explore full capabilities.
Happy Hunting 🔎
