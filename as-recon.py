#!/usr/bin/env python3
import requests
import urllib3
import requests
import urllib3
import sys
import concurrent.futures
import os

# SSL Warnings বন্ধ করা (Termux/Linux এর জন্য)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BANNER = """
     ___    ____        ____  __________  ______  _   __
    /   |  / ___/      / __ \/ ____/ __ \/ ____/ / | / /
   / /| |  \__ \______/ /_/ / __/ / / / / /   /  |/ /
  / ___ | ___/ /_____/ _, _/ /___/ /_/ / /___/ /|  /
 /_/  |_/____/     /_/ |_/_____/\____/\____/_/ |_/
                                             v4.1-Pro
--------------------------------------------------------
   Author  : @hakspare (Ajijul Islam Shohan)
   10+ Sources | Ultra-Fast | Low Storage
--------------------------------------------------------
"""

def fetch_data(url, domain):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Timeout ৫ সেকেন্ড দেওয়া হয়েছে যাতে টুল স্লো না হয়
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        if response.status_code == 200:
            return [line for line in response.text.splitlines() if domain in line]
    except:
        pass
    return []

def run_recon(domain):
    print(f"[INFO] 🚀 Multi-Source Engine active for: {domain}")
    
    sources = [
        f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=txt&fl=original&collapse=urlkey",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={domain}",
        f"https://crt.sh/?q=%25.{domain}&output=json",
        f"https://api.subdomain.center/api/index.php?domain={domain}",
        f"https://sonar.omnisint.io/subdomains/{domain}",
        f"https://jldc.me/anubis/subdomains/{domain}",
        f"https://api.threatminer.org/v2/domain.php?q={domain}&rt=5"
    ]

    all_found = set()
    # ১০টি থ্রেড একসাথে কাজ করবে, তাই ১ সেকেন্ডেই সব রেজাল্ট চলে আসবে
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(fetch_data, url, domain) for url in sources]
        for future in concurrent.futures.as_completed(futures):
            all_found.update(future.result())
    
    return sorted(list(all_found))

def main():
    print(BANNER)
    if len(sys.argv) < 3 or sys.argv[1] != "-d":
        print("Usage: as-recon -d example.com")
        sys.exit(1)

    target = sys.argv[2]
    results = run_recon(target)

    if results:
        # রেজাল্ট ফাইল সেভ করা
        filename = f"res_{target.replace('.','_')}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(results))
        print(f"\n[✓] Done! {len(results)} Unique Results Found.")
        print(f"[📂] Saved to: {filename}")
    else:
        print("\n[!] No URLs found. Check your connection or try another domain.")

if __name__ == "__main__":
    main()
