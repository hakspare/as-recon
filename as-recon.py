#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, os
from random import choice

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Pro Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36"
]

def get_banner():
    colors = [C, G, Y, M]
    clr = choice(colors)
    return rf"""
{clr}{B}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
{clr}  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
{clr}  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌
{clr}  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
{clr}   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{W}{B}     >> Ultimate Reconnaissance Framework v5.1 <<{W}
{G}--------------------------------------------------------
{Y}  Author  : {W}@hakspare (Ajijul Islam Shohan)
{Y}  Status  : {G}Stable & Multi-Threaded{W}
{G}--------------------------------------------------------{W}"""

def fetch_source(url, domain):
    try:
        headers = {'User-Agent': choice(USER_AGENTS)}
        res = requests.get(url, headers=headers, timeout=12, verify=False)
        if res.status_code == 200:
            # ডোমেইন এক্সট্রাকশনের জন্য উন্নত Regex
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            found = re.findall(pattern, res.text)
            return [s.lower() for s in found]
    except: pass
    return []

def run_recon(target):
    print(f"{C}[*] {W}Hunting subdomains for: {B}{G}{target}{W}\n")
    
    # পাওয়ারফুল ১২টি সোর্স
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
        f"https://columbus.elmasy.com/api/lookup/{target}",
        f"https://riddler.io/search/export/domain/{target}",
        f"https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{target}/*&output=json"
    ]

    all_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            results = f.result()
            if results:
                all_found.update(results)

    # ফাইনাল ক্লিনিং: শুধু ইউনিক এবং টার্গেট ডোমেইন ওয়ালা রেজাল্ট
    final = sorted(list(set([s for s in all_found if target in s])))
    return final

def main():
    if "-h" in sys.argv or "--help" in sys.argv or len(sys.argv) < 3:
        print(get_banner())
        print(f"{B}Usage:{W} as-recon -d target.com [-o output.txt]")
        sys.exit()

    print(get_banner())
    target = sys.argv[sys.argv.index("-d") + 1]
    output = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else None
    
    start = time.time()
    results = run_recon(target)
    
    if results:
        for r in results:
            print(f" {C}»{W} {r}")
        
        print(f"\n{Y}┌──────────────────────────────────────────┐")
        print(f"  {B}TOTAL UNIQUE FOUND : {G}{len(results)}{W}")
        print(f"  {B}SCAN TIME          : {C}{round(time.time()-start, 2)}s{W}")
        print(f"{Y}└──────────────────────────────────────────┘{W}")
        
        if output:
            with open(output, "w") as f:
                f.write("\n".join(results))
            print(f"{M}[!] File saved as: {W}{output}")
    else:
        print(f"{R}[!] Error: No data retrieved. Check internet connection.{W}")

if __name__ == "__main__":
    main()
