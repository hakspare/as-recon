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

def print_summary(results, duration, output_file=None):
    """এটি নিশ্চিত করবে যে ইউজার সবসময় একটি সুন্দর বক্স দেখবে"""
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY{W}                             {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(results):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    if output_file:
        print(f"{G}│{W}  {C}Saved To      :{W} {B}{output_file:<20}{W}   {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, r.text)]
    except: pass
    return []

def main():
    start_time = time.time()
    print(LOGO)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-o", "--output")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    # Hunt logic
    sources = [
        f"https://crt.sh/?q=%25.{args.domain}",
        f"https://api.subdomain.center/api/index.php?domain={args.domain}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{args.domain}/passive_dns"
    ]

    print(f"{B}{C}[*] Hunting Subdomains for: {args.domain}{W}")
    raw_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_source, url, args.domain): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            raw_subs.update(f.result())

    clean_list = sorted(list(set([s for s in raw_subs if args.domain in s])))
    final_results = []

    if clean_list:
        print(f"{G}[+]{W} Total Candidates Found: {B}{len(clean_list)}{W}\n")
        # Passive mode: সরাসরি লিস্টে সেভ হবে
        for s in clean_list:
            print(f" {C}»{W} {s}")
            final_results.append(s)
        
        # ফাইল সেভ লজিক
        if args.output:
            with open(args.output, "w") as f:
                f.write("\n".join(final_results))

    # সামারি প্রিন্ট (এটি মেইন লজিকের একদম বাইরে)
    duration = round(time.time() - start_time, 2)
    print_summary(final_results, duration, args.output)

if __name__ == "__main__":
    main()
