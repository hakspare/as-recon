#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string, json, os
from random import choices

# SSL Warnings বন্ধ করা
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- প্রফেশনাল কালার কোড ---
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

def fetch_source(url, domain, verbose=False):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            subs = list(set([s.lower() for s in re.findall(pattern, r.text)]))
            if verbose: print(f"{G}[DEBUG]{W} Found {len(subs)} from {url[:30]}...")
            return subs
    except: pass
    return []

def check_live_ultimate(subdomain, intel):
    try:
        ip = socket.gethostbyname(subdomain)
        if ip in intel.wildcard_ips: return None
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=4, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        if hashlib.md5(r.content).hexdigest() == intel.wildcard_hash: return None
        server = r.headers.get('Server', 'Hidden')[:12]
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        display = f" {C}»{W} {subdomain.ljust(35)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}({server}){W}"
        return (display, subdomain, {"subdomain": subdomain, "status": sc, "ip": ip, "cdn": cdn, "server": server})
    except: return None

def scan_logic(target, args):
    intel = Intelligence(target)
    intel.setup_wildcard_filter()
    
    # Standard Sources (Fast)
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://sonar.omnisint.io/subdomains/{target}"
    ]
    
    # Deep Mode Sources (Slow but thorough)
    if args.deep:
        sources.append(f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey")
        sources.append(f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5")

    raw_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target, args.verbose): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_subs.update(res)

    clean_list = sorted(list(set([s for s in raw_subs if target in s and not s.startswith("*")])))
    final_results = []
    json_data = []

    if clean_list:
        print(f"\n{G}[+]{W} Target: {B}{target}{W} | Found: {B}{len(clean_list)}{W}")
        if args.live:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                jobs = [executor.submit(check_live_ultimate, s, intel) for s in clean_list]
                for j in concurrent.futures.as_completed(jobs):
                    res = j.result()
                    if res:
                        print(res[0])
                        final_results.append(res[1])
                        json_data.append(res[2])
        else:
            for s in clean_list:
                print(f" {C}»{W} {s}")
                final_results.append(s)
                json_data.append({"subdomain": s})
                
    return final_results, json_data

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=LOGO,
        add_help=False
    )
    
    # Custom Help Layout
    h = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    h.add_argument("-d", "--domain", help="Single domain to scan")
    h.add_argument("-l", "--list", help="File containing list of domains")
    
    m = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    m.add_argument("--live", action="store_true", help="Check for live subdomains")
    m.add_argument("--deep", action="store_true", help="Enable Deep Archive scraping (Slow)")
    
    p = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    p.add_argument("-t", "--threads", type=int, default=60, help="Threads for live check (Default: 60)")
    p.add_argument("-v", "--verbose", action="store_true", help="Show debugging info")
    
    o = parser.add_argument_group(f'{Y}OUTPUT{W}')
    o.add_argument("-o", "--output", help="Save results to file")
    o.add_argument("--json", action="store_true", help="Export as JSON")
    
    s = parser.add_argument_group(f'{Y}SYSTEM{W}')
    s.add_argument("--update", action="store_true", help="Update AS-RECON")
    s.add_argument("-h", "--help", action="help", help="Show this help menu")

    args = parser.parse_args()

    if args.update:
        print(f"{Y}[*] Checking for updates...{W}")
        os.system("curl -sL https://raw.githubusercontent.com/hakspare/as-recon/main/setup.sh | bash")
        sys.exit()

    if not args.domain and not args.list:
        print(LOGO)
        parser.print_help()
        sys.exit()

    targets = []
    if args.domain: targets.append(args.domain)
    if args.list:
        with open(args.list, 'r') as f:
            targets.extend([line.strip() for line in f if line.strip()])

    all_found = []
    all_json = []
    start_time = time.time()

    for target in targets:
        f, j = scan_logic(target, args)
        all_found.extend(f)
        all_json.extend(j)

    duration = round(time.time() - start_time, 2)
    
    # Summary Box
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY{W}                                {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(all_found):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

    if args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(all_found))
    if args.json and args.output:
        with open(args.output + ".json", "w") as f:
            json.dump(all_json, f, indent=4)

if __name__ == "__main__":
    main()
