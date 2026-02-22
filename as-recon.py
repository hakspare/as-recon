#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import argparse
import random
import re
from datetime import datetime
import aiodns
import networkx as nx
from pathlib import Path

# Colors & Logo
C, G, Y, R, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
         {Y}AS-RECON v20.6{W} • {C}Master Edition{W}
"""

PASSIVE_SOURCES = [
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}"},
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json"},
    {"name": "columbus", "url": "https://columbus.elmasy.com/api/lookup/{domain}"},
    {"name": "threatcrowd", "url": "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"}
]

class ReconEngine:
    def __init__(self, domain, threads=100):
        self.domain = domain.lower()
        self.threads = threads
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.queue = asyncio.Queue()
        self.graph = nx.DiGraph()
        self.resolver = aiodns.DNSResolver(rotate=True)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']
        self.session = None

    async def add_to_queue(self, item):
        item = item.strip().lower().lstrip("*.").rstrip(".")
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put(item)

    async def query_dns(self, name):
        """ভ্যালিডেশন লজিক যা এরর মুক্ত এবং একুরেট"""
        try:
            # Modern aiodns method to fix DeprecationWarning
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=3)
            return [r.host for r in res] if res else []
        except (aiodns.error.DNSError, asyncio.TimeoutError):
            return []
        except Exception:
            return []

    async def fetch_source(self, src):
        try:
            async with self.session.get(src["url"].format(domain=self.domain), ssl=False, timeout=15) as r:
                if r.status != 200: return set()
                # Text conversion to handle both JSON and HTML
                content = await r.text()
                pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                matches = re.findall(pattern, content, re.IGNORECASE)
                subs = {m.lower().lstrip("*.") for m in matches if m.lower().endswith(self.domain)}
                print(f"{G}[+] {src['name']}: {len(subs)} found{W}")
                return subs
        except: return set()

    async def worker(self):
        while True:
            sub = await self.queue.get()
            try:
                if sub not in self.scanned:
                    self.scanned.add(sub)
                    ips = await self.query_dns(sub)
                    if ips:
                        self.assets[sub] = ips
                        self.graph.add_node(sub)
                        for ip in ips: self.graph.add_edge(sub, ip)
                        # সরাসরি টার্মিনালে পাওয়া সাবডোমেইন প্রিন্ট করবে
                        print(f"{Y}[FOUND]{W} {sub.ljust(30)} {G}{ips}{W}")
            finally:
                self.queue.task_done()

    async def run(self):
        print(LOGO)
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        
        print(f"{Y}[*] Starting Passive Discovery...{W}")
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks)
        for res in results:
            for sub in res: await self.add_to_queue(sub)
        
        print(f"{G}[+] Passive Phase Complete. Queue Size: {self.queue.qsize()}{W}")
        if self.queue.empty():
            print(f"{R}[!] No subdomains discovered.{W}")
            await self.session.close()
            return

        print(f"{Y}[*] Validating {self.queue.qsize()} subdomains using {self.threads} threads...{W}")
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        
        # কিউ শেষ না হওয়া পর্যন্ত ওয়েট করবে
        await self.queue.join()
        
        for w in workers: w.cancel()
        await self.session.close()
        
        print(f"\n{G}===================================================={W}")
        print(f"{G}[+] Recon finished! {len(self.assets)} unique subdomains validated.{W}")
        print(f"{G}===================================================={W}")
        
        if self.assets:
            output_file = f"subs_{self.domain}.txt"
            Path(output_file).write_text("\n".join(sorted(self.assets.keys())))
            print(f"{C}[*] Results saved in: {output_file}{W}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("--threads", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(ReconEngine(args.domain, args.threads).run())

if __name__ == "__main__":
    main()
