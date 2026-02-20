#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket
from random import choice, choices
import string

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Pro Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

def get_banner():
    return rf"""
{M}{B}   ▄▄▄· .▄▄ ·      ▄▄▄▄▄▄▄▄ . ▄▄·       ▐ ▄ 
{M}  ▐█ ▀█ ▐█ ▀. ▪     •██  ▀▄.▀·▐█ ▄·▪     •█▌▐█
{M}  ▄█▀▀█ ▄▀▀▀█▄ ▄█▀▄  ▐█.▪▐▀▀▪▄██▀▀█▄█▀▄ ▐█▐▐▌
{M}  ▐█ ▪▐▌▐█▄▪▐█▐█▌.▐▌ ▐█▌·▐█▄▄▌▐█ ▪▐█▐█▌.▐▌██▐█▌
{M}   ▀  ▀  ▀▀▀▀  ▀█▄▀▪ ▀▀▀  ▀▀▀  ▀  ▀ ▀█▄▀▪▀▀ █▪
{W}{B}     >> AS-RECON v8.0: The Sentinel Edition <<{W}
{G}--------------------------------------------------------{W}"""

def is_wildcard(domain):
    """সার্ভারে ওয়াইল্ডকার্ড ডিএনএস আছে কি না চেক করে"""
    random_sub = ''.join(choices(string.ascii_lowercase + string.digits, k=12)) + "." + domain
    try:
        r = requests.get(f"http://{random_sub}", timeout=3, verify=False)
        return True # যদি উল্টাপাল্টা ডোমেইনও ২০০ দেয়, তবে ওয়াইল্ডকার্ড আছে
    except:
        return False

def clean_subdomain(sub, domain):
    """Recursive junk পরিষ্কার করার লজিক"""
    sub = sub.lower().strip()
    # শুধুমাত্র ভ্যালিড ক্যারেক্টার রাখা
    if not re.match(r'^[a-z0-9.-]+$', sub): return None
    # ডোমেইনের ভেতরে ডোমেইন থাকলে ট্রিম করা
    if sub.count(domain) > 1: return None 
    return sub

def check_live(subdomain):
    """Deep Intelligence: সার্ভার হেডারসহ চেক"""
    try:
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=3, verify=False, allow_redirects=True)
        sc = r.status_code
        
        # সার্ভার ফিঙ্গারপ্রিন্টিং
        server = r.headers.get('Server', 'Unknown')
        
        color = G if sc == 200 else Y if sc in [403, 401] else R
        return f"{subdomain} {B}{color}[{sc}]{W} {C}({server}){W}"
    except:
        return None

def fetch_source(url, domain):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if res.status_code == 200:
            # উন্নতমানের রেজেক্স ফিল্টার
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            subs = re.findall(pattern, res.text)
            return [s.lower() for s in subs]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    
    print(get_banner())
    target = args.domain
    start_time = time.time()

    # ১. ওয়াইল্ডকার্ড ডিটেকশন (Intelligence)
    print(f"{C}[*]{W} Analyzing DNS infrastructure...")
    wildcard_enabled = is_wildcard(target)
    if wildcard_enabled:
        print(f"{R}[!] Wildcard DNS detected! Activating Strict Filter.{W}")

    # ২. সোর্স থেকে ডেটা কালেকশন
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"https://crt.sh/?q=%25.{target}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns"
    ]

    all_subs = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            all_subs.update(f.result())

    # ৩. অ্যাডভান্সড ক্লিনিং
    cleaned_subs = set()
    for s in all_subs:
        c = clean_subdomain(s, target)
        if c: cleaned_subs.add(c)
    
    # Junk filter (যেমন 'nwww', 'nmail' এগুলো সচরাচর নয়েজ হয়)
    final_list = []
    noise_pattern = re.compile(r'^(nwww|nmail|ncp|nautodiscover|nwebdisk)\.')
    for s in sorted(list(cleaned_subs)):
        if wildcard_enabled and noise_pattern.match(s):
            continue
        final_list.append(s)

    print(f"{G}[+]{W} Unique Intelligence Found: {B}{len(final_list)}{W}\n")

    # ৪. লাইভ ভ্যালিডেশন
    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            results = list(executor.map(check_live, final_list))
            for r in results:
                if r: print(f" {M}»{W} {r}")

    print(f"\n{Y}SCAN COMPLETED IN {round(time.time()-start_time, 2)}s{W}")

if __name__ == "__main__":
    main()
