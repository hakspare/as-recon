#!/usr/bin/env python3
"""
AS-RECON v20.7 - Ready for direct run: asrecon google.com
Stable 2026 edition - only working free passive sources
"""

import asyncio
import aiohttp
import json
import argparse
import random
import re
import time

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
    {Y}AS-RECON v20.7  •  asrecon google.com ready!{W}
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
    def __init__(self, domain, threads=30, rate=20, depth=4, live=False):
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
            res = await asyncio.wait_for(self.resolver.query(name, 'A'), timeout=3.5)
            return [r.host for r in res if r.host]
        except:
            return []

    async def fetch(self, src):
        url = src["url"].format(domain=self.domain)
        try:
            async with self.session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    print(f"{Y}{src['name']} → HTTP {resp.status}{W}")
                    return set()
                text = await resp.text()
                subs = set()
                if src["name"] == "crtsh":
                    try:
                        data = json.loads(text)
                        for entry in data:
                            names = entry.get("name_value", "").split("\n")
                            for n in names:
                                clean = n.strip().lower().lstrip("*.")
                                if clean.endswith(self.domain) and clean != self.domain:
                                    subs.add(clean)
                    except:
                        pass
                elif src["name"] == "anubis":
                    try:
                        data = json.loads(text)
                        subs = {s.lower().rstrip(".").lstrip("*.") for s in data if s and isinstance(s, str)}
                    except:
                        pass
                else:  # alienvault generic
                    try:
                        data = json.loads(text)
                        for rec in data.get("passive_dns", []):
                            h = rec.get("hostname", "").lower().rstrip(".")
                            if h.endswith(self.domain) and h != self.domain:
                                subs.add(h)
                    except:
                        pattern = r'[\w\.-]+\.' + re.escape(self.domain)
                        for m in re.findall(pattern, text, re.I):
                            clean = m.lower().rstrip(".")
                            if clean != self.domain:
                                subs.add(clean)
                print(f"{G}{src['name']}: {len(subs)} subs{W}")
                return subs
        except Exception as e:
            print(f"{R}{src['name']} failed: {str(e)[:50]}{W}")
            return set()

    async def collect_passive(self):
        tasks = [self.fetch(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total = set()
        for res in results:
            if isinstance(res, set):
                total.update(res)
        print(f"\n{G}Total passive subdomains: {len(total)}{W}")
        for sub in sorted(total, key=lambda x: x.count('.')):
            prio = 25 if any(k in sub for k in ['api', 'dev', 'test', 'prod']) else 12
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

                r, w = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=3)

                if port in [80, 8080]:
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    w.write(req)
                    data = b""
                    async for chunk in r:
                        data += chunk
                        if len(data) > 8192: break
                    text_low = data.lower()

                    m = re.search(br'<title>(.*?)</title>', data, re.I | re.S)
                    if m:
                        result["title"] = m.group(1).decode(errors='ignore').strip()[:60]

                    for tech, pat in TECH_PATTERNS.items():
                        if pat in text_low:
                            result["tech"].append(tech)

                result["ports"].append(port)
                w.close()
                await w.wait_closed()
            except:
                continue

        if result["ports"]:
            return result
        return None

    async def worker(self):
        while True:
            try:
                neg_p, rand, sub = await asyncio.wait_for(self.queue.get(), 4)
                if sub in self.assets:
                    continue

                if self.live:
                    probe = await self.probe_live(sub)
                    if probe:
                        self.assets[sub] = probe
                        ip1 = probe["ip"][0] if probe["ip"] else "-"
                        ports_str = ",".join(map(str, probe["ports"]))
                        tech_str = ",".join(probe["tech"]) or "-"
                        title = probe["title"] or "-"
                        print(f"{G}{sub:<55} | {ip1:<18} | ports:{ports_str:10} | tech:{tech_str:20} | {title[:35]}{W}")
                else:
                    ips = await self.resolve(sub)
                    if ips:
                        self.assets[sub] = {"ips": ips}

                if sub.count('.') < self.depth:
                    for pre in PERMUTATIONS:
                        new = f"{pre}.{sub}"
                        await self.add_to_queue(new, prio=6)

            except asyncio.TimeoutError:
                if self.queue.empty():
                    break
            except Exception as e:
                print(f"{R}Worker err: {str(e)[:40]}{W}")

    async def run(self):
        print(LOGO)
        self.session = aiohttp.ClientSession()
        await self.collect_passive()

        print(f"\n{Y}Workers starting ({self.threads} threads, rate limit {self.rate}){W}\n")
        tasks = [asyncio.create_task(self.worker()) for _ in range(self.threads)]

        await self.queue.join()
        for t in tasks:
            t.cancel()

        await self.session.close()

        if self.assets:
            out_file = f"subs_{self.domain}.txt"
            with open(out_file, "w") as f:
                for s in sorted(self.assets):
                    f.write(f"{s}\n")
            print(f"\n{G}Finished! {len(self.assets)} subdomains saved → {out_file}{W}")
        else:
            print(f"\n{Y}No valid subdomains found this run.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v20.7 - asrecon google.com")
    parser.add_argument("domain", help="Target domain (google.com)")
    parser.add_argument("--threads", type=int, default=30)
    parser.add_argument("--rate", type=int, default=20)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--live", action="store_true", help="Check live status + title/tech")
    args = parser.parse_args()

    recon = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live)
    asyncio.run(recon.run())

if __name__ == "__main__":
    main()
