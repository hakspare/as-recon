#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import argparse
import random
import re
import time
from datetime import datetime
import aiodns
import networkx as nx
import sqlite3
from pathlib import Path

# Colors & Logo
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
         {Y}AS-RECON v20.3{W} • {C}Bug-Free Edition{W}
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
        self.wildcard_ips = set()
        self.graph = nx.DiGraph()
        self.resolver = aiodns.DNSResolver(rotate=True)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8']
        self.session = None

    async def add_to_queue(self, item):
        item = item.strip().lower().lstrip("*.")
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put(item)

    async def query_dns(self, name):
        try:
            # Fix for DeprecationWarning
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=4)
            return [r.host for r in res]
        except:
            return []

    async def fetch_source(self, src):
        try:
            async with self.session.get(src["url"].format(domain=self.domain), ssl=False, timeout=15) as r:
                if r.status != 200: return set()
                data = await r.json() if 'json' in r.headers.get('content-type', '') else await r.text()
                pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                matches = re.findall(pattern, str(data), re.IGNORECASE)
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
                        # Optional: Print found sub in real-time
                        print(f"{C}[FOUND]{W} {sub} {G}({', '.join(ips)}){W}")
            finally:
                self.queue.task_done()

    async def run(self):
        print(LOGO)
        self.session = aiohttp.ClientSession()
        
        # Phase 1: Passive
        print(f"{Y}[*] Starting Passive Discovery...{W}")
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks)
        for res in results:
            for sub in res: await self.add_to_queue(sub)
        
        print(f"{G}[+] Passive Phase Complete. Queue Size: {self.queue.qsize()}{W}")
        if self.queue.empty():
            await self.session.close()
            return

        # Phase 2: Active Resolution
        print(f"{Y}[*] Resolving Subdomains (Threads: {self.threads})...{W}")
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        
        # Wait until the queue is fully processed
        await self.queue.join()
        
        for w in workers: w.cancel()
        await self.session.close()
        
        print(f"\n{G}[+] Recon finished! {len(self.assets)} unique subdomains validated.{W}")
        if self.assets:
            Path(f"subs_{self.domain}.txt").write_text("\n".join(sorted(self.assets.keys())))
            nx.write_graphml(self.graph, f"graph_{self.domain}.graphml")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("--threads", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(ReconEngine(args.domain, args.threads).run())

if __name__ == "__main__":
    main()
