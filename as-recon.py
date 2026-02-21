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

def strict_filter(sub, domain):
    """
    High-Level Filtering Logic:
    ১. মেইন ডোমেইন ছাড়া অন্য কোনো ডোমেইন লিকেজ (like .com.bd.target.com) ব্লক করবে।
    ২. ডাবল ডট বা ইনভ্যালিড ক্যারেক্টার ক্লিন করবে।
    ৩. শুধু জেনুইন সাবডোমেইন রিটার্ন করবে।
    """
    sub = sub.lower().strip().strip('.')
    
    # সার্টিফিকেট স্টার রিমুভ
    if sub.startswith("*."): sub = sub[2:]
    
    # Noise Filtering: ডোমেইনের মাঝখানে অন্য TLD থাকলে সেটা ভুয়া (যেমন: example.com.renesabazar.com)
    # আমরা শুধু চেক করবো ডোমেইনের আগে কয়টা পার্ট আছে
    if sub.count(domain) > 1: return None
    
    # ভ্যালিড সাবডোমেইন চেক (Regex: Strict Mode)
    # এটি নিশ্চিত করবে ডোমেইনের আগে শুধু আলফানিউমেরিক ক্যারেক্টার আছে
    pattern = re.compile(r'^([a-z0-9-]+\.)+' + re.escape(domain) + '$')
    if not pattern.match(sub): return None

    # অতিরিক্ত সুরক্ষার জন্য ডাবল ডোমেইন এক্সটেনশন চেক
    forbidden_leak = ['.com.', '.net.', '.org.', '.info.', '.edu.', '.gov.']
    if any(leak in sub for leak in forbidden_leak): return None

    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw_subs = re.findall(pattern, r.text)
            
            cleaned = set()
            for s in raw_subs:
                c = strict_filter(s, domain)
                if c: cleaned.add(c)
            return list(cleaned)
    except: pass
    return []

# [Intelligence Class & Check Live Logic remains same for efficiency]

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Target domain")
    
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--live", action="store_true", help="Enable live host checking")
    
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=60, help="Threads (Default: 60)")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show help")

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

    print(f"{C}[*] Initializing Strict-Intelligence on: {target}{W}")
    
    raw_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_results.update(res)

    final_list = sorted(list(raw_results))

    print(f"{Y}[*] Hunting Finished. Applying High-Level Filters...{W}")
    
    if not final_list:
        print(f"{R}[!] No valid subdomains found.{W}")
    else:
        print(f"{G}[+]{W} Unique Cleaned Targets: {B}{len(final_list)}{W}\n")
        for s in final_list:
            print(f" {C}»{W} {s}")

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY (v10.2 PRO){W}                 {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_list):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
