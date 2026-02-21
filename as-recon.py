#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, math
from collections import Counter

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

def get_entropy(label):
    if not label: return 0
    prob = [n/len(label) for n in Counter(label).values()]
    return -sum(p * math.log2(p) for p in prob)

def is_valid_sub(sub, domain):
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]
    
    # ১. Strict Anchor: ডোমেইনটা একদম শেষে থাকতে হবে এবং তার আগে শুধু একটা সাবডোমেইন পার্ট থাকবে
    # এটি azprintbd.com.renesabazar.com কে সরাসরি রিজেক্ট করবে
    if not sub.endswith(f".{domain}") and sub != domain:
        return None

    # ২. Garbage/Entropy Filter: সাবডোমেইনের প্রথম পার্ট চেক করা
    parts = sub.replace(f".{domain}", "").split('.')
    first_part = parts[0]
    
    # যদি মাঝখানে অন্য কোনো TLD থাকে (যেমন .com, .org) তবে ওটা সরাসরি বাদ
    bad_tlds = ['com', 'org', 'net', 'edu', 'gov', 'co', 'biz', 'info']
    if any(tld == p for p in parts for tld in bad_tlds):
        return None

    # এন্ট্রপি চেক (আপনার লজিক)
    if get_entropy(first_part) > 3.6 and len(first_part) > 12:
        return None

    return sub

def resolves(sub):
    try:
        socket.gethostbyname(sub)
        return True
    except:
        return False

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12, verify=False)
        if r.status_code == 200:
            # ৩. Improved Regex: এটি শুধু আলফানিউমেরিক সাবডোমেইন ধরবে, ডট-ওয়ালা অন্য ডোমেইন নয়
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            
            valid_set = set()
            for s in raw:
                v = is_valid_sub(s, domain)
                if v: valid_set.add(v)
            return list(valid_set)
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("--resolve", action="store_true")
    args = parser.parse_args()

    target = args.domain
    print(LOGO)
    print(f"{C}[*] Initializing Strict-Filtering on: {target}{W}")
    
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    all_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: all_subs.update(res)

    final_list = sorted(list(all_subs))
    
    print(f"{G}[+]{W} Total Potential Targets: {B}{len(final_list)}{W}\n")
    
    count = 0
    for s in final_list:
        if args.resolve:
            if resolves(s):
                print(f" {G}»{W} {s}")
                count += 1
        else:
            print(f" {C}»{W} {s}")
            count += 1

    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}TOTAL CLEANED: {count:<10}{W}               {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
