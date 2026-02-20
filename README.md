# 🚀 AS-RECON Pro v4.0
**The Ultimate High-Speed Reconnaissance Framework for Security Professionals**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android-green)](https://github.com/hakspare/as-recon)

**AS-RECON Pro** is a high-performance, multi-threaded reconnaissance tool designed for bug hunters and penetration testers. It automates the process of subdomain discovery and endpoint fetching while simultaneously verifying HTTP status codes at lightning speed.



---

## 🌟 Key Features
* **Massive Discovery:** Combines `subfinder` and `gau` to fetch thousands of unique endpoints.
* **High-Speed Engine:** Powered by Python's `ThreadPoolExecutor` for concurrent status checking.
* **Smart Filtering:** Automatically removes duplicate URLs and filters junk data.
* **Universal Support:** Optimized for both PC (x86_64) and Mobile (ARM64/Termux) architectures.
* **Color-coded Status:** Visual indicators for HTTP responses (200 OK, 403 Forbidden, 404 Not Found, etc.).
* **Automation Ready:** Supports silent mode (`-s`) for integration into custom bug bounty pipelines.

---

## 🐧 Supported Distributions
AS-RECON Pro is tested and fully compatible with:
* **Kali Linux** (Primary)
* **Parrot Security OS**
* **Ubuntu / Debian**
* **Arch Linux / BlackArch**
* **Android (Termux / NetHunter)**
* **Fedora / CentOS**

---

## 🛠️ Installation Guide

### 1. For Linux (Kali, Ubuntu, Arch, etc.)
Open your terminal and execute the following commands:
```bash
# Clone the repository
git clone https://github.com/hakspare/as-recon 

# Enter the directory
cd as-recon

# Grant execution permission and run the setup
chmod +x setup.sh

sudo ./setup.sh

2. For Android (Termux)
​Ensure you have Termux installed from F-Droid, then run:

pkg update && pkg upgrade -y
git clone https://github.com/hakspare/as-recon
cd as-recon
chmod +x setup.sh
./setup.sh



🚀 Usage & Examples
​Basic Recon
​Fetch URLs and check their live status:  as-recon -d example.com


High-Speed Scanning (Multi-threading)
​Use 100 threads for massive domains and save results to a file:
as-recon -d example.com -t 100 -o live_targets.txt


Silent Mode (For Pipelining)
​Display only the found URLs without the banner (useful for grep or nuclei input):
as-recon -d example.com -s


⚙️ Command Line Options
Option Long Flag Description
-d --domain Target Domain (e.g., google.com)
-t --threads Number of concurrent threads (Default: 30)
-o --output Save the validated results to a specific file
-s --silent Enable silent mode (No banner, only output)
-h --help Show the help menu


🤝 Contribution & Support
​If you find this tool useful, feel free to Star ⭐ the repository and follow me for more security tools.
​Bug Reports: Please open an issue if you encounter any problems.
Pull Requests: Contributions are always welcome

​👤 Author
​Ajijul Islam Shohan
​GitHub: @hakspare
​Twitter/X: @AzizulI18

​⚠️ Disclaimer
​This tool is developed for educational and ethical security testing purposes only. The author is not responsible for any misuse or damage caused by this tool. Always obtain permission before testing any target.

