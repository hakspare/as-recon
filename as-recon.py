#!/usr/bin/env python3
"""
AS-RECON v21.5 - Final Fixed Version (Direct Run + Clean Output)
"""

import asyncio
import aiohttp
import json
import argparse
import random
import re
import aiodns
import ssl
import time
from pathlib import Path
from datetime import datetime

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
    {Y}AS-RECON v21.5 - Direct Run Ready (asrecon google.com){W}
"""

# শুধু reliable ফ্রি সোর্স (rate limit কম)
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
]

PERMUTATIONS = ["dev", "test", "api", "app", "stage", "prod", "admin", "beta"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=10, rate=5, depth=4, live=False):
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
        self.wildcard_ips = set()

    async def add_to_queue(self, sub, prio=10):
        clean = sub.lower().strip()
        if clean not in self.seen and clean.endswith(self.domain) and clean != self.domain:
            self.seen.add(clean)
            await self.queue.put((-prio, random.random(), clean))

    async def resolve(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query_dns(name, 'A'), timeout=2.5)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except:
            return []

    async def detect_wildcard(self):
        print(f"{Y}[*] Detecting wildcard...{W}")
        randoms = [f"nonexist{random.randint(1000000,9999999)}.{self.domain}" for _ in range(5)]
        ips_sets = []
        for r in randoms:
            ips = await self.resolve(r)
            if ips:
                ips_sets.append(set(ips))
        if len(ips_sets) >= 3 and len(set.intersection(*ips_sets)) >= 2:
            self.wildcard_ips = set.intersection(*ips_sets)
            print(f"{Y}[!] Wildcard IPs detected: {self.wildcard_ips}{W}")
        else:
            print(f"{G}[+] No wildcard detected{W}")

    async def fetch_source(self, src):
        url = src["url"].format(domain=self.domain)
        for attempt in range(3):
            try:
                async with self.session.get(url, timeout=15, ssl=False) as resp:
                    if resp.status != 200:
                        print(f"{Y}{src['name']} → {resp.status} (attempt {attempt+1}){W}")
                        await asyncio.sleep(1.5 ** attempt)
                        continue

                    text = await resp.text()
                    subs = set()

                    if src["name"] == "crtsh":
                        try:
                            data = json.loads(text)
                            for entry in data:
                                names = entry.get("name_value", "").splitlines()
                                for n in names:
                                    n = n.strip().lower().lstrip("*.")
                                    if n.endswith(self.domain) and n != self.domain:
                                        subs.add(n)
                        except:
                            pass

                    elif src["name"] == "anubisdb":
                        try:
                            data = json.loads(text)
                            if isinstance(data, list):
                                for s in data:
                                    if isinstance(s, str):
                                        clean = s.lower().rstrip(".").lstrip("*.")
                                        if clean.endswith(self.domain) and clean != self.domain:
                                            subs.add(clean)
                        except:
                            pass

                    print(f"{G}{src['name']}: {len(subs)} subs found{W}")
                    return subs
            except Exception as e:
                print(f"{R}{src['name']} failed (attempt {attempt+1}): {str(e)[:60]}{W}")
                await asyncio.sleep(1.5 ** attempt)

        return set()

    async def collect_passive(self):
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_subs = set()
        for res in results:
            if isinstance(res, set):
                all_subs.update(res)
        print(f"\n{G}Passive sources collected {len(all_subs)} unique subdomains{W}")
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
                ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) if port == 443 else None
                if ssl_ctx:
                    ssl_ctx.check_hostname = False
                    ssl_ctx.verify_mode = ssl.CERT_NONE

                reader, writer = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=2.5)

                if port in [80, 8080]:
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    writer.write(req)
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
                    text = data.lower()

                    m = re.search(br'<title[^>]*>(.*?)</title>', data, re.I | re.S)
                    if m:
                        result["title"] = m.group(1).decode(errors='ignore').strip()[:50]

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
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=5.0)
                print(f"{Y}Processing: {sub}{W}")

                if sub in self.assets:
                    continue

                ips = await self.resolve(sub)
                if not ips:
                    print(f"{Y}No IP: {sub}{W}")
                    continue

                if self.wildcard_ips & set(ips):
                    print(f"{Y}Wildcard match skipped: {sub}{W}")
                    continue

                print(f"{G}Resolved: {sub} → {', '.join(ips[:2])}{W}")

                if self.live:
                    probe = await self.probe_live(sub)
                    if probe:
                        self.assets[sub] = probe
                        ip_str = probe["ip"][0] if probe["ip"] else "-"
                        ports = ",".join(map(str, probe["ports"]))
                        techs = ",".join(probe["tech"]) or "-"
                        title = probe["title"] or "-"
                        print(f"{G}{sub:<50} | IP: {ip_str:<15} | Ports: {ports:<10} | Tech: {techs:<15} | {title}{W}")
                else:
                    self.assets[sub] = {"ips": ips}

                if sub.count('.') < self.depth:
                    for pre in PERMUTATIONS:
                        await self.add_to_queue(f"{pre}.{sub}", prio=5)

            except asyncio.TimeoutError:
                if self.queue.empty():
                    break
            except Exception as e:
                print(f"{R}Worker error on {sub}: {str(e)[:60]}{W}")

    async def run(self):
        try:
            print(LOGO)
            self.session = aiohttp.ClientSession()
            await self.detect_wildcard()
            await self.collect_passive()

            print(f"\n{Y}Starting {self.threads} workers (rate {self.rate}/sec){W}\n")
            workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]

            await self.queue.join()
            for w in workers:
                w.cancel()

        except KeyboardInterrupt:
            print(f"\n{Y}Scan stopped by user. Saving partial results...{W}")
        except Exception as e:
            print(f"{R}Unexpected error: {str(e)}{W}")
        finally:
            if hasattr(self, 'session') and self.session and not self.session.closed:
                await self.session.close()
                print(f"{Y}Session closed cleanly{W}")

            if self.assets:
                filename = f"subs_{self.domain}.txt"
                with open(filename, "w") as f:
                    for sub in sorted(self.assets.keys()):
                        f.write(sub + "\n")
                print(f"{G}Finished! Saved {len(self.assets)} subdomains to {filename}{W}")
            else:
                print(f"{Y}No valid subdomains found.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v21.5 - Run: asrecon <domain>")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--rate", type=int, default=5)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
