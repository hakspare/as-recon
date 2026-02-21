#!/usr/bin/env python3
import requests, urllib3, sys, concurrent.futures, re, time, argparse, socket, hashlib, string, random, math
from collections import Counter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- UI & Colors ---
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

class ReconEngine:
    def __init__(self, domain):
        self.domain = domain
        self.wildcard_ip = None
        self.is_wildcard = False

    def detect_wildcard(self):
        """আপনার দেওয়া কনসেপ্ট: ওয়াইল্ডকার্ড ডিএনএস ডিটেকশন"""
        try:
            rand_sub = "".join(random.choice(string.ascii_lowercase) for _ in range(12)) + "." + self.domain
            ip1 = socket.gethostbyname(rand_sub)
            rand_sub2 = "".join(random.choice(string.ascii_lowercase) for _ in range(12)) + "." + self.domain
            ip2 = socket.gethostbyname(rand_sub2)
            if ip1 == ip2:
                self.is_wildcard = True
                self.wildcard_ip = ip1
                return True
        except: pass
        return False

    def get_entropy(self, label):
        """Entropy Filter: গারবেজ সাবডোমেইন চেনার লজিক"""
        prob = [n/len(label) for n in Counter(label).values()]
        return -sum(p * math.log2(p) for p in prob)

    def is_valid_sub(self, sub):
        """High-Level Filtering Pipeline"""
        sub = sub.lower().strip().strip('.')
        if sub.startswith("*."): sub = sub[2:]
        
        # ১. ডোমেইন লিকেজ ফিল্টার
        if sub.count(self.domain) > 1 or not sub.endswith(self.domain): return None
        
        # ২. Entropy/Garbage Filter (যদি এন্ট্রপি ৩.৮ এর বেশি হয় তবে ওটা র‍্যান্ডম জাঙ্ক)
        first_part = sub.split('.')[0]
        if self.get_entropy(first_part) > 3.8 and len(first_part) > 10: return None
        
        # ৩. Cross-TLD Leakage (.com.bd.target.com)
        if any(tld in sub for tld in ['.com.', '.net.', '.org.', '.edu.']): return None

        return sub

def resolve_dns(sub, engine):
    """DNS Resolution লজিক"""
    try:
        ip = socket.gethostbyname(sub)
        if engine.is_wildcard and ip == engine.wildcard_ip:
            return None
        return (sub, ip)
    except: return None

def fetch_source(url, domain, engine):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        if r.status_code == 200:
            pattern = r'(?:[a-zA-Z0-9-]+\.)+' + re.escape(domain)
            raw = re.findall(pattern, r.text)
            cleaned = set()
            for s in raw:
                valid = engine.is_valid_sub(s)
                if valid: cleaned.add(valid)
            return list(cleaned)
    except: pass
    return []

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=LOGO, add_help=False)
    target_grp = parser.add_argument_group(f'{Y}TARGET OPTIONS{W}')
    target_grp.add_argument("-d", "--domain", required=True, help="Domain to scan")
    
    mode_grp = parser.add_argument_group(f'{Y}SCAN MODES{W}')
    mode_grp.add_argument("--resolve", action="store_true", help="Resolve DNS for subdomains")
    
    perf_grp = parser.add_argument_group(f'{Y}PERFORMANCE{W}')
    perf_grp.add_argument("-t", "--threads", type=int, default=50, help="Threads (Default: 50)")
    
    sys_grp = parser.add_argument_group(f'{Y}SYSTEM{W}')
    sys_grp.add_argument("-h", "--help", action="help", help="Show help")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit()
    
    args = parser.parse_args()
    target = args.domain
    engine = ReconEngine(target)
    start_time = time.time()

    print(f"{B}{C}[*] Wildcard Check...{W}", end="\r")
    if engine.detect_wildcard():
        print(f"{R}[!] Wildcard DNS Detected: {engine.wildcard_ip}{W}")
    else:
        print(f"{G}[✓] No Wildcard DNS Detected.       {W}")

    sources = [
        f"https://crt.sh/?q=%25.{target}",
        f"https://api.subdomain.center/api/index.php?domain={target}",
        f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/passive_dns",
        f"https://api.hackertarget.com/hostsearch/?q={target}",
        f"https://jldc.me/anubis/subdomains/{target}"
    ]

    print(f"{Y}[*] Hunting Passive Data...{W}")
    passive_results = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, url, target, engine): url for url in sources}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: passive_results.update(res)

    # --- Filtering & Resolving ---
    final_output = []
    if args.resolve:
        print(f"{Y}[*] Resolving {len(passive_results)} targets...{W}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            jobs = [executor.submit(resolve_dns, s, engine) for s in passive_results]
            for j in concurrent.futures.as_completed(jobs):
                res = j.result()
                if res:
                    print(f" {G}»{W} {res[0].ljust(35)} {C}[{res[1]}]{W}")
                    final_output.append(res[0])
    else:
        for s in sorted(list(passive_results)):
            print(f" {C}»{W} {s}")
            final_output.append(s)

    duration = round(time.time() - start_time, 2)
    print(f"\n{G}┌──────────────────────────────────────────────┐{W}")
    print(f"{G}│{W}  {B}SCAN SUMMARY{W}                                {G}│{W}")
    print(f"{G}├──────────────────────────────────────────────┤{W}")
    print(f"{G}│{W}  {C}Total Found   :{W} {B}{len(final_output):<10}{W}             {G}│{W}")
    print(f"{G}│{W}  {C}Time Elapsed  :{W} {B}{duration:<10} seconds{W}     {G}│{W}")
    print(f"{G}└──────────────────────────────────────────────┘{W}")

if __name__ == "__main__":
    main()
