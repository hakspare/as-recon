#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [GOD MODE SETUP] কোনো এরর বা পারমিশন ইস্যু টিকবে না
def ultimate_power_fix():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3']
    
    # [1] Virtual Environment এর দেওয়াল ভেঙে প্যাকেজ পাথ ইনজেক্ট করা
    user_site = os.path.expanduser("~/.local/lib/python3.13/site-packages")
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

    # [2] অটো-ফিক্স লজিক (No Alert, No Sudo required)
    for module in required:
        try:
            __import__(module)
        except ImportError:
            try:
                # সিস্টেমে থাকা মেইন পাইথন ব্যবহার করে ফোর্স ইনস্টল
                subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--quiet", "--no-warn-script-location"])
            except:
                # যদি venv ব্লক করে, তবে PIP এর ইনজেকশন ব্যবহার করবে
                os.system(f"{sys.executable} -m pip install {module} --quiet")

# টুল স্টার্ট হওয়ার আগেই ইঞ্জিন রেডি
ultimate_power_fix()

# এখন ইম্পোর্ট হবে কোনো এরর ছাড়াই
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import re
import argparse
import random

# SSL warnings বন্ধ (Power Maximize)
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
          {Y}AS-RECON v26.0{W} • {C}100% Auto-Fix & Maximum Power{W}
"""

class ReconEngine:
    def __init__(self, domain, threads=300): # পাওয়ার বাড়িয়ে ৩০০ থ্রেড করা হয়েছে
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.scanned = set()
        self.session = None

    async def get_http_info(self, subdomain):
        """Smart Prober: জঞ্জালমুক্ত সলিড রেজাল্ট"""
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=8, verify_ssl=False, allow_redirects=True) as resp:
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
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=4.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                try:
                    res = await aiodns.DNSResolver().query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title = await self.get_http_info(sub)
                        # জঞ্জাল ফিল্টার: শুধু কাজ করে এমন টার্গেট দেখাবে
                        if status:
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        
        # প্যাসিভ সোর্স ডাটা (পাওয়ার মেইনটেইনড)
        await self.queue.put((10, random.random(), self.domain))
        
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]
        await asyncio.gather(*workers)
        await self.session.close()
        print(f"\n{G}[#] Recon Done. Power Scan Complete.{W}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", nargs="?", help="Target Domain")
    parser.add_argument("-d", "--target", help="Alternative Target Flag")
    args = parser.parse_args()
    
    target = args.domain if args.domain else args.target
    if not target:
        print(f"{R}[!] Usage: asrecon google.com{W}")
        sys.exit(1)
        
    try:
        asyncio.run(ReconEngine(target).run())
    except KeyboardInterrupt:
        sys.exit(0)
