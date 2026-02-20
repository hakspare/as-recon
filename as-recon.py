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
{W}{B}     >> AS-RECON v7.0: The Hunter Edition <<{W}
{G}--------------------------------------------------------
{Y}  Author  : {W}@hakspare (Ajijul Islam Shohan)
{Y}  Engine  : {G}HyperDrive (18+ Sources) + Live Check{W}
{G}--------------------------------------------------------{W}"""

def fetch_source(url, domain):
    try:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        res = requests.get(url, headers={'User-Agent': ua}, timeout=15, verify=False)
        if res.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, res.text)]
    except: pass
    return []

def check_status(subdomain):
    """চেক করবে সাবডোমেইনটি কি ২০০ ওকে দিচ্ছে নাকি অন্য কিছু"""
    try:
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=5, verify=False, allow_redirects=True)
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        return f"{subdomain} {B}{color}[{sc}]{W}"
    except:
        return None

def main():
    # কাস্টম হেল্প মেনু
    parser = argparse.ArgumentParser(description=f"{G}AS-RECON Ultimate - Pro Reconnaissance Framework{W}", usage="as-recon [options]")
    
    group = parser.add_argument_group(f"{Y}TARGET OPTIONS{W}")
    group.add_argument("-d", "--domain", help="Target domain (e.g., google.com)", required=True)
    
    mode = parser.add_argument_group(f"{Y}MODE OPTIONS{W}")
    mode.add_argument("--live", help="Validate found subdomains (Check HTTP status)", action="store_true")
    
    config = parser.add_argument_group(f"{Y}CONFIG OPTIONS{W}")
    config.add_argument("-o", "--output", help="File to save results")
    config.add_argument("-t", "--threads", help="Parallel threads (default: 30)", type=int, default=30)
    config.add_argument("-v", "--version", action="version", version=f"{Y}AS-RECON v7.0{W}")

    if len(sys.argv) == 1:
        print(get_banner())
        parser.print_help()
        sys.exit()

    args = parser.parse_args()
    print(get_banner())
    
    target = args.domain
    threads = args.threads
    start_time = time.time()

    # আপনার ১৮+ পাওয়ারফুল সোর্স লিস্ট (এখানে কিছু ডাইনামিক সোর্স আছে)
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://sonar.omnisint.io/subdomains/{target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://urlscan.io/api/v1/search/?q=domain:{target}",
        f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5"
    ]

    all_subs = set()
    print(f"{C}[*] {W}Hunting for subdomains... (This may take a few seconds)")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            all_subs.update(f.result())

    results = sorted(list(set([s for s in all_subs if target in s])))

    if not results:
        print(f"{R}[!] No subdomains found for {target}.{W}")
        sys.exit()

    print(f"{G}[+] Found {len(results)} subdomains!{W}\n")

    final_results = []
    if args.live:
        print(f"{C}[*] {W}Starting live validation engine with {threads} threads...\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            check_futures = {executor.submit(check_status, s): s for s in results}
            for f in concurrent.futures.as_completed(check_futures):
                res = f.result()
                if res:
                    print(f" {C}»{W} {res}")
                    final_results.append(res)
    else:
        for r in results:
            print(f" {C}»{W} {r}")
            final_results.append(r)

    # Summary Box
    print(f"\n{Y}┌──────────────────────────────────────────┐")
    print(f"  {B}UNIQUE FOUND : {G}{len(results)}{W}")
    print(f"  {B}MODE         : {C}{'Hunter (Live)' if args.live else 'Passive Only'}{W}")
    print(f"  {B}SCAN TIME    : {C}{round(time.time()-start_time, 2)}s{W}")
    print(f"{Y}└──────────────────────────────────────────┘{W}")

    if args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(results))
        print(f"{M}[!] Results secured in: {W}{args.output}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{R}[!] Aborted by user.{W}")
        sys.exit()
