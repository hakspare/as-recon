#!/usr/bin/env python3
import sys
import os
import subprocess

# ⚡ [PRISON BREAK] venv-এর বাধা ডিঙিয়ে মডিউল লোড করা
def global_power_fix():
    required = ['aiohttp', 'aiodns', 'networkx', 'requests', 'urllib3', 'dns']
    
    # ইউজার সাইট-প্যাকেজ পাথ ম্যানুয়ালি ইনজেক্ট করা (venv বাইপাস)
    import site
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.append(user_site)

    for m in required:
        try:
            if m == 'dns': __import__('dns.resolver')
            else: __import__(m)
        except ImportError:
            # venv-এর ভেতর `--user` কাজ না করলে আমরা সরাসরি pip install চালাবো
            # এবং venv isolation ভেঙে ফেলবো
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", m, "--quiet", "--break-system-packages"])
            except:
                # যদি তাতেও না হয়, ইউজার লেভেলে ট্রাই করবে
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", m, "--user", "--quiet", "--break-system-packages"])
                except: pass

global_power_fix()

# এখন মডিউলগুলো ইম্পোর্ট হবে কোনো ঝামেলা ছাড়াই
try:
    import asyncio, aiohttp, json, argparse, random, re, time, urllib3, aiodns
    import dns.resolver
    from datetime import datetime
except ImportError as e:
    print(f"\033[91m[!] Missing dependency: {e}. Please run: pip install aiohttp aiodns dnspython\033[0m")
    sys.exit(1)

urllib3.disable_warnings()

# Visuals
C, G, Y, R, M, W, B = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[95m', '\033[0m', '\033[1m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         [ PRISON BREAK EDITION ] • [ NO-ERROR RECON ]{W}
"""

class ReconEngine:
    def __init__(self, args):
        self.domain = args.domain.lower()
        self.threads = args.threads
        self.depth = args.depth
        self.queue = asyncio.PriorityQueue()
        self.assets = {}
        self.scanned = set()
        self.seen = set()
        self.resolver = aiodns.DNSResolver(rotate=True, timeout=2)
        self.resolver.nameservers = ['1.1.1.1', '8.8.8.8', '9.9.9.9']

    async def add_to_queue(self, item, priority=10):
        if item and item not in self.seen and item.endswith(self.domain):
            self.seen.add(item)
            await self.queue.put((-priority, random.random(), item))

    async def fetch_api(self, session, name, url):
        try:
            async with session.get(url.format(domain=self.domain), timeout=15) as r:
                if r.status == 200:
                    data = await r.text()
                    matches = re.findall(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+' + re.escape(self.domain) + r'\b', data, re.I)
                    return {m.lower().strip('.') for m in matches}
        except: pass
        return set()

    async def probe_http(self, session, sub):
        for proto in ['http', 'https']:
            try:
                async with session.get(f"{proto}://{sub}", timeout=4, verify_ssl=False) as r:
                    text = await r.text()
                    title = re.search(r'<title>(.*?)</title>', text, re.I)
                    title = title.group(1).strip()[:25] if title else "No Title"
                    server = r.headers.get('Server', 'Web')
                    return r.status, title, server
            except: continue
        return None, None, None

    async def worker(self, session):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=4.0)
                if sub in self.scanned: continue
                self.scanned.add(sub)
                
                try:
                    res = await self.resolver.query(sub, 'A')
                    ips = [r.host for r in res]
                    if ips:
                        status, title, server = await self.probe_http(session, sub)
                        if status:
                            print(f"{G}[+] {sub:<30} {B}{str(ips):<18}{W} [{status}] [{C}{title}{W}]")
                            self.assets[sub] = {"ips": ips, "status": status}
                            # Recursive
                            if sub.count('.') - self.domain.count('.') < self.depth:
                                for p in ["api", "dev", "v1"]: await self.add_to_queue(f"{p}.{sub}", 30)
                except: pass
            except asyncio.TimeoutError: break

    async def run(self):
        print(LOGO)
        print(f"{B}[*] Target: {self.domain} | Threads: {self.threads} | Depth: {self.depth}\n" + "—"*75)
        
        sources = {
            "Crtsh": "https://crt.sh/?q=%.{domain}&output=json",
            "Anubis": "https://jldc.me/anubis/subdomains/{domain}",
            "Alienvault": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
            "Archive": "http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey"
        }

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.threads, ssl=False)) as session:
            tasks = [self.fetch_api(session, name, url) for name, url in sources.items()]
            results = await asyncio.gather(*tasks)
            for sub_set in results:
                if sub_set:
                    for sub in sub_set: await self.add_to_queue(sub, 20)
            
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await asyncio.gather(*workers)

        print(f"\n{G}[#] Total Assets: {len(self.assets)}{W}")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-d", "--domain", help="Target domain")
    parser.add_argument("-t", "--threads", type=int, default=300)
    parser.add_argument("-x", "--depth", type=int, default=2)
    parser.add_argument("-h", "--help", action="help")
    
    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == '-h'):
        print(LOGO)
        print(f"{Y}Usage: asrecon -d google.com{W}\n")
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    if not args.domain and len(sys.argv) > 1:
        args.domain = sys.argv[1] # আগের মতো সরাসরি ডোমেইন সাপোর্ট

    try:
        asyncio.run(ReconEngine(args).run())
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
