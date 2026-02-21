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

def is_valid_sub(sub, domain):
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]
    
    # ১. Strict Validation: সাবডোমেইন অবশ্যই domain দিয়ে শেষ হতে হবে
    if not sub.endswith(f".{domain}") and sub != domain:
        return None

    # ২. Noise Filtering: সাবডোমেইন অংশে অন্য কোনো ডোমেইন এক্সটেনশন থাকা চলবে না
    # এটি azprintbd.com.renesabazar.com কে সরাসরি ব্লক করবে
    sub_part = sub.replace(domain, "").strip('.')
    garbage_extensions = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.bd']
    if any(ext in sub_part for ext in garbage_extensions):
        return None

    # ৩. Entropy check: র‍্যান্ডম গারবেজ ক্যারেক্টার ফিল্টার
    prob = [n/len(sub_part) for n in Counter(sub_part).values()] if sub_part else [0]
    entropy = -sum(p * math.log2(p) for p in prob if p > 0)
    if entropy > 3.7 and len(sub_part) > 12:
        return None

    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            # পাওয়ারফুল Regex যা শুধু ডোমেইন রিলেটেড স্ট্রিং ধরবে
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            
            # সরাসরি স্যানিটাইজেশন
            return [s for s in raw if is_valid_sub(s, domain)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-d", "--domain", required=True)
    args = parser.parse_args()

    target = args.domain
    print(LOGO)
    print(f"{C}[*] Hunting Subdomains for: {target}{W}")
    
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
            if res: all_found.update(res)

    # ফাইনাল ক্লিনআপ এবং ডুপ্লিকেট রিমুভ
    final_results = sorted(list(all_found))
    
    print(f"{G}[+]{W} Total Unique Cleaned Targets: {B}{len(final_results)}{W}\n")
    
    for s in final_results:
        print(f" {C}»{W} {s}")

    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY: {len(final_results):<10}{W}             {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
