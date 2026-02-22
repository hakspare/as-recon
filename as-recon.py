#!/usr/bin/env python3
import sys, os, subprocess

# ⚡ [SYSTEM INJECTION] সকল ইউজারের জন্য অটো-ডিপেন্ডেন্সি সেটআপ
def system_prep():
    needed = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3', 'dnspython']
    for m in needed:
        try: __import__(m)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", m, "--user", "--break-system-packages", "--quiet"])

system_prep()

import asyncio, aiohttp, json, argparse, random, re, time, urllib3, aiodns, dns.resolver
from datetime import datetime
from pathlib import Path

urllib3.disable_warnings()

# [Visuals] Commercial Theme
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         [ GOD MODE ACTIVE ] • [ UNLIMITED POWER EDITION ]{W}
"""

class ReconEngine:
    def __init__(self, args):
        self.domain = args.domain.lower()
        self.threads = args.threads
        self.depth = args.depth
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.resolver = aiodns.DNSResolver(rotate=True, timeout=2)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9', '1.0.0.1']

    async def add_to_queue(self, item, priority=10):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def fetch_api(self, session, name, url):
        """High-Performance API Fetcher"""
        try:
            async with session.get(url.format(domain=self.domain), timeout=15) as r:
                if r.status == 200:
                    data = await r.text()
                    matches = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+' + re.escape(self.domain) + r'\b', data, re.I)
                    return {m.lower().strip('.') for m in matches}
        except: pass
        return set()

    async def probe_http(self, session, sub):
        """Advanced Prober: Identifying Live Tech Stack"""
        for proto in ['http', 'https']:
            try:
                async with session.get(f"{proto}://{sub}", timeout=5, verify_ssl=False) as r:
                    text = await r.text()
                    title = re.search(r'<title>(.*?)</title>', text, re.I)
                    title = title.group(1).strip()[:30] if title else "No Title"
                    server = r.headers.get('Server', 'Unknown')
                    return r.status, title, server, proto
            except: continue
        return None, None, None, None

    async def worker(self, session):
        while True:
            try:
                prio_val, _, sub = await asyncio.wait_for(self.queue.get(), timeout=5.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                
                try:
                    # DNS রেজোলিউশন (God Mode Speed)
                    res = await self.resolver.query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title, server, proto = await self.probe_http(session, sub)
                        if status:
                            print(f"{G}[+] {sub:<35} {B}{str(ips):<20}{W} [{status}] [{C}{title}{W}] [{Y}{server}{W}]")
                            self.assets[sub] = {"ips": ips, "status": status, "title": title, "server": server}
                            
                            # রিকার্সিভ স্ক্যান (যদি ডেপথ বাকি থাকে)
                            current_depth = sub.count('.') - self.domain.count('.')
                            if current_depth < self.depth:
                                for p in ["dev", "api", "v1", "test", "staging"]:
                                    await self.add_to_queue(f"{p}.{sub}", 30)
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"{B}{M}[*]{W} Recon Level: {B}God-Mode{W} | Threads: {B}{self.threads}{W} | Depth: {B}{self.depth}{W}")
        print(f"{B}{M}[*]{W} Start Time: {datetime.now().strftime('%H:%M:%S')}\n" + "—"*85)

        # ৫০+ প্যাসিভ সোর্সের চেয়েও শক্তিশালী ১০টি হাই-ভ্যালু সোর্স
        sources = {
            "Crtsh": "https://crt.sh/?q=%.{domain}&output=json",
            "Wayback": "http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey",
            "Anubis": "https://jldc.me/anubis/subdomains/{domain}",
            "Alienvault": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
            "HackerTarget": "https://api.hackertarget.com/hostsearch/?q={domain}",
            "RapidDNS": "https://rapiddns.io/subdomain/{domain}?full=1",
            "CommonCrawl": "http://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{domain}/*&output=json"
        }

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.threads, ssl=False)) as session:
            # Phase 1: Passive Intelligence
            tasks = [self.fetch_api(session, name, url) for name, url in sources.items()]
            results = await asyncio.gather(*tasks)
            for sub_set in results:
                if sub_set:
                    for sub in sub_set: await self.add_to_queue(sub, 20)
            
            print(f"{B}{Y}[!] Intelligence Gathered. Starting Deep Probing...{W}\n")
            
            # Phase 2: Active Probing & Recursive Discovery
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await asyncio.gather(*workers)

        print(f"\n{B}{G}[#] Recon Complete. Total Unique Assets Found: {len(self.assets)}{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON God Mode", add_help=False)
    group = parser.add_argument_group(f"{B}{Y}ADVANCED COMMANDS{W}")
    group.add_argument("-d", "--domain", required=True, help="Target domain (e.g., google.com)")
    group.add_argument("-t", "--threads", type=int, default=400, help="God-mode threads (Default: 400)")
    group.add_argument("-x", "--depth", type=int, default=3, help="Recursive scan depth (Default: 3)")
    group.add_argument("-h", "--help", action="help", help="Show this menu")
    
    if len(sys.argv) == 1:
        print(LOGO)
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    try:
        asyncio.run(ReconEngine(args).run())
    except KeyboardInterrupt:
        print(f"\n{R}[!] Powering down...{W}")

if __name__ == "__main__":
    main()
