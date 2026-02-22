#!/usr/bin/env python3
"""
AS-RECON v20.9 - Fully stable version (asrecon google.com ready)
"""

import asyncio
import aiohttp
import json
import argparse
import random
import re
import aiodns
import ssl

# Colors
C = '\033[96m'
G = '\033[92m'
Y = '\033[93m'
R = '\033[91m'
W = '\033[0m'

LOGO = f"""
{C}█████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}
    {Y}AS-RECON v20.9 - Run: asrecon google.com{W}
"""

PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json"},
    {"name": "anubis", "url": "https://jldc.me/anubis/subdomains/{domain}"},
    {"name": "alienvault", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"},
]

PERMUTATIONS = ["dev", "test", "api", "app", "stage", "prod", "admin", "beta"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=25, rate=15, depth=4, live=False):
        self.domain = domain.lower()
        self.threads = threads
        self.rate = rate
        self.depth = depth
        self.live = live
        self.assets = {}
        self.seen = set()
        self.queue = asyncio.PriorityQueue()
        self.semaphore = asyncio.Semaphore(self.rate)
        self.session = None
        self.resolver = aiodns.DNSResolver()

    async def add_to_queue(self, sub, prio=10):
        clean = sub.lower().strip()
        if clean not in self.seen and clean.endswith(self.domain) and clean != self.domain:
            self.seen.add(clean)
            await self.queue.put((-prio, random.random(), clean))

    async def resolve(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=3)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except:
            return []

    async def fetch_source(self, src):
        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    print(f"{Y}{src['name']} → HTTP {resp.status}{W}")
                    return set()

                text = await resp.text()
                subs = set()

                if src["name"] == "crtsh":
                    try:
                        data = json.loads(text)
                        for entry in data:
                            nv = entry.get("name_value", "")
                            if nv:
                                for line in nv.split("\n"):
                                    clean = line.strip().lower().lstrip("*.")
                                    if clean.endswith(self.domain) and clean != self.domain:
                                        subs.add(clean)
                    except:
                        pass

                elif src["name"] == "anubis":
                    try:
                        data = json.loads(text)
                        for item in data:
                            if isinstance(item, str):
                                clean = item.lower().rstrip(".").lstrip("*.")
                                if clean.endswith(self.domain) and clean != self.domain:
                                    subs.add(clean)
                    except:
                        pass

                elif src["name"] == "alienvault":
                    try:
                        data = json.loads(text)
                        for rec in data.get("passive_dns", []):
                            h = rec.get("hostname", "").lower().rstrip(".")
                            if h.endswith(self.domain) and h != self.domain:
                                subs.add(h)
                    except:
                        pass

                print(f"{G}{src['name']}: {len(subs)} subs{W}")
                return subs
        except Exception as e:
            print(f"{R}{src['name']} failed: {str(e)[:60]}{W}")
            return set()

    async def collect_passive(self):
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_subs = set()
        for res in results:
            if isinstance(res, set):
                all_subs.update(res)
        print(f"\n{G}Found {len(all_subs)} unique subdomains from passive sources{W}")
        for sub in sorted(all_subs, key=lambda x: x.count('.')):
            prio = 25 if any(k in sub for k in ['api','dev','test','prod']) else 12
            await self.add_to_queue(sub, prio)

    async def probe_live(self, sub):
        result = {"ip": [], "ports": [], "tech": [], "title": ""}
        ips = await self.resolve(sub)
        if not ips:
            return None
        result["ip"] = ips[:2]

        for port in [80, 443, 8080]:
            try:
                ssl_ctx = None
                if port == 443:
                    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE

                reader, writer = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=3)

                if port in [80, 8080]:
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    writer.write(req)
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(4096), timeout=3.5)
                    text = data.lower()

                    m = re.search(br'<title[^>]*>(.*?)</title>', data, re.I | re.S)
                    if m:
                        result["title"] = m.group(1).decode(errors='ignore').strip()[:60]

                    for tech, pat in TECH_PATTERNS.items():
                        if pat in text:
                            result["tech"].append(tech)

                result["ports"].append(port)
                writer.close()
                await writer.wait_closed()
            except:
                continue

        return result if result["ports"] else None

    async def worker(self):
        while True:
            try:
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=5)
                if sub in self.assets:
                    continue

                if self.live:
                    probe = await self.probe_live(sub)
                    if probe:
                        self.assets[sub] = probe
                        ip = probe["ip"][0] if probe["ip"] else "-"
                        ports = ",".join(map(str, probe["ports"]))
                        techs = ",".join(probe["tech"]) or "-"
                        title = probe["title"] or "-"
                        print(f"{G}{sub:<50} | {ip:<16} | ports:{ports:<10} | tech:{techs:<15} | {title}{W}")
                else:
                    ips = await self.resolve(sub)
                    if ips:
                        self.assets[sub] = {"ips": ips}

                if sub.count('.') < self.depth:
                    for pre in PERMUTATIONS:
                        await self.add_to_queue(f"{pre}.{sub}", prio=6)

            except asyncio.TimeoutError:
                if self.queue.empty():
                    break
            except Exception as e:
                print(f"{R}Error processing {sub}: {str(e)[:50]}{W}")

    async def run(self):
        print(LOGO)
        self.session = aiohttp.ClientSession()
        await self.collect_passive()

        print(f"\n{Y}Starting scan with {self.threads} workers (rate: {self.rate}){W}\n")
        tasks = [asyncio.create_task(self.worker()) for _ in range(self.threads)]

        await self.queue.join()
        for t in tasks:
            t.cancel()

        await self.session.close()

        if self.assets:
            filename = f"subs_{self.domain}.txt"
            with open(filename, "w") as f:
                for sub in sorted(self.assets):
                    f.write(sub + "\n")
            print(f"\n{G}Done! {len(self.assets)} subdomains saved → {filename}{W}")
        else:
            print(f"\n{Y}No subdomains found.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v20.9 - asrecon <domain>")
    parser.add_argument("domain", help="Target domain (example: google.com)")
    parser.add_argument("--threads", type=int, default=25, help="Number of concurrent workers")
    parser.add_argument("--rate", type=int, default=15, help="Max concurrent requests")
    parser.add_argument("--depth", type=int, default=4, help="Max permutation depth")
    parser.add_argument("--live", action="store_true", help="Probe live subdomains (IP, ports, tech)")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
