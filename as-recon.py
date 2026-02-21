#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import argparse
import random
import sys
import sqlite3
from datetime import datetime
import aiodns
from collections import deque, defaultdict
import re
import gc
import heapq
import time
import networkx as nx

# Colors
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

# Professional ASCII Logo (আপনার দেওয়া ঠিক এটাই ব্যবহার করা হয়েছে)
LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                 
         {Y}AS-RECON v19.0{W}  •  {C}Amass-Level Subdomain Recon{W}
         {G}Passive → Hybrid → Graph | Built for Scale{W}
{W}
"""

# Passive Sources (Expanded to 10+ for realism; add more as needed)
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "alienvault", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    {"name": "bufferover", "url": "https://dns.bufferover.run/dns?q=.{domain}", "needs_key": False},
    {"name": "urlscan", "url": "https://urlscan.io/api/v1/search/?q=domain:{domain}", "needs_key": False},
    {"name": "certspotter", "url": "https://api.certspotter.com/v1/issuances?domain={domain}", "needs_key": False},
    {"name": "riddler", "url": "https://riddler.io/search/exportcsv?q=pld:{domain}", "needs_key": False},
    {"name": "virustotal", "url": "https://www.virustotal.com/api/v3/domains/{domain}/subdomains", "needs_key": True},
    {"name": "securitytrails", "url": "https://api.securitytrails.com/v1/domain/{domain}/subdomains", "needs_key": True},
    {"name": "netlas", "url": "https://app.netlas.io/api/responses/?q=domain:{domain}", "needs_key": True},
    {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
]

# Permutations for active generation
PERMUTATIONS = ["dev", "staging", "test", "beta", "api", "app", "portal", "admin", "internal", "prod", "old", "new"]

class ReconEngine:
    def __init__(self, domain, threads=200, rate=100, depth=5, api_keys=None):
        self.domain = domain.lower()
        self.threads = threads
        self.rate = rate
        self.depth = depth
        self.api_keys = api_keys or {}
        self.assets = {}
        self.scanned = set()
        self.wildcard_ips = set()
        self.queue = []  # Priority queue
        self.seen = set()
        self.found_ips = set()
        self.found_asns = set()
        self.graph = nx.DiGraph()
        self.resolver_pools = [
            ['1.1.1.1', '1.0.0.1'],
            ['8.8.8.8', '8.8.4.4'],
            ['9.9.9.9', '149.112.112.112'],
            ['208.67.222.222', '208.67.220.220'],
        ]
        self.resolver_health = {pool[0]: {'success': 1.0, 'latency': 0.1} for pool in self.resolver_pools}
        self.resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop(), rotate=True)
        self.session = None
        self.semaphore = asyncio.Semaphore(rate)
        self.db_conn = sqlite3.connect(f"asrecon_{domain}.db")
        self._init_db()
        self.load_checkpoint()

    def _init_db(self):
        c = self.db_conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS assets (sub TEXT PRIMARY KEY, data TEXT)')
        self.db_conn.commit()

    def add_to_queue(self, item, priority=10):
        if item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            heapq.heappush(self.queue, (-priority, random.random(), item))

    async def query_smart(self, name, rtype='A'):
        sorted_pools = sorted(self.resolver_pools, key=lambda p: self.resolver_health[p[0]]['success'] / (self.resolver_health[p[0]]['latency'] or 0.1), reverse=True)
        for pool in sorted_pools:
            start = time.time()
            self.resolver.nameservers = pool
            try:
                res = await self.resolver.query(name, rtype)
                latency = time.time() - start
                health = self.resolver_health[pool[0]]
                health['success'] = (health['success'] * 0.9) + 0.1
                health['latency'] = (health['latency'] * 0.9) + (latency * 0.1)
                return res
            except:
                health['success'] = (health['success'] * 0.9)
        return None

    async def detect_wildcard(self):
        fake_subs = [f"nonexist-{random.randint(100000,999999)}.{self.domain}" for _ in range(3)]
        ips_sets = []
        for fs in fake_subs:
            res = await self.query_smart(fs, 'A')
            if res:
                ips_sets.append({r.host for r in res})
        if ips_sets and len(set.intersection(*ips_sets)) > 0:
            self.wildcard_ips = set.intersection(*ips_sets)
            print(f"{Y}[!] Wildcard IPs detected: {self.wildcard_ips}{W}")
        else:
            self.wildcard_ips = set()

    async def fetch_and_parse(self, src):
        if src["needs_key"] and not self.api_keys.get(src["name"]):
            print(f"{Y}[!] Skipping {src['name']}: API key required{W}")
            return set()
        url = src["url"].format(domain=self.domain)
        headers = {}
        if src["needs_key"]:
            headers['Authorization'] = f"Bearer {self.api_keys[src['name']]}"  # adjust as per API
        try:
            async with self.session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    return set()
                content_type = resp.headers.get('content-type', '').lower()
                if 'json' in content_type:
                    data = await resp.json(content_type=None)
                else:
                    data = await resp.text()

                subs = set()
                text = json.dumps(data) if isinstance(data, (dict, list)) else data
                SUB_RE = re.compile(r'(?:[\w*-]+\.)+' + re.escape(self.domain), re.IGNORECASE)
                for match in SUB_RE.finditer(text):
                    sub = match.group(0).lower().lstrip('*.').rstrip('.')
                    if sub.endswith(self.domain) and sub != self.domain:
                        subs.add(sub)

                # Source-specific parsing
                if src["name"] == "crtsh" and isinstance(data, list):
                    for entry in data:
                        names = entry.get("name_value", "").splitlines()
                        for n in names:
                            n = n.strip().lower().lstrip('*.')
                            if n.endswith(self.domain) and n != self.domain:
                                subs.add(n)
                elif src["name"] == "alienvault" and isinstance(data, dict):
                    for record in data.get("passive_dns", []):
                        hostname = record.get("hostname", "").lower()
                        if hostname.endswith(self.domain) and hostname != self.domain:
                            subs.add(hostname)

                print(f"{G}[+] {src['name']}: Found {len(subs)} subdomains{W}")
                return subs
        except Exception as e:
            print(f"{R}[-] {src['name']} failed: {e}{W}")
            return set()

    async def passive_seed(self):
        tasks = [self.fetch_and_parse(src) for src in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_subs = set()
        for res in results:
            if isinstance(res, set):
                all_subs.update(res)
        for sub in sorted(all_subs, key=lambda x: x.count('.')):
            prio = 20 if any(k in sub for k in ['api', 'dev', 'stage', 'prod']) else 15
            self.add_to_queue(sub, priority=prio)
        print(f"{G}[+] Total passive subdomains seeded: {len(all_subs)}{W}")

    async def worker(self):
        while self.queue:
            async with self.semaphore:
                neg_prio, _, sub = heapq.heappop(self.queue)
                prio = -neg_prio
                if sub in self.scanned:
                    continue
                self.scanned.add(sub)

                res = await self.query_smart(sub, 'A')
                if not res:
                    continue

                ips = [r.host for r in res]
                if self.wildcard_ips and not self.wildcard_ips.isdisjoint(set(ips)):
                    print(f"{Y}[!] Skipping wildcard: {sub}{W}")
                    continue

                self.assets[sub] = {"ips": ips}
                self.graph.add_node(sub, type="subdomain")
                for ip in ips:
                    self.found_ips.add(ip)
                    self.graph.add_edge(sub, ip, type="resolves_to")

                if prio >= 10 and sub.count('.') < self.depth:
                    for pre in PERMUTATIONS:
                        new_sub = f"{pre}.{sub}"
                        self.add_to_queue(new_sub, priority=prio - 3)

                if len(self.scanned) % 500 == 0:
                    self.save_checkpoint()
                    gc.collect()

    def save_checkpoint(self):
        c = self.db_conn.cursor()
        for sub, data in self.assets.items():
            c.execute("INSERT OR REPLACE INTO assets VALUES (?, ?)", (sub, json.dumps(data)))
        self.db_conn.commit()
        print(f"{Y}[+] Checkpoint saved: {len(self.assets)} assets{W}")

    def load_checkpoint(self):
        c = self.db_conn.cursor()
        try:
            c.execute("SELECT * FROM assets")
            for row in c.fetchall():
                sub, data_str = row
                self.assets[sub] = json.loads(data_str)
                self.scanned.add(sub)
                self.seen.add(sub)
            print(f"{G}[+] Loaded checkpoint: {len(self.assets)} assets{W}")
        except:
            pass

    async def run(self):
        self.session = aiohttp.ClientSession()
        await self.detect_wildcard()
        await self.passive_seed()

        if not self.queue:
            for seed in [f"www.{self.domain}", f"api.{self.domain}", f"mail.{self.domain}"]:
                self.add_to_queue(seed, priority=20)

        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)

        self.save_checkpoint()
        await self.session.close()

        print(f"{G}[+] Recon complete! Unique subdomains: {len(self.assets)}{W}")
        with open(f"subdomains_{self.domain}.txt", "w") as f:
            for sub in sorted(self.assets.keys()):
                f.write(f"{sub}\n")
        nx.write_graphml(self.graph, f"graph_{self.domain}.graphml")
        print(f"{G}[+] Output saved to subdomains_{self.domain}.txt and graph_{self.domain}.graphml{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON: Amass-Level Subdomain Recon")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--threads", type=int, default=200, help="Number of threads")
    parser.add_argument("--rate", type=int, default=100, help="Rate limit")
    parser.add_argument("--depth", type=int, default=5, help="Recursion depth")
    parser.add_argument("--api-keys", type=str, help="JSON file with API keys")
    args = parser.parse_args()

    api_keys = {}
    if args.api_keys:
        try:
            with open(args.api_keys) as f:
                api_keys = json.load(f)
        except Exception as e:
            print(f"{R}[!] Failed to load API keys: {e}{W}")

    print("\n" + "=" * 70)
    print(LOGO)
    print("=" * 70)
    print(f"  {Y}Target:{W} {args.domain}")
    print(f"  {Y}Threads:{W} {args.threads}    {Y}Rate:{W} {args.rate}/s    {Y}Depth:{W} {args.depth}")
    print("=" * 70 + "\n")

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, api_keys)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
