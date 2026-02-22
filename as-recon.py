#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [ARCHITECT POWER] পারমিশন এবং অটো-ডিপেন্ডেন্সি ফিক্সার
def power_init():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    for module in required:
        try:
            __import__(module)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--user", "--break-system-packages", "--quiet"])
            except: pass

power_init()

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
import urllib3
from pathlib import Path

# SSL warnings বন্ধ
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
          {Y}AS-RECON v30.0{W} • {C}Ultimate God-Mode Edition{W}
"""

# [Power Up] সোর্স লিস্ট আরও মজবুত করা হয়েছে
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "alienvault", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    {"name": "anubis", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "sonar", "url": "https://sonar.omnisint.io/subdomains/{domain}", "needs_key": False},
    {"name": "columbus", "url": "https://columbus.elmasy.com/api/lookup/{domain}", "needs_key": False},
    {"name": "threatcrowd", "url": "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}", "needs_key": False}
]

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.resolver = aiodns.DNSResolver(rotate=True, timeout=4)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']

    async def add_to_queue(self, item, priority=10):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def fetch_source(self, src):
        """Passive Intelligence Gathering"""
        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=15) as r:
                if r.status == 200:
                    data = await r.text()
                    pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                    matches = re.findall(pattern, data, re.IGNORECASE)
                    subs = {m.lower().strip('.') for m in matches if m.lower().endswith(self.domain)}
                    print(f"{G}[S] {src['name']}: {len(subs)} found{W}")
                    return subs
        except: return set()

    async def get_http_info(self, sub):
        """Ultra-Fast Prober: No Junk, Only Live Assets"""
        try:
            async with self.session.get(f"http://{sub}", timeout=5, allow_redirects=True, verify_ssl=False) as r:
                text = await r.text()
                title = re.search(r'<title>(.*?)</title>', text, re.I)
                title = title.group(1).strip()[:30] if title else "Live"
                return r.status, title
        except: return None, None

    async def worker(self):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=5.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)

                try:
                    # DNS রেজোলিউশন (Maximum Power)
                    res = await self.resolver.query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        if status: # শুধু লাইভ রেজাল্ট দেখাবে
                            print(f"{G}[+] {sub:<35} {str(ips):<25} [{status}] [{title}]{W}")
                            self.assets[sub] = {"ips": ips, "status": status, "title": title}
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"[*] Target: {self.domain} | Power Mode: {self.threads} Threads\n")
        
        timeout = aiohttp.ClientTimeout(total=20)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        # ১. প্যাসিভ সোর্স থেকে ডেটা নেওয়া
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks)
        for sub_set in results:
            for sub in sub_set: await self.add_to_queue(sub, 20)

        # ২. ওয়ার্কার স্টার্ট করা (Probing Phase)
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        
        await self.session.close()
        print(f"\n{Y}[!] Recon Complete. Total Active Subs: {len(self.assets)}{W}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("-t", "--threads", type=int, default=300)
    args = parser.parse_args()
    
    try:
        asyncio.run(ReconEngine(args.domain, args.threads).run())
    except KeyboardInterrupt:
        print(f"\n{R}[!] Aborted.{W}")
