#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse
from random import choice

# SSL ওয়ার্নিং ইগনোর করা
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- High-End Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

def get_banner():
    colors = [C, G, Y, M]
    clr = choice(colors)
    return rf"""
{clr}{B}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
{clr}  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
{clr}  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌
{clr}  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
{clr}   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{W}{B}     >> AS-RECON v7.1: Turbo Optimized <<{W}
{G}--------------------------------------------------------
{Y}  Author  : {W}@hakspare (Ajijul Islam Shohan)
{Y}  Engine  : {G}HyperDrive + Fast Validation{W}
{G}--------------------------------------------------------{W}"""

def fetch_source(url, domain):
    try:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        res = requests.get(url, headers={'User-Agent': ua}, timeout=10, verify=False)
        if res.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, res.text)]
    except: pass
    return []

def check_status(subdomain):
    """Turbo Validation: টাইমআউট মাত্র ২ সেকেন্ড"""
    try:
        url = f"http://{subdomain}"
        # লাইভ চেকিংয়ের সময় ২ সেকেন্ডের বেশি অপেক্ষা করবে না
        r = requests.get(url, timeout=2, verify=False, allow_redirects=True)
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        return f"{subdomain} {B}{color}[{sc}]{W}"
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description=f"{G}AS-RECON Ultimate - Fast Recon Framework{W}")
    parser.add_argument("-d", "--domain", help="Target domain", required=True)
    parser.add_argument("-o", "--output", help="Save unique results")
    parser.add_argument("-t", "--threads", help="Parallel threads (default: 50)", type=int, default=50)
    parser.add_argument("--live", help="Check HTTP status (Slower but accurate)", action="store_true")
    
    if len(sys.argv) == 1:
        print(get_banner()); parser.print_help(); sys.exit()

    args = parser.parse_args()
    print(get_banner())
    
    target, threads = args.domain, args.threads
    start_time = time.time()

    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://sonar.omnisint.io/subdomains/{target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://urlscan.io/api/v1/search/?q=domain:{target}",
        f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5",
        f"https://rapiddns.io/subdomain/{target}?full=1"
    ]

    all_subs = set()
    print(f"{C}[*] {W}Hunting subdomains for {B}{target}{W}...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            all_subs.update(f.result())

    results = sorted(list(set([s for s in all_subs if target in s])))

    if not results:
        print(f"{R}[!] No results found.{W}"); sys.exit()

    print(f"{G}[+] Found {len(results)} unique subdomains!{W}\n")

    if args.live:
        print(f"{C}[*] {W}Validating with {Y}{threads}{W} threads (Timeout: 2s)...\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            # map ব্যবহার করা হয়েছে স্পিড অপ্টিমাইজেশনের জন্য
            live_results = list(executor.map(check_status, results))
            for res in live_results:
                if res: print(f" {C}»{W} {res}")
    else:
        for r in results:
            print(f" {C}»{W} {r}")

    print(f"\n{Y}┌──────────────────────────────────────────┐")
    print(f"  {B}TOTAL FOUND  : {G}{len(results)}{W}")
    print(f"  {B}TIME TAKEN   : {C}{round(time.time()-start_time, 2)}s{W}")
    print(f"{Y}└──────────────────────────────────────────┘{W}")

    if args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(results))
        print(f"{M}[!] Saved to: {W}{args.output}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(f"\n{R}[!] Stopped.{W}"); sys.exit()
