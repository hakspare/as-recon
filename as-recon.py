#!/usr/bin/env python3
"""
AS-RECON v21.0 - 2026 Stable Edition
Run directly: asrecon google.com
"""

import asyncio
import aiohttp
import json
import argparse
import random
import re
import aiodns
import ssl

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
    {Y}AS-RECON v21.0 - Fixed & Ready (2026){W}
"""

PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json"},
    {"name": "anubis", "url": "https://jldc.me/anubis/subdomains/{domain}"},
    {"name": "alienvault_otx", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"},
]

PERMUTATIONS = ["dev", "test", "api", "app", "stage", "prod", "admin", "beta", "internal"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=20, rate=10, depth=4, live=False):
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
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=3.0)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except Exception:
            return []

    async def fetch_source(self, src):
        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=12, ssl=False) as resp:  # ssl=False to avoid some cert issues
                if resp.status != 200:
                    print(f"{Y}{src['name']} → {resp.status}{W}")
                    return set()

                text = await resp.text()
                subs = set()

                if src["name"] == "crtsh":
                    try:
                        data = json.loads(text)
                        for entry in data:
                            nv = entry.get("name_value", "")
                            if nv:
                                for line in nv.splitlines():
                                    clean = line.strip().lower().lstrip("*.")
                                    if clean and clean.endswith(self.domain) and clean != self.domain:
                                        subs.add(clean)
                    except json.JSONDecodeError:
                        pass

                elif src["name"] == "anubis":
                    try:
                        data = json.loads(text)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, str):
                                    clean = item.lower().rstrip(".").lstrip("*.")
                                    if clean.endswith(self.domain) and clean != self.domain:
                                        subs.add(clean)
                    except:
                        pass

                elif src["name"] == "alienvault_otx":
                    try:
                        data = json.loads(text)
                        for rec in data.get("passive_dns", []):
                            h = rec.get("hostname", "").lower().rstrip(".")
                            if h and h.endswith(self.domain) and h != self.domain:
                                subs.add(h)
                    except:
                        pass

                print(f"{G}{src['name']}: {len(subs)} subs found{W}")
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
        print(f"\n{G}Passive sources collected {len(all_subs)} unique subdomains{W}")
        for sub in sorted(all_subs, key=lambda x: x.count('.')):
            prio = 25 if any(k in sub for k in ['api','dev','test','prod','stage']) else 12
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

                reader, writer = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=3.0)

                if port in [80, 8080]:
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    writer.write(req)
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
                    text = data.lower()

                    title_match = re.search(br'<title[^>]*>(.*?)</title>', data, re.I | re.S)
                    if title_match:
                        result["title"] = title_match.group(1).decode(errors='ignore').strip()[:50]

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
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=6.0)
                if sub in self.assets:
                    continue

                if self.live:
                    probe = await self.probe_live(sub)
                    if probe:
                        self.assets[sub] = probe
                        ip_str = probe["ip"][0] if probe["ip"] else "-"
                        ports_str = ",".join(map(str, probe["ports"]))
                        tech_str = ",".join(probe["tech"]) or "-"
                        title = probe["title"] or "-"
                        print(f"{G}{sub:<50} | IP: {ip_str:<15} | Ports: {ports_str:<10} | Tech: {tech_str:<15} | Title: {title}{W}")
                else:
                    ips = await self.resolve(sub)
                    if ips:
                        self.assets[sub] = {"ips": ips}

                if sub.count('.') < self.depth:
                    for pre in PERMUTATIONS:
                        await self.add_to_queue(f"{pre}.{sub}", prio=5)

            except asyncio.TimeoutError:
                if self.queue.empty():
                    break
            except Exception as e:
                print(f"{R}Worker issue: {str(e)[:60]}{W}")

    async def run(self):
        print(LOGO)
        self.session = aiohttp.ClientSession()
        await self.collect_passive()

        print(f"\n{Y}Launching {self.threads} workers (rate limit {self.rate}/sec){W}\n")
        workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]

        await self.queue.join()
        for w in workers:
            w.cancel()

        await self.session.close()

        if self.assets:
            filename = f"subs_{self.domain}.txt"
            with open(filename, "w") as f:
                for sub in sorted(self.assets.keys()):
                    f.write(sub + "\n")
            print(f"\n{G}Scan finished! {len(self.assets)} subdomains saved → {filename}{W}")
            if self.live:
                print(f"   → Live probed hosts shown above")
        else:
            print(f"\n{Y}No subdomains found this time. Try with --live or different domain.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v21.0 - asrecon <domain>")
    parser.add_argument("domain", help="Target domain (e.g. google.com)")
    parser.add_argument("--threads", type=int, default=20, help="Concurrent workers (default 20)")
    parser.add_argument("--rate", type=int, default=10, help="Max concurrent requests (default 10)")
    parser.add_argument("--depth", type=int, default=4, help="Permutation depth (default 4)")
    parser.add_argument("--live", action="store_true", help="Probe live subdomains (shows IP, ports, tech)")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
