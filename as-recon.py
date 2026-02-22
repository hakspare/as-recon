#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [AUTO-FIX FOR ALL USERS] 
# টুলটি রান হওয়ামাত্রই মডিউল চেক করবে এবং অটো-ইনস্টল করবে
def auto_setup():
    # ইম্পোর্ট নাম : প্যাকেজ নাম
    libs = {
        "aiohttp": "aiohttp",
        "aiodns": "aiodns",
        "dns.resolver": "dnspython",
        "urllib3": "urllib3"
    }
    
    for imp_name, pkg_name in libs.items():
        try:
            if "." in imp_name:
                __import__(imp_name.split('.')[0])
            else:
                __import__(imp_name)
        except ImportError:
            # ইউজার যদি venv বা root ডিরেক্টরিতে থাকে, সরাসরি ইনস্টল ট্রাই করবে
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name, "--quiet", "--break-system-packages"])
            except:
                pass

# মডিউল ইম্পোর্ট করার আগেই অটো-সেটআপ রান হবে
auto_setup()

# এখন মডিউল লোড হবে
try:
    import asyncio, aiohttp, aiodns, json, argparse, random, re
    import dns.resolver
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    # যদি অটো-সেটআপ ফেল করে (পারমিশন এরর), তবে ইউজারকে ডিরেক্ট কমান্ড দেখাবে
    print("\033[91m[!] Dependencies missing! Run this once:\033[0m")
    print(f"\033[92msudo {sys.prefix}/bin/pip install aiohttp aiodns dnspython\033[0m")
    sys.exit(1)

# --- বাকি কোড আপনার আগের মতোই পাওয়ারফুল ---
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         [ v36.0 - AUTO-FIX EDITION ] • [ GLOBAL POWER ]{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.seen = set()
        self.resolver = aiodns.DNSResolver(rotate=True)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8']

    async def add_to_queue(self, item):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put(item)

    async def fetch(self, session, url):
        try:
            async with session.get(url.format(domain=self.domain), timeout=10) as r:
                text = await r.text()
                matches = re.findall(r'\b(?:[a-z0-9-]+\.)+' + re.escape(self.domain) + r'\b', text, re.I)
                return {m.lower().strip('.') for m in matches}
        except: return set()

    async def worker(self, session):
        while True:
            try:
                sub = await asyncio.wait_for(self.queue.get(), timeout=3)
                try:
                    res = await self.resolver.query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        print(f"{G}[+] {sub:<30} {B}{str(ips)}{W}")
                        self.assets[sub] = ips
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"{B}[*] Recon Target: {self.domain}{W}\n" + "—"*60)
        
        sources = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://jldc.me/anubis/subdomains/{domain}"
        ]

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.threads, ssl=False)) as session:
            results = await asyncio.gather(*[self.fetch(session, url) for url in sources])
            for s in results:
                for sub in s: await self.add_to_queue(sub)
            
            await asyncio.gather(*[asyncio.create_task(self.worker(session)) for _ in range(self.threads)])
        print(f"\n{G}[#] Found {len(self.assets)} live subdomains.{W}")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domain", nargs="?")
    args = parser.parse_args()
    if not args.domain:
        print(LOGO + f"\nUsage: asrecon google.com")
        sys.exit(0)
    asyncio.run(ReconEngine(args.domain).run())

if __name__ == "__main__":
    main()
