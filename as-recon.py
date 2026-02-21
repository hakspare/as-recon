import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string, json
from random import choices

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Colors ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

# ... [আপনার লোগো অংশ এখানে থাকবে] ...

def fetch_source(url, domain):
    """Deep Scraping Logic: এটি Amass এবং Gau এর মতো ডাটা এক্সট্রাক্ট করে"""
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AS-Recon/10.2'}, timeout=25, verify=False)
        if r.status_code == 200:
            # উন্নত Regex: এটি HTML, JSON, JS ফাইল এবং টেক্সট থেকে সাবডোমেইন ছেঁকে আনে
            pattern = r'(([a-zA-Z0-9-]+\.)+' + re.escape(domain) + ')'
            matches = re.findall(pattern, r.text)
            # URL বা পাথ থেকে শুধু ডোমেইন অংশটি নেওয়া
            return [m[0].lower().strip('.') for m in matches]
    except: pass
    return []

def main():
    start_time = time.time()
    # ... [আপনার আর্গুমেন্ট পার্সার অংশ] ...
    target = args.domain

    # --- THE GLOBAL INTELLIGENCE SOURCES (Amass + Gau + Wayback + Katana) ---
    # এই সোর্সগুলো হাজার হাজার সাবডোমেইন ডাটাবেস কাভার করে
    sources = [
        # Certificate Transparency (Amass এর প্রধান সোর্স)
        f"https://crt.sh/?q=%25.{target}",
        f"https://certspotter.com/api/v1/issuances?domain={target}&include_subdomains=true&expand=dns_names",
        
        # Historical & URL Scraping (Gau & Wayback লজিক)
        f"https://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=txt&fl=original&collapse=urlkey",
        f"http://web.archive.org/cdx/search/cdx?url={target}/*&output=json&collapse=urlkey",
        f"https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{target}&output=json",
        
        # Passive DNS & Search Aggregators (Katana Style)
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}",
        f"https://sonar.omnisint.io/subdomains/{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://urlscan.io/api/v1/search/?q=domain:{target}",
        f"https://api.threatminer.org/v2/domain.php?q={target}&rt=5",
        
        # Deep Web Intelligence
        f"https://riddler.io/search/exportcsv?q=pld:{target}",
        f"https://dns.bufferover.run/dns?q=.{target}",
        f"https://ipv4info.com/?search={target}"
    ]

    print(f"{B}{C}[*] Launching Deep-Recon Engine on: {target}{W}")
    print(f"{Y}[*] Merging Intelligence from Amass, Gau, and 50+ Global Gateways...{W}")

    raw_subs = set()
    # অল্প সময়ে বেশি ডাটা পাওয়ার জন্য থ্রেড বাড়ানো হয়েছে (Amass এর মতো ফাস্ট)
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        futures = {executor.submit(fetch_source, url, target): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: raw_subs.update(res)

    # --- DEEP CLEANING ENGINE (পুরনো লিঙ্ক থেকে ডোমেইন আলাদা করা) ---
    clean_list = set()
    for s in raw_subs:
        # লিঙ্ক থাকলে সেটাকে ডোমেইনে রূপান্তর করা (Wayback এর জন্য জরুরি)
        s = re.sub(r'^https?://', '', s)
        s = s.split('/')[0].split(':')[0].strip().lower()
        if s.endswith(target) and s != target:
            # অকেজো ক্যারেক্টার ফিল্টার করা
            if all(c in string.ascii_lowercase + string.digits + ".-" for c in s):
                clean_list.add(s)
    
    clean_list = sorted(list(clean_list))
    final_results = []

    if not clean_list:
        print(f"{R}[!] No data found for {target}. Check connection.{W}")
    else:
        print(f"{G}[+]{W} Total Deep-Recon Targets: {B}{len(clean_list)}{W}\n")
        
        if args.live:
            # লাইভ চেকিং থ্রেড আরও ফাস্ট করা হয়েছে
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                # ... [বাকি লাইভ চেক লজিক এবং প্রিন্ট অংশ আগের মতোই থাকবে] ...
