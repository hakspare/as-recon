#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, json
from random import choice

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Pro Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
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
{W}{B}     >> HyperDrive Reconnaissance Engine v6.2 <<{W}
{G}--------------------------------------------------------
{Y}  Author  : {W}@hakspare (Ajijul Islam Shohan)
{Y}  Sources : {G}18+ Passive Databases & CDX Records{W}
{G}--------------------------------------------------------{W}"""

def fetch_source(url, domain):
    try:
        headers = {'User-Agent': choice(USER_AGENTS)}
        res = requests.get(url, headers=headers, timeout=15, verify=False)
        if res.status_code == 200:
            # উন্নত ডোমেইন ম্যাচিং প্যাটার্ন
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, res.text)]
    except: pass
    return []

def run_recon(target, threads):
    print(f"{C}[*] {W}Engaging {B}18+ High-Performance Sources{W} for: {G}{target}{W}\n")
    
    # ১৮টি ডাইনামিক সোর্স যা সব বড় টুল ব্যবহার করে
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://sonar.omnisint.io/subdomains/{target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://urlscan.io/api/v1/search/?q=domain:{target}",
        f"https://columbus.elmasy.com/api/lookup/{target}",
        f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5",
        f"https://rapiddns.io/subdomain/{target}?full=1",
        f"https://certspotter.com/api/v0/certs?domain={target}",
        f"https://api.facebook.com/method/links.getStats?urls={target}&format=json",
        f"https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{target}/*&output=json",
        f"https://dns.bufferover.run/dns?q=.{target}",
        f"https://www.google.com/search?q=site:*.{target}&num=100",
        f"https://shodan.io/host/search?query=hostname:*.{target}",
        f"https://securitytrails.com/list/apex_domain/{target}"
    ]

    all_found = set()
    # ৩০টি থ্রেড একসাথে রকেট স্পিডে কাজ করবে
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            results = f.result()
            if results: all_found.update(results)

    return sorted(list(set([s for s in all_found if target in s])))

def main():
    parser = argparse.ArgumentParser(description=f"{G}AS-RECON HyperDrive - Next-Gen Recon Tool{W}")
    parser.add_argument("-d", "--domain", help="Target domain (google.com)", required=False)
    parser.add_argument("-o", "--output", help="Output file name")
    parser.add_argument("-t", "--threads", help="Parallel threads (default: 30)", type=int, default=30)
    parser.add_argument("-v", "--version", action="version", version=f"{Y}AS-RECON v6.2-HyperDrive{W}")
    
    if len(sys.argv) == 1:
        print(get_banner())
        parser.print_help()
        sys.exit()

    args = parser.parse_args()
    if not args.domain:
        print(get_banner()); print(f"{R}[!] Error: Domain required.{W}"); sys.exit()

    print(get_banner())
    start_time = time.time()
    results = run_recon(args.domain, args.threads)
    
    if results:
        for r in results: print(f" {G}»{W} {r}")
        
        print(f"\n{Y}┌──────────────────────────────────────────┐")
        print(f"  {B}TOTAL UNIQUE FOUND : {G}{len(results)}{W}")
        print(f"  {B}DIVERSITY INDEX    : {C}18+ Sources{W}")
        print(f"  {B}EXECUTION TIME     : {C}{round(time.time()-start_time, 2)}s{W}")
        print(f"{Y}└──────────────────────────────────────────┘{W}")
        
        if args.output:
            with open(args.output, "w") as f: f.write("\n".join(results))
            print(f"{M}[!] Secured in: {W}{args.output}")
    else:
        print(f"{R}[!] No data found. Try increasing threads or checking your connection.{W}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print(f"\n{R}[!] Stopped.{W}"); sys.exit()
