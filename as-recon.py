#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string
from random import choices

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def clean_subdomain(sub, domain):
    """গারবেজ ডাটা এবং ডাবল ডোমেইন ফিল্টারিং লজিক"""
    sub = sub.lower().strip().strip('.')
    
    # ১. সার্টিফিকেট স্টার/ওয়াইল্ডকার্ড রিমুভাল
    if sub.startswith("*."): sub = sub[2:]
    
    # ২. ডাবল ডোমেইন বা জাঙ্ক ডাটা ডিটেকশন (যেমন: example.com.target.com)
    # যদি ডোমেইন নামের আগে অন্য কোনো ডট-যুক্ত ডোমেইন থাকে যা ভ্যালিড সাবডোমেইন নয়
    parts = sub.split('.')
    domain_parts = domain.split('.')
    
    # যদি সাবডোমেইনের ভেতরেই মেইন ডোমেইন একাধিকবার থাকে বা ভুল ফরমেটে থাকে
    if sub.count(domain) > 1 or f".{domain}.{domain}" in sub:
        return None

    # ৩. Regex Over-match ফিক্স: শুধু ডোমেইন পর্যন্ত রাখা
    match = re.search(r'([a-z0-9-.]+\.' + re.escape(domain) + r')$', sub)
    if not match: return None
    
    final_sub = match.group(1)
    
    # ৪. অপ্রয়োজনীয় ডট বা ভুল ডোমেইন লিকেজ ফিল্টার
    if final_sub.startswith(domain): return None # target.com যেন না দেখায়
    
    return final_sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            # পাওয়ারফুল Regex যা ডোমেইনের প্যাটার্ন চেনে
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw_subs = re.findall(pattern, r.text)
            
            cleaned = []
            for s in raw_subs:
                c = clean_subdomain(s, domain)
                if c: cleaned.append(c)
            return cleaned
    except: pass
    return []

# [Intelligence Class & Other Functions remain same for speed]
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
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Domain to scan")
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--live", action="store_true", help="Live check")
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=60, help="Threads")
    out_grp = parser.add_argument_group(f'{Y}OUTPUT{W}')
    out_grp.add_argument("-o", "--output", help="Save file")
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Help menu")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    args = parser.parse_args()

    start_time = time.time()
    target = args.domain
    intel = Intelligence(target)
    
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{C}[*] Initializing Intelligence on: {target}{W}")
    intel.setup_wildcard_filter()
    
    print(f"{Y}[*] Hunting Subdomains (Passive-Engine)...{W}")
    raw_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_results.update(res)

    final_list = sorted(list(raw_results))

    if not final_list:
        print(f"{R}[!] No valid data found.{W}")
    else:
        print(f"{G}[+]{W} Total Potential Targets: {B}{len(final_list)}{W}\n")
        if args.live:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                jobs = [executor.submit(check_live_ultimate, s, intel) for s in final_list]
                for j in concurrent.futures.as_completed(jobs):
                    res = j.result()
                    if res: print(res[0])
        else:
            for s in final_list: print(f" {C}»{W} {s}")

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2){W}                     {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_list):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
