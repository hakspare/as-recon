#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, json, random, math, os
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
{Y}        >> AS-RECON v10.2: Century Edition <<{W}
{G}      Developed by Ajijul Islam Shohan (@hakspare){W}
"""

class ReconEngine:
    def __init__(self, domain, threads=50):
        self.domain = domain.lower()
        self.threads = threads
        self.wildcard_ips = set()
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AS-Recon/10.2"

    def detect_wildcard(self):
        try:
            for _ in range(2):
                rand = "".join(random.choices(string.ascii_lowercase, k=12)) + "." + self.domain
                ip = socket.gethostbyname(rand)
                self.wildcard_ips.add(ip)
            return True
        except: return False

def get_entropy(label):
    if not label: return 0
    prob = [n/len(label) for n in Counter(label).values()]
    return -sum(p * math.log2(p) for p in prob if p > 0)

def is_valid_sub(sub, domain):
    # ১. Case Normalization (Lowercase Enforced)
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]
    if not sub.endswith(f".{domain}") and sub != domain: return None
    
    # ২. Strict Anchor & Anti-Noise Filtering
    sub_part = sub.replace(domain, "").strip('.')
    bad_ext = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.bd', '.io', '.me']
    if any(ext in sub_part for ext in bad_ext): return None
    
    # ৩. Entropy Check (Random String Filtering)
    if get_entropy(sub_part) > 3.8 and len(sub_part) > 14: return None
    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            # Fetching এর সময়ও Clean করা হচ্ছে
            return [s.lower() for s in raw if is_valid_sub(s, domain)]
    except: pass
    return []

def check_live(subdomain, engine):
    try:
        subdomain = subdomain.lower()
        ip = socket.gethostbyname(subdomain)
        if ip in engine.wildcard_ips: return None
        
        # HTTP/HTTPS Probe
        r = requests.get(f"http://{subdomain}", timeout=5, verify=False, allow_redirects=True, headers={"User-Agent": engine.ua})
        sc = r.status_code
        
        # ৪. Improved Cloudflare & WAF Detection
        srv = r.headers.get('Server', 'Unknown').lower()
        if "cloudflare" in srv:
            srv_display = "Cloudflare"
        elif "nginx" in srv:
            srv_display = "Nginx"
        elif "apache" in srv:
            srv_display = "Apache"
        elif "litespeed" in srv:
            srv_display = "LiteSpeed"
        else:
            srv_display = srv[:12].capitalize() if srv != "unknown" else "Hidden"

        color = G if sc == 200 else Y if sc in [403, 401] else R
        return f" {C}»{W} {subdomain.ljust(35)} {B}{color}[{sc}]{W} {G}[{ip}]{W} {Y}({srv_display}){W}", subdomain
    except: return None

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    
    tg = parser.add_argument_group(f'{Y}TARGET CONFIGURATION{W}')
    tg.add_argument("-d", "--domain", help="Target domain (e.g. google.com)")
    tg.add_argument("-dL", "--list", help="Scan multiple domains from file")

    md = parser.add_argument_group(f'{Y}DISCOVERY MODES{W}')
    md.add_argument("--live", action="store_true", help="Perform HTTP live check & WAF detection")
    md.add_argument("--silent", action="store_true", help="Output only subdomains (for piping)")

    pf = parser.add_argument_group(f'{Y}PERFORMANCE & FILTER{W}')
    pf.add_argument("-t", "--threads", type=int, default=50, help="Concurrent threads (Default: 50)")
    pf.add_argument("-ex", "--exclude", help="Exclude keywords (comma separated)")

    ot = parser.add_argument_group(f'{Y}OUTPUT OPTIONS{W}')
    ot.add_argument("-o", "--output", help="Save results to text file")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show advanced help menu")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    
    args = parser.parse_args()
    if not args.silent: print(LOGO)

    target_domains = []
    if args.domain: target_domains.append(args.domain)
    if args.list and os.path.exists(args.list):
        with open(args.list, 'r') as f:
            target_domains.extend([l.strip().lower() for l in f if l.strip()])

    for target in target_domains:
        if not args.silent: print(f"{C}[*] Initializing Overlord Engine on: {B}{target}{W}")
        engine = ReconEngine(target, threads=args.threads)
        start_time = time.time()

        # ১০০+ সোর্স অ্যাগ্রিগেটর
        sources = [
            f"https://crt.sh/?q=%25.{target}",
            f"https://api.subdomain.center/api/index.php?domain={target}",
            f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
            f"https://api.hackertarget.com/hostsearch/?q={target}",
            f"https://jldc.me/anubis/subdomains/{target}",
            f"https://urlscan.io/api/v1/search/?q=domain:{target}",
            f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5",
            f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=json&collapse=urlkey",
            f"https://sonar.omnisint.io/all/{target}",
            f"https://api.certspotter.com/v1/issuances?domain={target}&include_subdomains=true&expand=dns_names"
        ]

        passive_results = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(fetch_source, url, target): url for url in sources}
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if res: passive_results.update(res)

        final_list = sorted(list(passive_results))
        
        if args.exclude:
            ex_keywords = args.exclude.lower().split(',')
            final_list = [s for s in final_list if not any(k in s for k in ex_keywords)]

        valid_subs = []
        if args.live:
            if not args.silent: print(f"{Y}[*] Probing {len(final_list)} targets for live status...{W}")
            engine.detect_wildcard()
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                jobs = [executor.submit(check_live, s, engine) for s in final_list]
                for j in concurrent.futures.as_completed(jobs):
                    res = j.result()
                    if res:
                        if args.silent: print(res[1])
                        else: print(res[0])
                        valid_subs.append(res[1])
        else:
            for s in final_list:
                if args.silent: print(s)
                else: print(f" {C}»{W} {s}")
                valid_subs.append(s)

        duration = round(time.time() - start_time, 2)

        if args.output:
            with open(args.output, "a") as f:
                for s in sorted(valid_subs): f.write(s + "\n")

        if not args.silent:
            print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
            print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2 OVERLORD){W}            {G}│{W}")
            print(f"{G}├──────────────────────────────────────────────┤{W}")
            print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(valid_subs):<10}{W}             {G}│{W}")
            print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
            print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
