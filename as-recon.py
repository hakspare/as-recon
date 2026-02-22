#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import argparse
import random
import re
import socket
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
         {Y}AS-RECON v20.7{W} • {C}Master Edition{W}
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
        self.session = None

    async def add_to_queue(self, item):
        item = item.strip().lower().lstrip("*.").rstrip(".")
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put(item)

    async def resolve_host(self, name):
        """DNS Resolution using system resolver for 100% accuracy"""
        try:
            loop = asyncio.get_event_loop()
            # Standard socket resolver - bypasses aiodns bugs
            addr_info = await loop.getaddrinfo(name, None, family=socket.AF_INET)
            ips = list(set([info[4][0] for info in addr_info]))
            return ips
        except:
            return []

    async def fetch_source(self, src):
        try:
            async with self.session.get(src["url"].format(domain=self.domain), ssl=False, timeout=15) as r:
                if r.status != 200: return set()
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
                    ips = await self.resolve_host(sub)
                    if ips:
                        self.assets[sub] = ips
                        # Real-time success output
                        print(f"{Y}[VALID]{W} {sub.ljust(30)} {G}{ips}{W}")
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
        
        q_size = self.queue.qsize()
        print(f"{G}[+] Passive Phase Complete. Queue Size: {q_size}{W}")
        
        if q_size == 0:
            print(f"{R}[!] No subdomains discovered.{W}")
            await self.session.close()
            return

        print(f"{Y}[*] Validating {q_size} subdomains using {self.threads} threads...{W}")
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        
        # Wait until everything in the queue is processed
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
    parser.add_argument("--threads", type=int, default=50) # Reduced default threads for stability
    args = parser.parse_args()
    asyncio.run(ReconEngine(args.domain, args.threads).run())

if __name__ == "__main__":
    main()
