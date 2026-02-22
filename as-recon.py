#!/usr/bin/env python3
import asyncio
import aiohttp
import argparse
import re
import socket
import sys
from pathlib import Path

# Colors
C, G, Y, R, W, B, M = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[95m'

LOGO = f"""
{B}{C}  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
         {Y}AS-RECON v20.9{W} • {C}The Hunting Edition{W}
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

    async def get_live_info(self, session, url):
        """HTTP Status এবং Technology ডিটেক্ট করার ম্যাজিক"""
        try:
            async with session.get(f"http://{url}", timeout=5, ssl=False, allow_redirects=True) as resp:
                status = resp.status
                server = resp.headers.get("Server", "Unknown")
                length = resp.headers.get("Content-Length", "0")
                
                # Status Color Logic
                color = G if status == 200 else Y if status in [301, 302] else R
                return f"{color}[{status}]{W} {M}[{server}]{W} {C}[len:{length}]{W}"
        except:
            return None

    async def resolve_host(self, name):
        try:
            loop = asyncio.get_event_loop()
            addr_info = await loop.getaddrinfo(name, None, family=socket.AF_INET)
            return list(set([info[4][0] for info in addr_info]))
        except: return []

    async def fetch_source(self, session, url):
        try:
            async with session.get(url.format(domain=self.domain), ssl=False, timeout=15) as r:
                if r.status != 200: return
                content = await r.text()
                pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    sub = m.lower().lstrip("*.").rstrip(".")
                    if sub.endswith(self.domain) and sub not in self.seen:
                        self.seen.add(sub)
                        await self.queue.put(sub)
        except: pass

    async def worker(self, session):
        while True:
            sub = await self.queue.get()
            ips = await self.resolve_host(sub)
            if ips:
                live_data = ""
                if self.live:
                    info = await self.get_live_info(session, sub)
                    if info: live_data = f" {info}"
                
                if self.silent:
                    print(sub)
                else:
                    ip_info = f" {G}({','.join(ips)}){W}" if self.show_ip else ""
                    print(f"{B}[+]{W} {sub.ljust(35)}{ip_info}{live_data}")
                
                self.assets[sub] = ips
            self.queue.task_done()

    async def run(self):
        if not self.silent: print(LOGO)
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            sources = [
                "https://jldc.me/anubis/subdomains/{}",
                "https://crt.sh/?q=%.{}&output=json",
                "https://columbus.elmasy.com/api/lookup/{}",
                "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={}"
            ]
            
            if not self.silent: print(f"{Y}[*] Discovering & Probing {self.domain}...{W}\n")
            await asyncio.gather(*[self.fetch_source(session, s) for s in sources])
            
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await self.queue.join()
            for w in workers: w.cancel()

        if self.output:
            Path(self.output).write_text("\n".join(sorted(self.assets.keys())))

def main():
    parser = argparse.ArgumentParser(description="AS-RECON PRO")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Threads")
    parser.add_argument("-o", "--output", help="Save results")
    parser.add_argument("-ip", "--show-ip", action="store_true", help="Show IPs")
    parser.add_argument("-live", action="store_true", help="Show Status & Tech")
    parser.add_argument("-silent", action="store_true", help="Silent mode")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    asyncio.run(ReconEngine(args).run())

if __name__ == "__main__":
    main()
