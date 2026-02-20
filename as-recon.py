#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

BANNER = rf"""
{C}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
{C}  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
{C}  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌
{C}  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
{C}   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{M}  >> {W}{B}Professional Reconnaissance Engine {M}<<{W}
"""

def fetch_data(url, domain):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return re.findall(r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain), response.text)
    except: pass
    return []

def run_recon(domain):
    print(f"{C}[*] Scanning {B}{domain}{W} across multiple sources...")
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={domain}",
        f"https://crt.sh/?q=%25.{domain}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={domain}",
        f"https://sonar.omnisint.io/subdomains/{domain}",
        f"https://jldc.me/anubis/subdomains/{domain}"
    ]
    all_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_data, url, domain) for url in sources]
        for future in concurrent.futures.as_completed(futures):
            all_found.update(future.result())
    return sorted(list(set([s.lower() for s in all_found if domain in s])))

def main():
    print(BANNER)
    args = sys.argv
    if "-d" not in args:
        print(f"{R}Usage: as-recon -d target.com [-o output.txt]{W}")
        sys.exit(1)

    target = args[args.index("-d") + 1]
    output_file = args[args.index("-o") + 1] if "-o" in args else None
    
    start_time = time.time()
    results = run_recon(target)
    
    if results:
        print(f"\n{G}[+] Found {len(results)} Subdomains:{W}\n")
        for sub in results:
            print(f" {C}»{W} {sub}")
        
        if output_file:
            with open(output_file, "w") as f:
                f.write("\n".join(results))
            print(f"\n{Y}[📂] Results saved to: {W}{output_file}")
        
        print(f"\n{G}[✓] Scan Complete in {round(time.time()-start_time, 2)}s{W}")
    else:
        print(f"\n{R}[!] No results found.{W}")

if __name__ == "__main__":
    main()
