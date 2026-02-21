#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, random, string, math
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
    prob = [n/len(label) for n in Counter(label).values()]
    return -sum(p * math.log2(p) for p in prob)

def is_valid_sub(sub, domain):
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]
    
    # ১. Strict Domain Match (অন্য ডোমেইন লিক হওয়া বন্ধ করবে)
    if not sub.endswith(domain) or sub == domain: return None
    
    # ২. Garbage/Entropy Filter (আপনার দেওয়া ৩.৫ থ্রেশহোল্ড)
    first_part = sub.split('.')[0]
    if get_entropy(first_part) > 3.5 and len(first_part) > 12: return None
    
    # ৩. Double TLD Leakage (azprintbd.com.renesabazar.com বাদ দিবে)
    bad_patterns = ['.com.', '.net.', '.org.', '.edu.', '.gov.', '.co.']
    if any(p in sub for p in bad_patterns): return None

    # ৪. Duplicate domain count check
    if sub.count(domain) > 1: return None

    return sub

def resolves(sub):
    try:
        socket.gethostbyname(sub)
        return True
    except: return False

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            return [s for s in raw if is_valid_sub(s, domain)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("--resolve", action="store_true")
    args = parser.parse_args()

    target = args.domain
    print(LOGO)
    print(f"{C}[*] Initializing High-Level Filtering on: {target}{W}")
    
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    all_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                for s in res:
                    valid = is_valid_sub(s, target)
                    if valid: all_found.add(valid)

    # রেজাল্ট সর্টিং এবং ক্লিন ডাইরেক্ট আউটপুট
    final = sorted(list(all_found))
    
    # DNS Resolution Filter (আপনার রিকোয়েস্ট অনুযায়ী)
    valid_subs = []
    print(f"{Y}[*] Validating {len(final)} candidates...{W}")
    
    for s in final:
        if args.resolve:
            if resolves(s):
                print(f" {G}»{W} {s}")
                valid_subs.append(s)
        else:
            print(f" {C}»{W} {s}")
            valid_subs.append(s)

    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}TOTAL CLEANED FOUND: {len(valid_subs):<10}{W}      {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
