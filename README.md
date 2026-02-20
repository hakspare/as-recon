​🚀 AS-RECON v10.2 (Overlord Edition)
​Advanced Subdomain Discovery & Infrastructure Intelligence Framework
​AS-RECON is a next-generation subdomain discovery framework engineered for speed, accuracy, and deep infrastructure mapping. By leveraging 18+ high-authority passive data sources and its proprietary Hash-based Sentinel Engine, it eliminates the bottleneck of traditional reconnaissance by terminating False Positives (Garbage Hosts) at the source.
​💎 Core Architecture & Features
​Hyper-Threaded Discovery: Built on a ThreadPoolExecutor architecture allowing massive parallelization (50 to 500+ threads).
​God-Eye Filtering: Uses MD5 content hashing and response entropy to detect and filter out Wildcard DNS and shared hosting junk.
​Infrastructure Intelligence: Automatically fingerprints Cloudflare (CF) protection, identifies Direct IPs, and extracts Server Headers.
​Cross-Platform Compatibility: Optimized for Linux (Kali, Parrot), Android (Termux), and macOS.
​System-Wide Integration: Deploys as a global system command for seamless workflow integration.

​🛠️ Technical Specifications
Component Detail
Engine HyperDrive v2.5 (Asynchronous Threading)
Concurrency Customizable Parallel Threads
Data Sources crt.sh, AlienVault OTX, Wayback Machine, SubdomainCenter, etc.
Validation MD5 Content Hashing & Recursive Domain Stripping
Network Layer HTTP/1.1 via Requests (Optimized for low-latency)

📥 Installation & Deployment
​Standard Installation (Linux & Termux)
​Copy and paste the following commands to deploy the framework globally:
# Clone the repository
git clone https://github.com/hakspare/as-recon

# Enter the directory
cd as-recon

# Run the global deployment script
chmod +x setup.sh
./setup.sh

Manual Installation
​If you prefer to run the script without system-wide integration:
pip install requests urllib3 argparse
python3 as-recon.py -d target.com --live

🚀 Usage & CLI Arguments
​AS-RECON follows the POSIX standard for CLI arguments:
Argument Description
-d, --domain [Required] The target apex domain (e.g., example.com)
-o, --output [Optional] Exports unique live subdomains to a text file
-t, --threads [Optional] Defines concurrency level (Default: 50)
--live [Flag] Enables the HTTP Validation Engine to check for active hosts
-h, --help Displays the advanced help menu

Example Command:  as-recon -d example.com --live -o results.txt


📊 Performance Metrics
​Passive Scan Speed: ~500-800 subdomains/second.
​Validation Speed: ~50-100 hosts/second (Hardware dependent).
​Success Rate: 99.9% unique subdomain isolation via Sentinel filtering.
​⚠️ Legal Disclaimer
​Notice: This tool is strictly for educational and ethical security testing purposes only. The developer (Ajijul Islam Shohan) is not responsible for any misuse, damage, or illegal activities caused by this tool. Usage of AS-RECON for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state, and federal laws.
​Developed by Ajijul Islam Shohan (@hakspare)
