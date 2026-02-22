#!/usr/bin/env python3
import sys
import os
import argparse
import random
import re
import time
import json
from datetime import datetime

# ⚡ [DEPENDENCY CHECK] কোনো এরর ছাড়াই মডিউল চেক করা
try:
    import asyncio
    import aiohttp
    import aiodns
    import dns.resolver
    import urllib3
    urllib3.disable_warnings()
except ImportError as e:
    # যদি কোনো মডিউল মিসিং থাকে, তবে সুন্দর করে ইনস্ট্রাকশন দেবে
    missing = str(e).split("'")[-2]
    pkg = "dnspython" if missing == "dns" else missing
    print(f"\033[91m[!] Missing Module: {missing}\033[0m")
    print(f"\033[93m[#] Please run this command to fix:\033[0m")
    print(f"\033[1;92m    sudo /opt/as-recon/venv/bin/pip install aiohttp aiodns dnspython\033[0m")
    sys.exit(1)

# Visuals
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         [ v35.0 - STABLE POWER ] • [ PERMISSION FIXED ]{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        # High-performance DNS resolvers
        self.resolver = aiodns.DNSResolver(rotate=True, timeout=2)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']

    async def add_to_queue(self, item, priority=10):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def fetch_source(self, session, url):
        try:
            async with session.get(url.format(domain=self.domain), timeout=15) as r:
                if r.status == 200:
                    data = await r.text()
                    # Enhanced regex for subdomain matching
                    pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+' + re.escape(self.domain) + r'\b'
                    matches = re.findall(pattern, data, re.I)
                    return {m.lower().strip('.') for m in matches}
        except: pass
        return set()

    async def worker(self, session):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=4.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                
                try:
                    res = await self.resolver.query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        print(f"{G}[+] {sub:<30} {B}{str(ips):<20}{W} [LIVE]")
                        self.assets[sub] = ips
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"{B}[*] Target: {self.domain} | Mode: High-Power ({self.threads} Threads)\n" + "—"*70)
        
        sources = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://jldc.me/anubis/subdomains/{domain}",
            "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
            "http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey"
        ]

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.threads, ssl=False)) as session:
            tasks = [self.fetch_source(session, url) for url in sources]
            results = await asyncio.gather(*tasks)
            for sub_set in results:
                if sub_set:
                    for sub in sub_set: await self.add_to_queue(sub)
            
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await asyncio.gather(*workers)

        print(f"\n{G}[#] Scan Complete! Total Live Assets: {len(self.assets)}{W}")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domain", nargs="?", help="Target domain")
    parser.add_argument("-t", "--threads", type=int, default=300)
    parser.add_argument("-h", "--help", action="help")
    
    args = parser.parse_args()
    
    if not args.domain:
        print(LOGO)
        print(f"{Y}Usage: asrecon google.com{W}")
        sys.exit(0)

    try:
        asyncio.run(ReconEngine(args.domain, args.threads).run())
    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopping power...{W}")

if __name__ == "__main__":
    main()
