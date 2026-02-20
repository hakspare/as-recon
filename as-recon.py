#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string
from random import choices

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

class Intelligence:
    def __init__(self, domain):
        self.domain = domain
        self.wildcard_hash = None
        self.wildcard_len = None
        self.ua = "Mozilla/5.0 (X11; Linux x86_64) AS-Recon/10.1"

    def get_hash(self, content):
        return hashlib.md5(content).hexdigest()

    def setup_wildcard_filter(self):
        rand = "".join(choices(string.ascii_lowercase, k=12)) + "." + self.domain
        try:
            r = requests.get(f"http://{rand}", timeout=4, verify=False, headers={"User-Agent": self.ua})
            self.wildcard_hash = self.get_hash(r.content)
            self.wildcard_len = len(r.content)
            return True
        except: return False

def fetch_source(url, domain):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            # উন্নত রেজেক্স যা সব ধরণের সাবডোমেইন খুঁজে পাবে
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, r.text)]
    except: pass
    return []

def check_live_ultimate(subdomain, intel):
    try:
        ip = socket.gethostbyname(subdomain)
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=4, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        
        curr_hash = intel.get_hash(r.content)
        if curr_hash == intel.wildcard_hash or len(r.content) == intel.wildcard_len:
            return None

        server = r.headers.get('Server', 'Hidden')[:12]
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        
        res = f" {C}»{W} {subdomain.ljust(30)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}({server}){W}"
        return (res, subdomain)
    except: return None

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v10.1 Overlord")
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    target = args.domain
    intel = Intelligence(target)
    
    print(f"\n{B}{M}[*] Profiling Target: {target}{W}")
    if intel.setup_wildcard_filter():
        print(f"{R}[!] Wildcard Detected. Hash-filtering enabled.{W}")

    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey"
    ]

    raw_subs = set()
    print(f"{C}[*] Extracting Intelligence...{W}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            raw_subs.update(f.result())

    clean_list = sorted(list(set([s for s in raw_subs if target in s])))
    
    if not clean_list:
        print(f"{R}[!] No data found! Check your internet or domain.{W}")
        return

    print(f"{G}[+]{W} Collected {len(clean_list)} unique targets.\n")

    final_subs = []
    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            jobs = [executor.submit(check_live_ultimate, s, intel) for s in clean_list]
            for j in concurrent.futures.as_completed(jobs):
                res = j.result()
                if res:
                    print(res[0])
                    final_subs.append(res[1])
    else:
        for s in clean_list:
            print(f" {C}»{W} {s}")
            final_subs.append(s)

    if args.output and final_subs:
        with open(args.output, "w") as f:
            f.write("\n".join(final_subs))
        print(f"\n{G}[✓] Saved to: {args.output}{W}")

if __name__ == "__main__":
    main()
