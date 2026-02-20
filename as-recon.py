#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib
from random import choices
import string

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Pro Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

class Intelligence:
    def __init__(self, domain):
        self.domain = domain
        self.wildcard_hash = None
        self.wildcard_len = None
        self.ua = "Mozilla/5.0 (X11; Linux x86_64) AS-Recon/10.0"

    def get_hash(self, content):
        return hashlib.md5(content).hexdigest()

    def setup_wildcard_filter(self):
        """ভুয়া ডোমেইনের ফিঙ্গারপ্রিন্ট তৈরি করা"""
        rand = "".join(choices(string.ascii_lowercase, k=12)) + "." + self.domain
        try:
            r = requests.get(f"http://{rand}", timeout=4, verify=False, headers={"User-Agent": self.ua})
            self.wildcard_hash = self.get_hash(r.content)
            self.wildcard_len = len(r.content)
            return True
        except: return False

    def get_asn(self, ip):
        """বেসিক আইপি টু এএসএন লজিক (Offline fallback)"""
        try:
            # এটি এপিআই ছাড়াও বেসিক আইপি রেঞ্জ দেখে বুঝতে পারে
            if ip.startswith(("104.", "172.", "188.")): return "Cloudflare"
            return socket.gethostbyaddr(ip)[0] if ip else "Unknown"
        except: return "N/A"

def check_live_ultimate(subdomain, intel, target):
    try:
        ip = socket.gethostbyname(subdomain)
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=3, verify=False, allow_redirects=True, headers={"User-Agent": intel.ua})
        
        # ১. Wildcard Hash Filtering (The Killer Feature)
        curr_hash = intel.get_hash(r.content)
        if curr_hash == intel.wildcard_hash or len(r.content) == intel.wildcard_len:
            return None # False Positive Terminated

        # ২. CDN & Server Detection
        server = r.headers.get('Server', 'Unknown')
        cdn = "CF" if "cloudflare" in server.lower() or "cf-ray" in r.headers else "Direct"
        
        # ৩. ASN/Org Intelligence
        org = intel.get_asn(ip)

        sc = r.status_code
        color = G if sc == 200 else Y if sc in [403, 401] else R
        
        # ফরম্যাটেড আউটপুট
        res = (f" {C}»{W} {subdomain.ljust(30)} {B}{color}[{sc}]{W} {M}({cdn}){W} {G}[{ip}]{W} {Y}{org[:20]}{W}")
        return (res, subdomain)
    except: return None

# ... (fetch_source function remains same as previous version)

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v10.0 Overlord")
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-t", "--threads", type=int, default=60)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    intel = Intelligence(args.domain)
    print(f"\n{B}{M}[*] Profiling Target Intelligence...{W}")
    if intel.setup_wildcard_filter():
        print(f"{R}[!] Wildcard Detected. Hash-based filtering enabled.{W}")

    # (Source fetching logic - same as v9.2)
    # ... 
    
    # [দ্রুততা নিশ্চিত করতে সোর্স ফেচিং পার্ট এখানে থাকবে]
    sources = [
        f"https://crt.sh/?q=%25.{args.domain}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={args.domain}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{args.domain}/passive_dns"
    ]
    
    all_raw = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(requests.get, s, timeout=10) for s in sources]
        for f in concurrent.futures.as_completed(futures):
            try:
                # উন্নত রেজেক্স যা সাব-সাবডোমেইন ক্যাচ করে
                pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(args.domain)
                all_raw.update(re.findall(pattern, f.result().text))
            except: pass

    valid_list = []
    print(f"{G}[+]{W} Raw Intel: {len(all_raw)} | Analyzing Live Infrastructure...\n")

    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            jobs = [executor.submit(check_live_ultimate, s, intel, args.domain) for s in all_raw]
            for j in concurrent.futures.as_completed(jobs):
                out = j.result()
                if out:
                    print(out[0])
                    valid_list.append(out[1])

    if args.output and valid_list:
        with open(args.output, "w") as f: f.write("\n".join(valid_list))

if __name__ == "__main__":
    main()
