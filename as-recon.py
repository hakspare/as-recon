#!/usr/bin/env python3
"""
AS-RECON v20.5 - Stable for all users • Updated 2026 sources + Live probe
Focus: Reliable free/passive sources + better error handling
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
import socket
import ssl
from urllib.parse import urlparse

# Colors
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
         {Y}AS-RECON v20.5{W} • {C}Stable & User-Friendly 2026 Edition{W}
"""

# Updated reliable sources (2026 context - mostly free/public)
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "anubis", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "alienvault_otx", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    # API key দরকার → comment out করা (optional)
    # {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
    # {"name": "censys", "url": "...", "needs_key": True},
]

PERMUTATIONS = ["dev", "staging", "test", "beta", "api", "app", "portal", "admin", "internal", "prod"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
    "Django": b"__csrftoken",
    # আরও যোগ করা যাবে
}

class ReconEngine:
    def __init__(self, domain, threads=50, rate=30, depth=4, api_keys_path=None, live=False):
        self.domain = domain.lower()
        self.threads = threads
        self.rate = rate
        self.depth = depth
        self.live = live
        self.api_keys = self.load_api_keys(api_keys_path)
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.queue = asyncio.PriorityQueue()
        self.wildcard_ips = set()
        self.session = None
        self.resolver = aiodns.DNSResolver(rotate=True)
        self.semaphore = asyncio.Semaphore(self.rate)
        self.db = sqlite3.connect(f"asrecon_{self.domain}.db")
        self.init_db()
        self.load_checkpoint()

    def load_api_keys(self, path):
        if not path or not Path(path).exists():
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except:
            print(f"{R}API keys file load failed{W}")
            return {}

    def init_db(self):
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS results (sub TEXT PRIMARY KEY, data TEXT, updated TEXT)''')
        self.db.commit()

    async def add_to_queue(self, item, priority=10):
        if item not in self.seen and item.endswith(self.domain) and item != self.domain:
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def query_smart(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=4)
            return [r.host for r in res if r.host]
        except:
            return []

    async def detect_wildcard(self):
        print(f"{Y}[*] Checking for wildcard...{W}")
        randoms = [f"randomtest{random.randint(1,999999)}.{self.domain}" for _ in range(5)]
        ips_sets = []
        for r in randoms:
            ips = await self.query_smart(r)
            if ips:
                ips_sets.append(set(ips))
        if len(ips_sets) >= 3 and len(set.intersection(*ips_sets)) > 1:
            self.wildcard_ips = set.intersection(*ips_sets)
            print(f"{Y}[!] Wildcard detected: {self.wildcard_ips}{W}")
        else:
            print(f"{G}[+] No wildcard{W}")

    async def fetch_source(self, src):
        if src["needs_key"] and src["name"] not in self.api_keys:
            print(f"{Y}Skip {src['name']}: No API key{W}")
            return set()

        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    print(f"{Y}{src['name']} → HTTP {resp.status}{W}")
                    return set()
                text = await resp.text()
                subs = set()
                if src["name"] == "crtsh":
                    try:
                        data = json.loads(text)
                        for entry in data:
                            name = entry.get("name_value", "").strip().lower().lstrip("*.")
                            if name.endswith(self.domain) and name != self.domain:
                                subs.add(name)
                    except:
                        pass
                elif src["name"] == "anubis":
                    try:
                        data = json.loads(text)
                        subs = {s.lower().rstrip(".").lstrip("*.") for s in data if isinstance(s, str) and s.lower().endswith(self.domain)}
                    except:
                        pass
                else:
                    # generic fallback
                    pattern = r'(?:[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\.)+' + re.escape(self.domain)
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    subs = {m.lower().rstrip(".").lstrip("*.") for m in matches if m.lower().endswith(self.domain) and m.lower() != self.domain}

                print(f"{G}{src['name']}: {len(subs)} subs{W}")
                return subs
        except Exception as e:
            print(f"{R}{src['name']} error: {str(e)[:60]}{W}")
            return set()

    async def passive_phase(self):
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_subs = set()
        for res in results:
            if isinstance(res, set):
                all_subs.update(res)
        print(f"{G}[+] Passive found: {len(all_subs)} unique{W}")
        for sub in sorted(all_subs):
            await self.add_to_queue(sub, priority=20 if '.' in sub else 10)

    async def probe_live(self, sub):
        result = {"ip": [], "ports": [], "tech": set(), "title": "", "status": "down"}
        ips = await self.query_smart(sub)
        if not ips:
            return None
        result["ip"] = ips[:2]

        for port in [80, 443, 8080]:
            try:
                if port == 443:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    reader, writer = await asyncio.open_connection(sub, port, ssl=ctx, timeout=3)
                else:
                    reader, writer = await asyncio.open_connection(sub, port, timeout=3)

                if port in [80, 8080]:
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n".encode()
                    writer.write(req)
                    data = b""
                    try:
                        while True:
                            chunk = await reader.read(2048)
                            if not chunk: break
                            data += chunk
                            if len(data) > 8192: break
                    except:
                        pass

                    text = data.lower()
                    if b"<title>" in data:
                        m = re.search(br'<title>(.*?)</title>', data, re.I | re.S)
                        if m:
                            result["title"] = m.group(1).decode(errors='ignore').strip()[:60]

                    for tech, pat in TECH_PATTERNS.items():
                        if pat in text:
                            result["tech"].add(tech)

                result["ports"].append(port)
                result["status"] = "live"
                writer.close()
                await writer.wait_closed()
            except:
                pass

        return result if result["status"] == "live" else None

    async def worker(self):
        while True:
            try:
                _, _, sub = await self.queue.get()
                if sub in self.scanned:
                    continue
                self.scanned.add(sub)

                async with self.semaphore:
                    ips = await self.query_smart(sub)
                if not ips or (self.wildcard_ips & set(ips)):
                    continue

                if self.live:
                    probe = await self.probe_live(sub)
                    if probe:
                        self.assets[sub] = probe
                        tech_str = ", ".join(probe["tech"]) if probe["tech"] else "-"
                        print(f"{G}{sub:<45} | {probe['ip'][0] if probe['ip'] else '-':<15} | Ports: {probe['ports']} | Tech: {tech_str} | {probe['title'][:40]}{W}")
                else:
                    self.assets[sub] = {"ips": ips}

                if sub.count('.') < self.depth:
                    for p in PERMUTATIONS:
                        await self.add_to_queue(f"{p}.{sub}", priority=8)

            except Exception as e:
                print(f"{R}Worker error on {sub}: {str(e)[:50]}{W}")
            finally:
                self.queue.task_done()

    def save_results(self):
        with open(f"subs_{self.domain}.txt", "w") as f:
            for sub in sorted(self.assets):
                f.write(f"{sub}\n")
        print(f"{G}→ Saved {len(self.assets)} subs to subs_{self.domain}.txt{W}")

    async def run(self):
        print(LOGO)
        async with aiohttp.ClientSession() as sess:
            self.session = sess
            await self.detect_wildcard()
            await self.passive_phase()

            workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
            await self.queue.join()
            for w in workers:
                w.cancel()

            self.save_results()

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v20.5 - Easy subdomain recon for everyone")
    parser.add_argument("domain", nargs="?", help="Target domain (example: google.com)")
    parser.add_argument("--threads", type=int, default=50, help="Concurrent tasks (default 50)")
    parser.add_argument("--rate", type=int, default=30, help="Max concurrent requests")
    parser.add_argument("--depth", type=int, default=4, help="Permutation depth")
    parser.add_argument("--api-keys", help="JSON file with API keys (optional)")
    parser.add_argument("--live", action="store_true", help="Probe live subdomains (IP, ports, tech)")
    args = parser.parse_args()

    if not args.domain:
        parser.print_help()
        return

    engine = ReconEngine(
        domain=args.domain,
        threads=args.threads,
        rate=args.rate,
        depth=args.depth,
        api_keys_path=args.api_keys,
        live=args.live
    )
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
