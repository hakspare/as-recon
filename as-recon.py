#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, string
from random import choices

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

def get_wildcard_ip(domain):
    try:
        random_sub = ''.join(choices(string.ascii_lowercase, k=15)) + "." + domain
        return socket.gethostbyname(random_sub)
    except: return None

def check_live_pro(subdomain, wildcard_ip, target):
    try:
        current_ip = socket.gethostbyname(subdomain)
        if current_ip == wildcard_ip: return None
        if subdomain.count('.') > target.count('.') + 1: return None

        url = f"http://{subdomain}"
        r = requests.get(url, timeout=3, verify=False, allow_redirects=True)
        if len(r.content) < 100: return None 
        
        sc = r.status_code
        server = r.headers.get('Server', 'Hidden')[:15]
        color = G if sc == 200 else Y if sc in [403, 401] else R
        
        # রিটার্ন ডেটা (টার্মিনাল ডিসপ্লে এবং ফাইল সেভ এর জন্য)
        display = f" {C}»{W} {subdomain.ljust(35)} {B}{color}[{sc}]{W} {C}({server}){W} {Y}[{current_ip}]{W}"
        return (display, subdomain)
    except: return None

def fetch_source(url, domain):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if res.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, res.text)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(description="AS-RECON God-Eye Edition")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-o", "--output", help="Save results to file")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Threads count")
    parser.add_argument("--live", action="store_true", help="Validate live status")
    args = parser.parse_args()
    
    target = args.domain
    print(f"\n{M}{B}[*] INITIALIZING GOD-EYE FILTER: {target}{W}")
    
    wildcard_ip = get_wildcard_ip(target)
    if wildcard_ip: print(f"{R}[!] Wildcard Detected! IP: {wildcard_ip}{W}")

    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns"
    ]

    raw_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            raw_subs.update(f.result())

    clean_list = sorted(list(set([s for s in raw_subs if target in s])))
    print(f"{G}[+]{W} Collected {len(clean_list)} potential targets. Filtering now...\n")

    valid_subs = []
    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = [executor.submit(check_live_pro, s, wildcard_ip, target) for s in clean_list]
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if res:
                    display, sub = res
                    print(display)
                    valid_subs.append(sub)
    else:
        for s in clean_list:
            print(f" {C}»{W} {s}")
            valid_subs.append(s)

    # ফাইল সেভ লজিক
    if args.output and valid_subs:
        with open(args.output, "w") as f:
            f.write("\n".join(valid_subs))
        print(f"\n{G}[!] Mission Accomplished! Results saved in: {B}{args.output}{W}")

if __name__ == "__main__":
    main()
