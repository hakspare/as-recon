#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, string
from random import choices

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Pro Styling ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

def get_wildcard_ip(domain):
    """ভুয়া সাবডোমেইনের আইপি বের করা (Wildcard Detection)"""
    try:
        random_sub = ''.join(choices(string.ascii_lowercase, k=15)) + "." + domain
        return socket.gethostbyname(random_sub)
    except:
        return None

def check_live_pro(subdomain, wildcard_ip, target):
    """অ্যাডভান্সড ফিল্টারিং ইঞ্জিন"""
    try:
        # ১. IP ভিত্তিক ফিল্টারিং
        current_ip = socket.gethostbyname(subdomain)
        if current_ip == wildcard_ip:
            return None # False Positive detected

        # ২. ডোমেইন স্ট্রিপিং (যদি সাবডোমেইনের ভেতর অন্য ডোমেইন থাকে)
        if subdomain.count('.') > target.count('.') + 1:
            # অতিরিক্ত ডট থাকলে সেটা সম্ভবত জাঙ্ক (যেমন: azprintbd.com.renesabazar.com)
            return None

        # ৩. HTTP রিকোয়েস্ট উইথ ইন্টেলিজেন্স
        url = f"http://{subdomain}"
        r = requests.get(url, timeout=3, verify=False, allow_redirects=True)
        
        # যদি পেজ সাইজ খুব ছোট হয় বা টাইটেল 'Index of' থাকে (বাজে হোস্টিং এর লক্ষণ)
        if len(r.content) < 100: return None 
        
        sc = r.status_code
        server = r.headers.get('Server', 'Hidden')[:15]
        
        color = G if sc == 200 else Y if sc in [403, 401] else R
        return f"{subdomain.ljust(35)} {B}{color}[{sc}]{W} {C}({server}){W} {Y}[{current_ip}]{W}"
    except:
        return None

def fetch_source(url, domain):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
        if res.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            return [s.lower() for s in re.findall(pattern, res.text)]
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    
    target = args.domain
    print(f"\n{M}{B}[*] INITIALIZING GOD-EYE FILTER FOR: {target}{W}")
    
    # ওয়াইল্ডকার্ড আইপি ডিটেক্ট করা
    wildcard_ip = get_wildcard_ip(target)
    if wildcard_ip:
        print(f"{R}[!] Wildcard Detected! IP: {wildcard_ip} (Filtering active){W}")

    # সোর্স থেকে ডেটা নেওয়া (আগের সোর্সগুলোই থাকবে)
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

    # ইউনিক ডোমেইন ফিল্টার
    clean_list = sorted(list(set([s for s in raw_subs if target in s])))
    print(f"{G}[+]{W} Collected {len(clean_list)} potential targets. Filtering now...\n")

    # লাইভ ভ্যালিডেশন (The Real Magic)
    if args.live:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            # আর্গুমেন্ট পাস করার জন্য ল্যাম্বডা বা পার্শিয়াল দরকার নেই, সরাসরি লিস্ট কম্প্রিহেনশন
            results = [executor.submit(check_live_pro, s, wildcard_ip, target) for s in clean_list]
            for f in concurrent.futures.as_completed(results):
                r = f.result()
                if r: print(f" {C}»{W} {r}")

if __name__ == "__main__":
    main()
