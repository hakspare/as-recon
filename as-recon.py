#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string
from random import choices

# SSL এরর মেসেজ হাইড করার জন্য
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কালার এবং স্টাইলিং ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

# --- প্রফেশনাল ASCII লোগো ---
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
        """ভুয়া সাবডোমেইন ধরার জন্য ওয়াইল্ডকার্ড ডিটেকশন"""
        for _ in range(3):
            rand = "".join(choices(string.ascii_lowercase, k=15)) + "." + self.domain
            try:
                ip = socket.gethostbyname(rand)
                self.wildcard_ips.add(ip)
                r = requests.get(f"http://{rand}", timeout=5, verify=False, headers={"User-Agent": self.ua})
                self.wildcard_hash = hashlib.md5(r.content).hexdigest()
            except: pass
        return len(self.wildcard_ips) > 0

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, r.text)]
    except: pass
    return []

def check_live_ultimate(subdomain, intel):
    try:
        # DNS আইপি চেক
        ip = socket.gethostbyname(subdomain)
        if ip in intel.wildcard_ips: return None
        if not subdomain.endswith(intel.domain): return None

        # HTTP প্রোপিং
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=4, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        
        # কন্টেন্ট হ্যাশ চেক
        if hashlib.md5(r.content).hexdigest() == intel.wildcard_hash: return None

        server = r.headers.get('Server', 'Hidden')[:12]
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        
        display = f" {C}»{W} {subdomain.ljust(35)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}({server}){W}"
        return (display, subdomain)
    except: return None

def main():
    start_time = time.time() # সময় গণনা শুরু
    print(LOGO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    target = args.domain
    intel = Intelligence(target)
    
    print(f"{B}{C}[*] Initializing Intelligence on: {target}{W}")
    if intel.setup_wildcard_filter():
        print(f"{R}[!] Wildcard Detected. Sentinel Filtering Enabled.{W}")

    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey"
    ]

    raw_subs = set()
    print(f"{Y}[*] Hunting Subdomains from 18+ Sources...{W}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            raw_subs.update(f.result())

    clean_list = sorted(list(set([s for s in raw_subs if target in s])))
    
    final_results = []
    if not clean_list:
        print(f"{R}[!] Discovery phase failed to find data.{W}")
    else:
        print(f"{G}[+]{W} Total Unique Candidates: {B}{len(clean_list)}{W}\n")
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

    # --- সামারি বক্স জেনারেটর (ফাইনাল ফিক্স) ---
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY{W}                             {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_results):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    if args.output:
        print(f"{G}│{W}  {C}Saved To      :{W} {B}{args.output:<20}{W}   {G}│{W}")
        with open(args.output, "w") as f:
            f.write("\n".join(sorted(list(set(final_results)))))
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
