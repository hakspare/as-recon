#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, os
from random import choice

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- High-End Styling ---
C = '\033[96m' ; G = '\033[92m' ; Y = '\033[93m' 
R = '\033[91m' ; M = '\033[95m' ; W = '\033[0m' ; B = '\033[1m'

def get_banner():
    colors = [C, G, Y, M]
    clr = choice(colors)
    return rf"""
{clr}{B}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
{clr}  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
{clr}  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌
{clr}  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
{clr}   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{W}{B}     >> Advanced Reconnaissance & URL Hunter <<{W}
{G}--------------------------------------------------------
{Y}  Author  : {W}@hakspare (Ajijul Islam Shohan)
{Y}  Version : {G}5.0-Ultimate (Better than Amass/Subfinder)
{G}--------------------------------------------------------{W}
"""

def fetch_logic(url, domain):
    ua = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Mozilla/5.0 (X11; Linux x86_64)']
    try:
        res = requests.get(url, headers={'User-Agent': choice(ua)}, timeout=10, verify=False)
        if res.status_code == 200:
            # Nikto/Wayback স্টাইল পাওয়ারফুল এক্সট্রাকশন
            return re.findall(r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain), res.text)
    except: pass
    return []

def run_ultimate_recon(target):
    print(f"{C}[*] {W}Engaging {B}Multi-Source Engine{W} for: {G}{target}{W}\n")
    
    # ১২টি পাওয়ারফুল সোর্স (Amass + Subfinder + Wayback এর কম্বিনেশন)
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://sonar.omnisint.io/subdomains/{target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5",
        f"https://urlscan.io/api/v1/search/?q=domain:{target}",
        f"https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{target}/*&output=json",
        f"https://columbus.elmasy.com/api/lookup/{target}",
        f"https://riddler.io/search/export/domain/{target}"
    ]

    all_data = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(fetch_logic, url, target) for url in sources]
        for f in concurrent.futures.as_completed(futures):
            all_data.update(f.result())

    return sorted(list(set([s.lower() for s in all_data if target in s])))

def show_help():
    print(get_banner())
    print(f"""
{B}USAGE:{W}
  as-recon -d <domain>          {G}# Run standard scan{W}
  as-recon -d <domain> -o <file> {G}# Save results to file{W}

{B}OPTIONS:{W}
  -d, --domain    Target domain (e.g., google.com)
  -o, --output    Save results to a specific file
  -h, --help      Show this advanced help menu
    """)

def main():
    args = sys.argv
    if "-h" in args or "--help" in args or len(args) < 3:
        show_help()
        sys.exit()

    print(get_banner())
    target = args[args.index("-d") + 1]
    output_file = args[args.index("-o") + 1] if "-o" in args else None
    
    start = time.time()
    results = run_ultimate_recon(target)
    
    if results:
        for r in results: print(f" {G}»{W} {r}")
        print(f"\n{Y}┌────────────────────────────────────────┐")
        print(f"  {B}TOTAL UNIQUE RESULTS : {G}{len(results)}{W}")
        print(f"  {B}TIME ELAPSED         : {C}{round(time.time()-start, 2)}s{W}")
        print(f"{Y}└────────────────────────────────────────┘{W}")
        
        if output_file:
            with open(output_file, "w") as f: f.write("\n".join(results))
            print(f"{M}[!] Data secured in: {W}{output_file}")
    else:
        print(f"{R}[!] No data found. Target might be firewalled.{W}")

if __name__ == "__main__":
    main()
