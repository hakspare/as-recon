#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [ULTIMATE FIX] venv এবং প্যাকেজ নেম এরর সমাধান
def force_load_dependencies():
    # প্যাকেজ ম্যাপ: ইম্পোর্ট নাম বনাম পিপ ইনস্টল নাম
    dependencies = {
        'aiohttp': 'aiohttp',
        'aiodns': 'aiodns',
        'networkx': 'networkx',
        'requests': 'requests',
        'urllib3': 'urllib3',
        'dns': 'dnspython' # এখানে 'dns' এর বদলে 'dnspython' ইনস্টল হবে
    }
    
    for imp_name, pkg_name in dependencies.items():
        try:
            if imp_name == 'dns': __import__('dns.resolver')
            else: __import__(imp_name)
        except ImportError:
            # venv এর ভেতর থাকলে --user ছাড়া ইনস্টল করার চেষ্টা করবে
            try:
                # --break-system-packages যোগ করা হয়েছে যাতে Kali/Debian এ সমস্যা না হয়
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name, "--quiet", "--break-system-packages"])
            except:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name, "--user", "--quiet", "--break-system-packages"])
                except Exception as e:
                    print(f"\033[91m[!] Manual Fix Needed: run 'pip install {pkg_name}'\033[0m")

force_load_dependencies()

import asyncio, aiohttp, json, argparse, random, re, time, urllib3, aiodns
import dns.resolver
from datetime import datetime

urllib3.disable_warnings()

# Visuals
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         [ v34.0 - POWER UNLEASHED ] • [ VENV COMPATIBLE ]{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.resolver = aiodns.DNSResolver(rotate=True, timeout=2)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8']

    async def add_to_queue(self, item, priority=10):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def fetch_source(self, session, url):
        try:
            async with session.get(url.format(domain=self.domain), timeout=12) as r:
                if r.status == 200:
                    data = await r.text()
                    matches = re.findall(r'\b(?:[a-z0-9-]+\.)+' + re.escape(self.domain) + r'\b', data, re.I)
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
                        # শুধু লাইভ রেজাল্ট প্রিন্ট হবে
                        print(f"{G}[+] {sub:<30} {B}{str(ips):<20}{W} [LIVE]")
                        self.assets[sub] = ips
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"{B}[*] Target: {self.domain} | Power: {self.threads} Threads\n" + "—"*65)
        
        sources = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://jldc.me/anubis/subdomains/{domain}",
            "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
        ]

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.threads, ssl=False)) as session:
            tasks = [self.fetch_source(session, url) for url in sources]
            results = await asyncio.gather(*tasks)
            for sub_set in results:
                for sub in sub_set: await self.add_to_queue(sub)
            
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await asyncio.gather(*workers)

        print(f"\n{Y}[!] Done. Found {len(self.assets)} unique live subdomains.{W}")

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
        print(f"\n{R}[!] Stopping...{W}")

if __name__ == "__main__":
    main()
