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
    👉 এই ফাংশনটি আপনার Filtering Perfect করবে।
    এটি Dirty Data, Regex Over-match এবং Wordlist Leak ফিক্স করবে।
    """
    sub = sub.lower().strip()
    # ১. সার্টিফিকেট পার্সিং এবং ওয়াইল্ডকার্ড ফিক্স
    if sub.startswith("*."): sub = sub[2:]
    if sub.startswith("."): sub = sub[1:]
    
    # ২. Regex Over-match ফিক্স (শুধু ডোমেইন পর্যন্ত রাখা)
    # এটি ডোমেইনের পরের সব আবর্জনা (যেমন ", /, ?, >) কেটে ফেলে
    match = re.search(r'([a-z0-9-.]+\.' + re.escape(domain) + r')', sub)
    if match:
        sub = match.group(1)
    
    # ৩. Dirty Data Filtering (অপ্রয়োজনীয় ক্যারেক্টার থাকলে বাদ)
    if not all(c in (string.ascii_lowercase + string.digits + ".-") for c in sub):
        return None
    
    # ৪. ডাবল ডট বা ভুল ফরমেট ফিক্স
    if ".." in sub or sub == domain:
        return None
        
    return sub

def fetch_source(url, domain):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            # পাওয়ারফুল Regex যা ডোমেইনের প্যাটার্ন চেনে
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw_subs = re.findall(pattern, r.text)
            
            cleaned = []
            for s in raw_subs:
                c = clean_subdomain(s, domain)
                if c: cleaned.append(c)
            return cleaned
    except: pass
    return []

# ... [বাকি Intelligence ক্লাস এবং check_live ফাংশন আগের মতোই থাকবে] ...

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", metavar="DOMAIN", required=True, help="Target domain")
    
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--live", action="store_true", help="Check live hosts")
    
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=60, help="Threads")
    
    out_grp = parser.add_argument_group(f'{Y}OUTPUT{W}')
    out_grp.add_argument("-o", "--output", help="Save result")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show help")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    args = parser.parse_args()

    # --- Scanning Logic with Improved Filtering ---
    start_time = time.time()
    target = args.domain
    
    # Sources list
    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{C}[*] Hunting Subdomains for: {target}{W}")
    
    raw_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_results.update(res)

    # ডুপ্লিকেট রিমুভ এবং সর্টিং
    final_list = sorted(list(raw_results))

    print(f"{G}[+]{W} Unique Cleaned Targets: {B}{len(final_list)}{W}\n")
    
    # লাইভ চেক এবং সামারি কোড (আগের মতো)
    # ... [Summary and Output Logic] ...
