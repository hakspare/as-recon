#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string
from random import choices

# SSL Warnings বন্ধ করা
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কালার এবং লোগো ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{C}{B}
   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄  ▐█▐▐▌
  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{Y}        >> AS-RECON v10.2: Overlord Engine <<{W}
{G}      Developed by Ajijul Islam Shohan (@hakspare){W}
"""

class Intelligence:
    def __init__(self, domain):
        self.domain = domain
        self.wildcard_ips = set()
        self.wildcard_hash = None
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AS-Recon/10.2"

    def setup_wildcard_filter(self):
        for _ in range(2):
            rand = "".join(choices(string.ascii_lowercase, k=12)) + "." + self.domain
            try:
                ip = socket.gethostbyname(rand)
                self.wildcard_ips.add(ip)
                r = requests.get(f"http://{rand}", timeout=3, verify=False, headers={"User-Agent": self.ua})
                self.wildcard_hash = hashlib.md5(r.content).hexdigest()
            except: pass
        return len(self.wildcard_ips) > 0

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, r.text)]
    except: pass
    return []

def check_live_ultimate(subdomain, intel):
    try:
        ip = socket.gethostbyname(subdomain)
        if ip in intel.wildcard_ips: return None
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=3, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        if hashlib.md5(r.content).hexdigest() == intel.wildcard_hash: return None
        server = r.headers.get('Server', 'Hidden')[:12]
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        display = f" {C}»{W} {subdomain.ljust(35)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}({server}){W}"
        return (display, subdomain)
    except: return None

def main():
    # --- অ্যাডভান্সড হেল্প মেনু লজিক ---
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=LOGO,
        add_help=False # ডিফল্ট হেল্প বন্ধ করে কাস্টম গ্রুপ করা হয়েছে
    )
    
    # হেল্প মেনু গ্রুপিং
    target = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target.add_argument("-d", "--domain", help="Target domain to scan (e.g. google.com)")
    
    mode = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode.add_argument("--live", action="store_true", help="Check if subdomains are alive (Status, CDN, IP)")
    
    perf = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf.add_argument("-t", "--threads", type=int, default=60, help="Number of concurrent threads (Default: 60)")
    
    out = parser.add_argument_group(f'{Y}OUTPUT OPTIONS{W}')
    out.add_argument("-o", "--output", help="Save the results to a text file")
    
    sys_opt = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_opt.add_argument("-h", "--help", action="help", help="Show this advanced help menu and exit")

    args = parser.parse_args()

    # ডোমেইন না দিলে হেল্প মেনু দেখাবে
    if not args.domain:
        print(LOGO)
        parser.print_help()
        sys.exit()

    start_time = time.time()
    target_domain = args.domain
    intel = Intelligence(target_domain)
    
    sources = [
        f"https://crt.sh/?q=%25.{target_domain}",
        f"https://api.subdomain.center/api/index.php?domain={target_domain}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target_domain}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target_domain}",
        f"https://jldc.me/anubis/subdomains/{target_domain}",
        f"https://sonar.omnisint.io/subdomains/{target_domain}",
        f"https://api.threatminer.org/v2/domain.php?q={target_domain}&rt=5"
    ]

    print(f"{B}{C}[*] Initializing Intelligence on: {target_domain}{W}")
    intel.setup_wildcard_filter()
    
    print(f"{Y}[*] Hunting Subdomains from 50+ Sources (Passive-Engine)...{W}")
    raw_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target_domain): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_subs.update(res)

    clean_list = sorted(list(set([s for s in raw_subs if target_domain in s and not s.startswith("*")])))
    final_results = []

    if not clean_list:
        print(f"{R}[!] No discovery data found.{W}")
    else:
        print(f"{G}[+]{W} Total Potential Targets: {B}{len(clean_list)}{W}\n")
        if args.live:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                jobs = [executor.submit(check_live_ultimate, s, intel) for s in clean_list]
                for j in concurrent.futures.as_completed(jobs):
                    res = j.result()
                    if res:
                        print(res[0])
                        final_results.append(res[1])
        else:
            for s in clean_list:
                print(f" {C}»{W} {s}")
                final_results.append(s)

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2){W}                     {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_results):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    if args.output:
        print(f"{G}│{W}  {C}Saved To      :{W} {B}{args.output:<20}{W}   {G}│{W}")
        with open(args.output, "w") as f:
            f.write("\n".join(final_results))
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
