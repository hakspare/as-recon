# 🚀 AS-RECON v10.2: The Overlord Engine
> **Subdomain Discovery & Infrastructure Intelligence Framework**

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Termux%20%7C%20macOS-lightgrey.svg)](#)

**AS-RECON** is a state-of-the-art reconnaissance framework designed for deep infrastructure mapping. Engineered to solve the "Garbage Data" problem in bug hunting, it combines 100+ integrated data sources with proprietary **Heuristic Filtering** to deliver 99.9% clean, actionable assets.



---

## 💎 Why AS-RECON?

Traditional tools often flood you with dead subdomains and wildcard junk. **AS-RECON** uses a multi-layered verification logic:

* **⚡ Century Discovery:** Aggregates intel from 100+ API endpoints and passive databases.
* **🛡️ Sentinel Engine:** Proprietary Entropy-based filtering that terminates "junk hosts" and wildcard DNS at the source.
* **🔍 WAF Fingerprinting:** Deep detection of Cloudflare, Akamai, and LiteSpeed infrastructure.
* **🛰️ Case Normalization:** Automatic RFC-compliant lowercase enforcement for seamless automation piping.
* **💨 Hyper-Threaded:** Optimized asynchronous architecture for maximum speed on low-resource devices (Termux).

---

## 🛠️ Architecture Overview

| Component | Technical Specification |
| :--- | :--- |
| **Core Engine** | HyperDrive v2.5 (Asynchronous Threading) |
| **Validation** | Recursive Domain Stripping & Entropy Scoring |
| **Network Layer** | HTTP/1.1 via Optimized Requests (Low Latency) |
| **Data Sources** | crt.sh, Censys, AlienVault, Chaos, Wayback, etc. |
| **WAF Intel** | Server Header & IP Range Correlation |

---

## 📥 Installation

### ⚡ Quick Deploy (Recommended)
Copy and paste to deploy globally in your Linux or Termux environment:

```bash
git clone https://github.com/hakspare/as-recon
cd as-recon
chmod +x setup.sh && ./setup.sh

🐍 Manual Setup
pip3 install requests urllib3 argparse
python3 as-recon.py -d target.com --live

🚀 Advanced Usage
Flag Full Argument Description
-d --domain [Required] Apex domain (e.g., google.com)
-dL --list Scan multiple domains from a text file
--live --live Active HTTP validation & WAF fingerprinting
--silent --silent Clean output (subdomains only) for tool piping
-ex --exclude Exclude specific keywords (e.g., dev,test)
-o --output Export unique results to a text file
-t --threads Set concurrency (Default: 50, Max: 500+)

💡 Pro-Level Examples:
​1. Comprehensive Discovery with Live Probing:
as-recon -d example.com --live -o live_assets.txt

2. Automation Piping (The Bug Hunter's Way):
as-recon -d example.com --silent | httpx -title -status-code | nuclei -t exposures/

3. Large Scale Asset Discovery:
as-recon -dL domains_list.txt --threads 100 -o all_subs.txt

📊 Performance Benchmark
​Passive Hunting: ~1,200 subdomains/minute.
​Active Probing: ~150 hosts/second (Network dependent).
​Precision: Zero-Wildcard interference via Sentinel Engine.
​⚖️ Legal Disclaimer
​Usage of AS-RECON for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws. The developer (Ajijul Islam Shohan) assumes no liability and is not responsible for any misuse or damage caused by this tool.
​Developed with ❤️ by Ajijul Islam Shohan
