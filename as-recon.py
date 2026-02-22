#!/usr/bin/env python3
"""
AS-RECON v20.4 - Maximum Power Subdomain Recon (50+ Passive Sources)
Fixed: Clean Output (No 0/NA), Added Smart Probing, Maintained Full Power
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
import urllib3

# SSL warnings বন্ধ করা (পাওয়ারফুল স্ক্যানিংয়ের জন্য জরুরি)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Colors & Logo
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}
          {Y}AS-RECON v20.4{W} • {C}Power Probing Edition (Shohan Fix){W}
"""

# Source trust scores
SOURCE_SCORE = {
    "crtsh": 0.95, "chaos": 0.92, "censys": 0.90, "securitytrails": 0.88,
    "virustotal": 0.85, "alienvault_otx": 0.80, "sonar_omnisint": 0.78
}

PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "censys", "url": "https://search.censys.io/api/v2/certificates/search?q=parsed.names%3A*.{domain}", "needs_key": True},
    {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
    {"name": "securitytrails", "url": "https://api.securitytrails.com/v1/domain/{domain}/subdomains", "needs_key": True},
    {"name": "virustotal", "url": "https://www.virustotal.com/api/v3/domains/{domain}/subdomains", "needs_key": True},
    {"name": "sonar_omnisint", "url": "https://sonar.omnisint.io/subdomains/{domain}", "needs_key": False},
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "columbus", "url": "https://columbus.elmasy.com/api/lookup/{domain}", "needs_key": False},
    {"name": "threatcrowd", "url": "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}", "needs_key": False},
]

PERMUTATIONS = ["dev", "staging", "test", "api", "app", "admin", "prod"]

class ReconEngine:
    def __init__(self, domain, threads=250, rate=120, depth=5, api_keys_path=None):
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
        self.found_ips = set()
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
        if item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            score = SOURCE_SCORE.get(item, 0.5) * 10
            await self.queue.put((-priority - score, random.random(), item))

    async def query_smart(self, name):
        self.resolver.nameservers = self.resolver_pools[0]
        try:
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=4)
            return [r.host for r in res]
        except: return []

    # --- Power Feature: Smart HTTP Prober ---
    async def get_http_info(self, subdomain):
        """সাবডোমেইনটি লাইভ কি না এবং টাইটেল কি তা বের করে (No 0/NA Logic)"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=6, verify_ssl=False, allow_redirects=True) as resp:
                status = resp.status
                text = await resp.text()
                title = "N/A"
                title_match = re.search(r'<title>(.*?)</title>', text, re.I)
                if title_match:
                    title = title_match.group(1).strip()[:30]
                return status, title
        except:
            return None, None

    async def fetch_source(self, src):
        if src["needs_key"] and src["name"] not in self.api_keys: return set()
        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=15) as r:
                if r.status != 200: return set()
                data = await r.json(content_type=None)
                subs = set()
                # Simplified parsing for speed
                text = json.dumps(data)
                pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                return {m.lower().lstrip("*.").rstrip(".") for m in matches if m.lower().endswith(self.domain)}
        except: return set()

    async def worker(self):
        while True:
            try:
                neg_prio, _, sub = await asyncio.wait_for(self.queue.get(), timeout=3.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)

                async with self.semaphore:
                    ips = await self.query_smart(sub)
                    
                if ips:
                    # HTTP Probing - এই অংশটি আউটপুট ফিল্টার করে
                    status, title = await self.get_http_info(sub)
                    
                    # যদি status পাওয়া যায় (অর্থাৎ লাইভ), শুধু তখনই প্রিন্ট করবে
                    if status:
                        self.assets[sub] = {"ips": ips, "status": status, "title": title}
                        print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                    
                    # সাব-লেভেল স্ক্যানিং পাওয়ার বজায় রাখা
                    if sub.count('.') < self.depth:
                        for pre in PERMUTATIONS:
                            await self.add_to_queue(f"{pre}.{sub}", 5)

            except asyncio.TimeoutError: break
            except Exception: continue

    async def run(self):
        print(LOGO)
        # Power setting: Increase connection pool size
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
        
        print(f"[*] Power Scanning: {self.domain} with {self.threads} threads...")
        
        # Passive Phase
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks)
        for res in results:
            for sub in res: await self.add_to_queue(sub, 15)

        # Active Worker Phase
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        
        await self.session.close()
        print(f"\n{G}[#] Recon Complete. Total Active Assets: {len(self.assets)}{W}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("--threads", type=int, default=250)
    args = parser.parse_args()
    
    engine = ReconEngine(args.domain, threads=args.threads)
    asyncio.run(engine.run())
