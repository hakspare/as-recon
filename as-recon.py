#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string, random, math
from collections import Counter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- UI & Colors ---
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
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AS-Recon/10.2"

    def detect_wildcard(self):
        try:
            for _ in range(2):
                rand = "".join(random.choices(string.ascii_lowercase, k=12)) + "." + self.domain
                ip = socket.gethostbyname(rand)
                self.wildcard_ips.add(ip)
            return len(self.wildcard_ips) > 0
        except: return False

def get_entropy(label):
    if not label: return 0
    prob = [n/len(label) for n in Counter(label).values()]
    return -sum(p * math.log2(p) for p in prob if p > 0)

def is_valid_sub(sub, domain):
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]
    if not sub.endswith(f".{domain}") and sub != domain: return None
    
    sub_part = sub.replace(domain, "").strip('.')
    bad_extensions = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.bd']
    if any(ext in sub_part for ext in bad_extensions): return None
    if get_entropy(sub_part) > 3.7 and len(sub_part) > 12: return None
    return sub

def check_live(subdomain, intel):
    try:
        ip = socket.gethostbyname(subdomain)
        if ip in intel.wildcard_ips: return None
        r = requests.get(f"http://{subdomain}", timeout=4, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        server = r.headers.get('Server', 'Hidden')[:12]
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        display = f" {C}»{W} {subdomain.ljust(30)} {B}{color}[{sc}]{W} {G}[{ip}]{W} {Y}({server}){W}"
        return display, subdomain
    except: return None

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            return [s for s in raw if is_valid_sub(s, domain)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Domain target (e.g. google.com)")
    
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--live", action="store_true", help="Perform HTTP live check & service detection")
    
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=50, help="Number of concurrent threads (Default: 50)")
    
    out_grp = parser.add_argument_group(f'{Y}OUTPUT{W}')
    out_grp.add_argument("-o", "--output", help="Save results to a text file")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show this professional help menu")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    args = parser.parse_args()

    start_time = time.time()
    target = args.domain
    intel = Intelligence(target)
    
    print(f"{C}[*] Initializing Intelligence & Wildcard Check...{W}")
    intel.detect_wildcard()
    
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{Y}[*] Hunting Subdomains (Passive-Engine)...{W}")
    passive_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: passive_results.update(res)

    final_list = sorted(list(passive_results))
    duration = round(time.time() - start_time, 2)

    print(f"{G}[+]{W} Unique Cleaned Targets: {B}{len(final_list)}{W}\n")
    
    live_found = []
    if args.live:
        print(f"{M}[*] Starting Live Verification with {args.threads} threads...{W}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            jobs = [executor.submit(check_live, s, intel) for s in final_list]
            for j in concurrent.futures.as_completed(jobs):
                res = j.result()
                if res:
                    print(res[0])
                    live_found.append(res[1])
    else:
        for s in final_list:
            print(f" {C}»{W} {s}")
            live_found.append(s)

    # Save to output
    if args.output:
        with open(args.output, "w") as f:
            for s in live_found: f.write(s + "\n")
        print(f"\n{G}[✓] Results saved to: {args.output}{W}")

    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2 PRO){W}                 {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_list):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
