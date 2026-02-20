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
        self.ua = "Mozilla/5.0 (X11; Linux x86_64) AS-Recon/10.2"

    def get_hash(self, content):
        return hashlib.md5(content).hexdigest()

    def setup_wildcard_filter(self):
        rand = "".join(choices(string.ascii_lowercase, k=15)) + "." + self.domain
        try:
            r = requests.get(f"http://{rand}", timeout=5, verify=False, headers={"User-Agent": self.ua}, allow_redirects=True)
            self.wildcard_hash = self.get_hash(r.content)
            self.wildcard_len = len(r.content)
            return True
        except: return False

def check_live_ultimate(subdomain, intel):
    try:
        # DNS Resolution
        ip = socket.gethostbyname(subdomain)
        
        # HTTP Probe
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=4, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        
        # Wildcard Content Check
        curr_hash = intel.get_hash(r.content)
        if curr_hash == intel.wildcard_hash or len(r.content) == intel.wildcard_len:
            return None

        # Server/CDN Intel
        server = r.headers.get('Server', 'Hidden')[:12]
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        
        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        
        # Format terminal output
        display = f" {C}»{W} {subdomain.ljust(30)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}({server}){W}"
        return (display, subdomain)
    except: return None

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, r.text)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v10.2")
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    intel = Intelligence(args.domain)
    print(f"\n{B}{M}[*] Target Intelligence: {args.domain}{W}")
    
    if intel.setup_wildcard_filter():
        print(f"{R}[!] Wildcard Detected. Active Filter Enabled.{W}")

    sources = [
        f"https://crt.sh/?q=%25.{args.domain}",
        f"https://api.subdomain.center/api/index.php?domain={args.domain}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{args.domain}/passive_dns",
        f"https://web.archive.org/cdx/search/cdx?url=*.{args.domain}/*&output=txt&fl=original&collapse=urlkey"
    ]

    raw_subs = set()
    print(f"{C}[*] Hunting Subdomains...{W}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, args.domain): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            raw_subs.update(f.result())

    clean_list = sorted(list(set([s for s in raw_subs if args.domain in s])))
    if not clean_list:
        print(f"{R}[!] No subdomains found.{W}"); return

    print(f"{G}[+]{W} Collected {len(clean_list)} unique candidates.\n")

    final_results = []
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

    # Final File Writing (After the loop)
    if args.output and final_results:
        # ইউনিক ডোমেইন নিশ্চিত করা
        unique_final = sorted(list(set(final_results)))
        with open(args.output, "w") as f:
            for item in unique_final:
                f.write(f"{item}\n")
        print(f"\n{G}[✓] Success! {len(unique_final)} lines saved to: {B}{args.output}{W}")

if __name__ == "__main__":
    main()
