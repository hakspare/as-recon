#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [GLOBAL ZERO-STEP FIX] পারমিশন বা venv-এর তোয়াক্কা করবে না
def global_power_fix():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    
    # ইউজার সাইট-প্যাকেজ পাথ ফোর্স করা (যাতে venv বাধা দিতে না পারে)
    import site
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.append(user_site)

    try:
        import requests
        import aiohttp
    except ImportError:
        # venv-এর ভেতর লিখতে না পারলে, এটি সাইলেন্টলি ইউজার লেভেলে ইন্সটল হবে
        # এখানে কোনো sudo বা /opt/ পারমিশন লাগবে না
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *required, 
            "--user", "--break-system-packages", "--quiet"
        ])
        # ইন্সটল হওয়ার পর পাথ রিফ্রেশ
        if user_site not in sys.path: sys.path.append(user_site)

# ইঞ্জিন স্টার্ট করার আগে দেওয়াল ভাঙা
global_power_fix()

import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import re
import argparse
import random

# SSL warnings বন্ধ (পাওয়ার মেইনটেইনড)
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
          {Y}AS-RECON v29.0{W} • {C}Zero-Step Universal Fix{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.scanned = set()
        self.session = None

    async def get_http_info(self, subdomain):
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=7, verify_ssl=False) as resp:
                if resp.status != 0:
                    text = await resp.text()
                    title = re.search(r'<title>(.*?)</title>', text, re.I)
                    return resp.status, (title.group(1).strip()[:30] if title else "Live")
        except: return None, None

    async def worker(self):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=4.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                try:
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        await self.queue.put((1, 1, self.domain))
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", nargs="?")
    args = parser.parse_args()
    if args.domain:
        asyncio.run(ReconEngine(args.domain).run())
