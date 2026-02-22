#!/usr/bin/env python3
import sys
import subprocess
import importlib

# ⚡ [POWER FEATURE] Auto-Installer Logic for Users
REQUIRED_MODELS = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']

def install_missing():
    for module in REQUIRED_MODELS:
        try:
            importlib.import_name = module
            if module == 'aiodns': __import__('aiodns')
            else: __import__(module)
        except ImportError:
            # User-ke disturb na kore background-e install hobe
            subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--break-system-packages", "--quiet"])

# Background-e silent install cholbe
install_missing()

# Ekhon baki module gulo import hobe
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import json
import argparse
import random
import re
from datetime import datetime
import networkx as nx

# Disable SSL Warnings for Max Power
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

C, G, Y, R, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}
          {Y}AS-RECON v20.3{W} • {C}Auto-Setup & Max Power Mode{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=250):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.session = None

    async def get_http_info(self, subdomain):
        """Smart Prober: Powerful but Clean (No 0/NA)"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=7, verify_ssl=False, allow_redirects=True) as resp:
                status = resp.status
                text = await resp.text()
                title = re.search(r'<title>(.*?)</title>', text, re.I)
                title = title.group(1).strip()[:30] if title else "N/A"
                return status, title
        except:
            return None, None

    async def worker(self):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=3.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)

                # DNS Query & Filtered Printing
                try:
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        if status: # Power Filter: Only live assets
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        # Dummy Passive Fill (Actual code has 50+ sources)
        await self.queue.put((10, random.random(), self.domain))
        
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    args = parser.parse_args()
    asyncio.run(ReconEngine(args.domain).run())
