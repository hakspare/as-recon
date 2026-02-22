#!/usr/bin/env python3
import sys
import os
import subprocess
import importlib

# ⚡ [ARCHITECT SELF-HEAL] ইউজারকে কিছু করতে হবে না, টুল নিজেই সব ফিক্স করবে
def auto_setup():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        # ইউজারকে ডিস্টার্ব না করে সাইলেন্টলি ইনস্টল হবে
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--user", "--break-system-packages", "--quiet"])
        except:
            # যদি তাতেও না হয়, ইউজারকে শুধু একবার বলবে sudo দিতে
            os.system(f"sudo pip install {' '.join(missing)} --break-system-packages --quiet")

# টুল রান হওয়া মাত্রই সেটআপ চেক করবে
auto_setup()

# এখন মেইন ইমপোর্টগুলো হবে
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import json
import argparse
import random
import re

# SSL warnings বন্ধ (Max Power)
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
          {Y}AS-RECON v23.0{W} • {C}Zero-Config Power Mode{W}
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
        """Clean Output Prober: ০ বা এনএ সরাবে, পাওয়ার বাড়াবে"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=7, verify_ssl=False, allow_redirects=True) as resp:
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
                    # DNS রেজোলিউশন (Full Power)
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        # [SMART FILTER] শুধু লাইভ রেজাল্ট প্রিন্ট হবে
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        # এখানে আপনার ৫০+ প্যাসিভ সোর্স লোড হবে
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
