#!/usr/bin/env python3
import sys
import os
import re
import argparse
import random

# ⚡ [POWER CHECK] কোনো এরর ছাড়াই সলিড চেক
def check_dependencies():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        # জঞ্জালমুক্ত পরিষ্কার মেসেজ
        print(f"\033[91m[!] Missing: {', '.join(missing)}\033[0m")
        print(f"\033[92m[*] Run this once to fix everything: \033[1msudo pip install {' '.join(missing)} --break-system-packages\033[0m")
        sys.exit(1)

# রান করার আগেই চেক
check_dependencies()

# এখন সব পাওয়ারফুল লাইব্রেরি ইম্পোর্ট
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import networkx as nx

# SSL warnings বন্ধ (Probing Speed বাড়াতে)
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
          {Y}AS-RECON v27.0{W} • {C}Ultimate Power (Full Fix){W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300):
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
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=4.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                try:
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        # জঞ্জাল ফিল্টার: শুধু লাইভ টার্গেট প্রিন্ট হবে
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        # প্যাসিভ সোর্স (Full Power)
        await self.queue.put((10, random.random(), self.domain))
        
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", nargs="?")
    args = parser.parse_args()
    
    if not args.domain:
        print(f"{R}[!] Usage: asrecon google.com{W}")
        sys.exit(1)
        
    try:
        asyncio.run(ReconEngine(args.domain).run())
    except KeyboardInterrupt:
        sys.exit(0)
