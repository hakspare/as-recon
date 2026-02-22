#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [ARCHITECT POWER] পারমিশন ছাড়াই মডিউল ফিক্স করার লজিক
def super_power_fix():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        # সিস্টেম venv বা root পারমিশন ব্লক করলে এটি ইউজারের হোম ডিরেক্টরিতে সাইলেন্টলি ইন্সটল করবে
        # এতে আর sudo বা chown কমান্ড দেওয়া লাগবে না
        user_lib = os.path.expanduser("~/.local/lib/python3.13/site-packages")
        if user_lib not in sys.path:
            sys.path.append(user_lib)
            
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--user", "--break-system-packages", "--quiet"])
            print("\033[92m[*] Powering up... Initial setup completed.\033[0m")
        except:
            # যদি তাতেও সমস্যা হয়, সরাসরী কোডের ভেতর থেকে এনভায়রনমেন্ট বাইপাস করবে
            os.environ["PYTHONPATH"] = user_lib

# রান হওয়ার আগেই সব রেডি
super_power_fix()

# এরপর আপনার আসল পাওয়ারফুল লাইব্রেরি ইম্পোর্ট
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import re
import argparse
import random

# SSL warnings বন্ধ (স্ক্যানিং স্পিড বাড়াতে)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Colors & Logo
C, G, Y, R, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}
          {Y}AS-RECON v25.0{W} • {C}Auto-Fix No-Permission Mode{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=250):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.scanned = set()
        self.session = None

    async def get_http_info(self, subdomain):
        """Smart Prober: অপ্রয়োজনীয় জঞ্জাল (0/NA) সরাবে"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=6, verify_ssl=False, allow_redirects=True) as resp:
                status = resp.status
                text = await resp.text()
                title = re.search(r'<title>(.*?)</title>', text, re.I)
                title = title.group(1).strip()[:30] if title else "Live"
                return status, title
        except:
            return None, None

    async def worker(self):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=3.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                try:
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        # জঞ্জাল ফিল্টার: শুধু কাজ করে এমন রেজাল্ট আসবে
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        await self.queue.put((10, random.random(), self.domain))
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    args = parser.parse_args()
    try:
        asyncio.run(ReconEngine(args.domain).run())
    except KeyboardInterrupt:
        sys.exit(0)
