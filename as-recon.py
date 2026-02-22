#!/usr/bin/env python3
import sys
import os
import subprocess
import re

# ⚡ [ARCHITECT POWER] পারমিশন এবং মডিউল অটো-ফিক্সার
def power_setup():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    for module in required:
        try:
            __import__(module)
        except ImportError:
            try:
                # venv এর ভেতরে সাইলেন্টলি ইনস্টল করার চেষ্টা
                subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--quiet"])
            except subprocess.CalledProcessError:
                # পারমিশন এরর দিলে ইউজারকে সলিউশন বলে দেবে
                print(f"\033[91m[!] Permission Denied in /opt/as-recon/venv/\033[0m")
                print(f"\033[92m[*] Please run this once: sudo chown -R $USER:$USER /opt/as-recon/\033[0m")
                sys.exit(1)

# রান হওয়ার আগেই সব রেডি করবে
power_setup()

import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import json
import argparse
import random

# SSL warnings বন্ধ (Max Speed)
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
          {Y}AS-RECON v24.1{W} • {C}Clean Output & Auto-Permission{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=250):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.scanned = set()
        self.session = None

    async def get_http_info(self, subdomain):
        """Smart Prober: ০ বা এনএ সরাবে, শুধু কাজের রেজাল্ট দেখাবে"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=7, verify_ssl=False, allow_redirects=True) as resp:
                status = resp.status
                text = await resp.text()
                title_match = re.search(r'<title>(.*?)</title>', text, re.I)
                title = title_match.group(1).strip()[:30] if title_match else "Live"
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
                    # DNS Probing (Maximum Power)
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        # জঞ্জাল মুক্ত আউটপুট: শুধু লাইভ টার্গেট
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        # এখানে আপনার প্যাসিভ সোর্স ডাটা আসবে
        await self.queue.put((10, random.random(), self.domain))
        
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", help="Target domain")
    args = parser.parse_args()
    
    try:
        asyncio.run(ReconEngine(args.domain).run())
    except KeyboardInterrupt:
        sys.exit(0)
