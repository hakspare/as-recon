# AS-RECON v19.0

**Amass-Level Subdomain Recon Tool**
█████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
Passive → Hybrid → Graph | Built for Scale

### Features
- 10+ passive sources (crt.sh, AlienVault, BufferOver, Chaos, VirusTotal ইত্যাদি)
- Smart DNS resolver pool + health-based rotation
- Wildcard detection & filtering
- Priority queue + permutation generation
- Graph correlation (NetworkX)
- SQLite checkpoint/resume
- Rate limiting & concurrency control

### Installation

```bash
git clone https://github.com/yourusername/as-recon.git
cd as-recon
chmod +x setup.sh
./setup.sh

এরপর যেকোনো জায়গা থেকে চালাতে পারবেন:
as-recon example.com
Usage
# Basic
as-recon target.com

# Advanced
as-recon target.com --threads 200 --rate 100 --depth 5 --api-keys api_keys.json
API keys ফাইলের উদাহরণ (api_keys.json):
{
  "virustotal": "your_key_here",
  "securitytrails": "your_key_here",
  "chaos": "your_key_here"
}
Output Files
subdomains_target.com.txt → সব subdomain লিস্ট
graph_target.com.graphml → correlation graph
Requirements
Python 3.8+
Poetry (setup.sh দিয়ে অটো ইনস্টল হয়)
License
MIT
Happy recon! 🔍
