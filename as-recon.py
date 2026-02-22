#!/usr/bin/env python3
"""
AS-RECON v20.4 - Ultra-Stable & Accurate Edition
Fixes: SSL Errors, Result Accuracy, DNS Deprecation
"""

import asyncio
import aiohttp
import json
import argparse
import random
import re
import gc
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
         {Y}AS-RECON v20.3{W} • {C}Ultra-Stable Edition{W}
"""

SOURCE_SCORE = {
    "crtsh": 0.95, "chaos": 0.92, "censys": 0.90, "securitytrails": 0.88,
    "virustotal": 0.85, "sonar_omnisint": 0.78, "anubisdb": 0.75
}

PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "sonar_omnisint", "url": "https://sonar.omnisint.io/subdomains/{domain}", "needs_key": False},
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "columbus", "url": "https://columbus.elmasy.com/api/lookup/{domain}", "needs_key": False},
    {"name": "threatcrowd", "url": "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}", "needs_key": False},
    {"name": "circl_lu", "url": "https://www.circl.lu/pdns/query/{domain}", "needs_key": False}
]

PERMUTATIONS = ["dev", "staging", "api", "app", "admin", "prod", "vpn", "internal"]

class ReconEngine:
    def __init__(self, domain, threads=250, rate=120, depth=3, api_keys_path=None):
        self.domain = domain.lower()
        self.threads = threads
        self.rate = rate
        self.depth = depth
        self.api_keys = self.load_api_keys(api_keys_path)
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.queue = asyncio.PriorityQueue()
        self.wildcard_ips = set()
        self.graph = nx.DiGraph()
        self.resolver = aiodns.DNSResolver(rotate=True)
        self.resolver_pools = [['1.1.1.1', '1.0.0.1'], ['8.8.8.8', '8.8.4.4']]
        self.resolver_health = {p[0]: {'success': 1.0, 'latency': 0.1} for p in self.resolver_pools}
        self.semaphore = asyncio.Semaphore(self.rate)
        self.session = None
        self.db = sqlite3.connect(f"asrecon_{self.domain}.db")
        self.init_db()

    def load_api_keys(self, path):
        if not path or not Path(path).exists(): return {}
        with open(path) as f: return json.load(f)

    def init_db(self):
        c = self.db.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS results (sub TEXT PRIMARY KEY, data TEXT, updated TEXT)')
        self.db.commit()

    async def add_to_queue(self, item, priority=10):
        item = item.strip().lower().lstrip("*.")
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            score_boost = SOURCE_SCORE.get(item.split('.')[0], 0.5) * 5
            await self.queue.put((-priority - score_boost, random.random(), item))

    async def query_smart(self, name, rtype='A'):
        for pool in self.resolver_pools:
            self.resolver.nameservers = pool
            try:
                res = await asyncio.wait_for(self.resolver.query(name, rtype), timeout=4)
                return [r.host if hasattr(r, 'host') else str(r) for r in res]
            except: continue
        return []

    async def detect_wildcard(self):
        test_sub = f"wildcard{random.randint(100,999)}.{self.domain}"
        ips = await self.query_smart(test_sub)
        if ips:
            self.wildcard_ips = set(ips)
            print(f"{Y}[!] Wildcard detected: {self.wildcard_ips}{W}")

    async def fetch_source(self, src):
        url = src["url"].format(domain=self.domain)
        try:
            # SSL False added to bypass certificate errors
            async with self.session.get(url, timeout=15, ssl=False) as r:
                if r.status != 200: return set()
                data = await r.json() if 'json' in r.headers.get('content-type', '') else await r.text()
                
                subs = set()
                text_data = str(data)
                pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                matches = re.findall(pattern, text_data, re.IGNORECASE)
                subs = {m.lower().lstrip("*.") for m in matches if m.lower().endswith(self.domain)}
                
                print(f"{G}[+] {src['name']}: {len(subs)} found{W}")
                return subs
        except: return set()

    async def passive_phase(self):
        print(f"{Y}[*] Starting Passive Discovery...{W}")
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks)
        for res in results:
            for sub in res: await self.add_to_queue(sub, 20)
        print(f"{G}[+] Passive Phase Complete. Queue Size: {self.queue.qsize()}{W}")

    async def worker(self):
        while True:
            try:
                # Increased timeout to ensure it doesn't quit while queue is filling
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=5.0)
                
                if sub in self.scanned:
                    self.queue.task_done()
                    continue
                
                self.scanned.add(sub)
                async with self.semaphore:
                    ips = await self.query_smart(sub)

                if ips and not (self.wildcard_ips & set(ips)):
                    self.assets[sub] = {"ips": ips}
                    self.graph.add_node(sub)
                    for ip in ips: self.graph.add_edge(sub, ip)
                    
                    # Permutations for deep discovery
                    if sub.count('.') < self.depth + self.domain.count('.'):
                        for p in PERMUTATIONS:
                            await self.add_to_queue(f"{p}.{sub}", 5)

                self.queue.task_done()
            except asyncio.TimeoutError: break
            except Exception: continue

    async def run(self):
        print(LOGO)
        # Session initialized with connector to handle more concurrent requests
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        await self.detect_wildcard()
        await self.passive_phase()
        
        if self.queue.empty():
            print(f"{R}[!] No subdomains found in passive phase.{W}")
            await self.session.close()
            return

        print(f"{Y}[*] Starting Resolution & Permutation (Threads: {self.threads})...{W}")
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        
        await self.session.close()
        self.save_results()

    def save_results(self):
        print(f"\n{G}[+] Recon finished! {len(self.assets)} unique subdomains validated.{W}")
        if self.assets:
            Path(f"subs_{self.domain}.txt").write_text("\n".join(sorted(self.assets.keys())))
            nx.write_graphml(self.graph, f"graph_{self.domain}.graphml")
            print(f"{C}[i] Results saved to subs_{self.domain}.txt and graph_{self.domain}.graphml{W}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("--threads", type=int, default=100)
    args = parser.parse_args()
    engine = ReconEngine(args.domain, threads=args.threads)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
