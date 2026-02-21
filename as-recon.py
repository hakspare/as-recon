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

def advanced_strict_filter(sub, target_domain):
    """
    👉 এই ফাংশনটিই আপনার আসল ফিল্টার।
    এটি চেক করে সাবডোমেইনটি কি আসলেই target_domain এর অংশ, নাকি অন্য কোনো ডোমেইন ঢুকে গেছে।
    """
    sub = sub.lower().strip().strip('.')
    if sub.startswith("*."): sub = sub[2:]

    # ১. Noise Filtering: যদি সাবডোমেইনের ভেতর অন্য TLD থাকে (যেমন .com. .net. .org.)
    # target_domain এর বাইরে কোনো ডট থাকলে সেটা বাদ।
    # উদাহরণ: azprintbd.com.renesabazar.com বাদ যাবে।
    check_pattern = r'^([a-z0-9-]+\.)+' + re.escape(target_domain) + '$'
    if not re.match(check_pattern, sub):
        return None

    # ২. Cross-Domain Leakage: সাবডোমেইন পার্টে যদি একাধিকবার ডোমেইন নাম থাকে
    if sub.count(target_domain) > 1:
        return None

    # ৩. Forbidden TLD Leak: অনেক সময় সোর্স থেকে অন্য ডোমেইন লিক হয়
    forbidden = ['.com.', '.net.', '.org.', '.edu.', '.gov.', '.xyz.']
    if any(x in sub for x in forbidden):
        return None

    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12, verify=False)
        if r.status_code == 200:
            # সাবডোমেইন খোঁজার জন্য পাওয়ারফুল প্যাটার্ন
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw_subs = re.findall(pattern, r.text)
            
            cleaned = set()
            for s in raw_subs:
                # এখানে হাই-লেভেল ফিল্টার কল করা হচ্ছে
                valid_sub = advanced_strict_filter(s, domain)
                if valid_sub:
                    cleaned.add(valid_sub)
            return list(cleaned)
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Target domain")
    
    # Help option
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show help")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
        
    args = parser.parse_args()
    target = args.domain
    start_time = time.time()

    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{C}[*] Initializing Ultra-Strict Filter on: {target}{W}")
    
    all_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: all_found.update(res)

    final_results = sorted(list(all_found))

    if not final_results:
        print(f"{R}[!] No valid subdomains found after strict filtering.{W}")
    else:
        print(f"{G}[+]{W} Unique Cleaned Targets: {B}{len(final_results)}{W}\n")
        for s in final_results:
            print(f" {C}»{W} {s}")

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (STRICT MODE){W}               {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Cleaned :{W} {B}{len(final_results):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
