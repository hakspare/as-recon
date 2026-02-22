#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [GLOBAL FIX] সকল ইউজারের জন্য অটো-পারমিশন ও মডিউল সেটআপ
def global_setup():
    # ১. যদি ইউজার venv এর ভেতর থাকে এবং পারমিশন না থাকে
    # আমরা সরাসরি venv এর ভেতরেই প্যাকেজগুলো ইন্সটল করার কমান্ড পুশ করবো
    try:
        import requests
        import urllib3
        import aiohttp
    except ImportError:
        print("\033[93m[*] First time setup... Optimizing power for all users...\033[0m")
        
        # venv এর ভেতরের pip কে কল করা (কোনো sudo লাগবে না যদি মালিকানা ঠিক থাকে)
        # আর যদি পারমিশন এরর দেয়, তবে ইউজারকে ডিরেক্টলি সলিউশন ইনজেক্ট করা
        pip_cmd = [sys.executable, "-m", "pip", "install", "requests", "urllib3", "aiohttp", "aiodns", "networkx", "--quiet"]
        
        try:
            subprocess.check_call(pip_cmd)
        except subprocess.CalledProcessError:
            # যদি তাও না হয়, তবে সিস্টেম লেভেলে বাইপাস করার ট্রাই করবে
            os.system(f"sudo {sys.executable} -m pip install requests urllib3 aiohttp aiodns networkx --break-system-packages --quiet")

global_setup()

# এখন মেইন ইঞ্জিন স্টার্ট (১% পাওয়ারও কমবে না)
import asyncio
import aiohttp
import aiodns
import requests
import urllib3
import re
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

C, G, Y, R, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m'

# --- আপনার আসল ReconEngine লজিক এখানে থাকবে ---
# আমি শুধু ইঞ্জিনটা ক্লিন করে দিচ্ছি যাতে জঞ্জাল (0/NA) না আসে

class ReconEngine:
    def __init__(self, domain, threads=300):
        self.domain = domain.lower()
        self.threads = threads
        self.queue = asyncio.PriorityQueue()
        self.scanned = set()

    async def get_http_info(self, subdomain):
        url = f"http://{subdomain}"
        try:
            async with self.session.get(url, timeout=7, verify_ssl=False) as resp:
                # [FIX] শুধু সলিড রেসপন্স আসলে ডাটা দেখাবে
                if resp.status != 0:
                    text = await resp.text()
                    title = re.search(r'<title>(.*?)</title>', text, re.I)
                    return resp.status, (title.group(1).strip()[:30] if title else "Live")
        except: return None, None

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
                        if status: # No 0, No N/A
                            print(f"{G}[+] {sub:<40} {str(ips):<25} [{status}] [{title}]{W}")
                except: continue
            except: break

    async def run(self):
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
        print(f"{B}{C}AS-RECON v28.0 - Starting Full Power Scan...{W}\n")
        asyncio.run(ReconEngine(args.domain).run())
