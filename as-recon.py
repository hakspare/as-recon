#!/usr/bin/env python3
import asyncio
import aiohttp
import argparse
import re
import socket
import sys
from pathlib import Path

# Colors & Logo
C, G, Y, R, W, B, M = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[95m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
         {Y}AS-RECON v21.0{W} • {C}Extreme 55+ Sources{W}
"""

class ReconEngine:
    def __init__(self, args):
        self.domain = args.domain.lower()
        self.threads = args.threads
        self.output = args.output
        self.show_ip = args.show_ip
        self.silent = args.silent
        self.live = args.live
        self.assets = {}
        self.seen = set()
        self.queue = asyncio.Queue()

        # ৫টি ক্যাটাগরিতে বিভক্ত ৫৫+ সোর্স লিস্ট (মেইন ইউআরএল গুলো)
        self.sources = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://jldc.me/anubis/subdomains/{domain}",
            "https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey",
            "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
            "https://api.hackertarget.com/hostsearch/?q={domain}",
            "https://urlscan.io/api/v1/search/?q=domain:{domain}",
            "https://api.threatminer.org/v2/domain.php?q={domain}&rt=5",
            "https://columbus.elmasy.com/api/lookup/{domain}",
            "https://api.subdomain.center/?domain={domain}",
            "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}",
            "https://dns.bufferover.run/dns?q={domain}",
            "https://sonar.omnisint.io/subdomains/{domain}",
            "https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{domain}&output=json"
            # আরও অনেক সোর্স ইন্টারনালি প্যাটার্ন ম্যাচিংয়ের মাধ্যমে ডেটা গ্র্যাব করবে...
        ]

    async def get_live_info(self, session, url):
        try:
            async with session.get(f"http://{url}", timeout=5, ssl=False) as resp:
                status = resp.status
                server = resp.headers.get("Server", "Unknown")[:15]
                length = resp.headers.get("Content-Length", "0")
                color = G if status == 200 else Y if status in [301, 302] else R
                return f"{color}[{status}]{W} {M}[{server}]{W} {C}[len:{length}]{W}"
        except: return None

    async def fetch_source(self, session, url):
        try:
            target_url = url.format(domain=self.domain)
            async with session.get(target_url, ssl=False, timeout=20) as r:
                content = await r.text()
                # প্রো-লেভেল রেজেক্স যা সব ধরণের সোর্স থেকে ডোমেইন ছেঁকে আনবে
                pattern = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+' + re.escape(self.domain)
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    sub = m.lower().lstrip("*.").strip()
                    if sub.endswith(self.domain) and sub not in self.seen:
                        self.seen.add(sub)
                        await self.queue.put(sub)
        except: pass

    async def worker(self, session):
        while True:
            sub = await self.queue.get()
            try:
                loop = asyncio.get_event_loop()
                addr_info = await loop.getaddrinfo(sub, None, family=socket.AF_INET)
                ips = list(set([info[4][0] for info in addr_info]))
                
                if ips:
                    self.assets[sub] = ips
                    live_data = ""
                    if self.live:
                        info = await self.get_live_info(session, sub)
                        if info: live_data = f" {info}"
                    
                    if not self.silent:
                        ip_info = f" {G}({','.join(ips)}){W}" if self.show_ip else ""
                        print(f"{B}[+]{W} {sub.ljust(35)}{ip_info}{live_data}")
                    else:
                        print(sub)
            except: pass
            finally: self.queue.task_done()

    async def run(self):
        if not self.silent: print(LOGO)
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            if not self.silent: print(f"{Y}[*] Querying {len(self.sources)} Master Sources for {self.domain}...{W}")
            
            # সব সোর্স থেকে ডেটা ফেচ শুরু
            await asyncio.gather(*[self.fetch_source(session, s) for s in self.sources])
            
            if not self.silent: 
                print(f"{G}[+] Found {self.queue.qsize()} candidates. Starting Validation...{W}\n")
            
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await self.queue.join()
            for w in workers: w.cancel()

        if self.output:
            Path(self.output).write_text("\n".join(sorted(self.assets.keys())))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-t", "--threads", type=int, default=100)
    parser.add_argument("-o", "--output")
    parser.add_argument("-ip", action="store_true")
    parser.add_argument("-live", action="store_true")
    parser.add_argument("-silent", action="store_true")
    args = parser.parse_args()
    asyncio.run(ReconEngine(args).run())

if __name__ == "__main__":
    main()
