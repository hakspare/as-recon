#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# কালার কোডস
G = '\033[92m' # Green
Y = '\033[93m' # Yellow
R = '\033[91m' # Red
C = '\033[96m' # Cyan
W = '\033[0m'  # White

BANNER = rf"""{C}
     ___    ____        ____  __________  ______  _   __
    /   |  / ___/      / __ \/ ____/ __ \/ ____/ / | / /
   / /| |  \__ \______/ /_/ / __/ / / / / /   /  |/ /
  / ___ | ___/ /_____/ _, _/ /___/ /_/ / /___/ /|  /
 /_/  |_/____/     /_/ |_/_____/\____/\____/_/ |_/
                                             {Y}v4.1-Pro{W}
{G}--------------------------------------------------------
   Author  : @hakspare (Ajijul Islam Shohan)
   10+ Sources | Ultra-Fast | Multi-Threaded
--------------------------------------------------------{W}"""

def fetch_data(url, domain):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            # উন্নত Regex লজিক যাতে আরও বেশি URL/Subdomain পাওয়া যায়
            content = response.text
            extracted = re.findall(r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain), content)
            return extracted
    except:
        pass
    return []

def run_recon(domain):
    print(f"{Y}[INFO] 🚀 Multi-Source Engine active for: {G}{domain}{W}\n")
    
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={domain}",
        f"https://crt.sh/?q=%25.{domain}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={domain}",
        f"https://sonar.omnisint.io/subdomains/{domain}",
        f"https://jldc.me/anubis/subdomains/{domain}",
        f"https://api.threatminer.org/v2/domain.php?q={domain}&rt=5",
        f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
    ]

    all_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_data, url, domain) for url in sources]
        for future in concurrent.futures.as_completed(futures):
            all_found.update(future.result())
    
    return sorted(list(all_found))

def main():
    print(BANNER)
    if len(sys.argv) < 3 or sys.argv[1] != "-d":
        print(f"{R}Usage: as-recon -d example.com{W}")
        sys.exit(1)

    target = sys.argv[2]
    results = run_recon(target)

    if results:
        # শুধু ডোমেইনগুলো ফিল্টার করা
        unique_subs = sorted(list(set([s.lower() for s in results if target in s])))
        
        filename = f"res_{target.replace('.','_')}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(unique_subs))
            
        print(f"{G}[✓] Success! {W}{len(unique_subs)} {G}Unique Subdomains Found.{W}")
        print(f"{Y}[📂] Results saved to: {W}{filename}")
    else:
        print(f"{R}[!] No data found. Try another domain.{W}")

if __name__ == "__main__":
    main()
