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

def clean_subdomain(sub, domain):
    """
    👉 Strict Sanitizer: ভুল ডোমেইন লিকেজ এবং নোইজ ডাটা ফিল্টার করে।
    """
    sub = sub.lower().strip().strip('.')
    
    # ১. সার্টিফিকেট স্টার/ওয়াইল্ডকার্ড রিমুভাল
    if sub.startswith("*."): sub = sub[2:]
    
    # ২. Noise Filtering: সাবডোমেইনের মাঝখানে অন্য কোনো TLD (.com, .org) থাকলে বাদ
    # এটি azprintbd.com.renesabazar.com এর মতো ভুল ডাটা ব্লক করবে
    invalid_tlds = ['.com.', '.org.', '.net.', '.edu.', '.gov.', '.xyz.', '.info.']
    if any(tld in sub for tld in invalid_tlds):
        return None

    # ৩. ডাবল ডোমেইন ডিটেকশন (target.com.target.com)
    if sub.count(domain) > 1:
        return None

    # ৪. Regex Validation: শুধু ভ্যালিড ক্যারেক্টার এবং সঠিক ডোমেইন ফরমেট নিশ্চিত করা
    pattern = re.compile(r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+' + re.escape(domain) + '$')
    if not pattern.match(sub):
        return None
    
    # ৫. সেলফ-ডোমেইন ফিল্টার
    if sub == domain:
        return None
        
    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw_subs = re.findall(pattern, r.text)
            
            cleaned = set()
            for s in raw_subs:
                c = clean_subdomain(s, domain)
                if c: cleaned.add(c)
            return list(cleaned)
    except: pass
    return []

# ... [Intelligence Class and live check logic remains same] ...

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Domain to scan")
    
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--live", action="store_true", help="Check for live hosts")
    
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=60, help="Threads (Default: 60)")
    
    out_grp = parser.add_argument_group(f'{Y}OUTPUT{W}')
    out_grp.add_argument("-o", "--output", help="Save text results to file")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show advanced help menu")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    args = parser.parse_args()

    start_time = time.time()
    target = args.domain
    
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{B}{C}[*] Initializing Intelligence on: {target}{W}")
    
    raw_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_results.update(res)

    final_list = sorted(list(raw_results))

    if not final_list:
        print(f"{R}[!] No valid discovery data found.{W}")
    else:
        print(f"{G}[+]{W} Total Potential Targets: {B}{len(final_list)}{W}\n")
        for s in final_list:
            print(f" {C}»{W} {s}")

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2){W}                     {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_list):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
