#!/usr/bin/env python3
"""
AS-RECON v21.4 - Final Stable Version (Direct Run Ready - 2026)
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
    {Y}AS-RECON v21.4 - Direct Run: asrecon google.com{W}
"""

# শুধু এখনো কাজ করা ফ্রি সোর্স রাখা হয়েছে (error কম হবে)
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "alienvault_otx", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    # চাইলে পরে API key দিয়ে এগুলো enable করতে পারো
    # {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
    # {"name": "virustotal", "url": "https://www.virustotal.com/api/v3/domains/{domain}/subdomains", "needs_key": True},
]

PERMUTATIONS = ["dev", "test", "api", "app", "stage", "prod", "admin", "beta"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=12, rate=6, depth=4, live=False, api_keys_path=None):
        self.domain = domain.lower()
        self.threads = threads
        self.rate = rate
        self.depth = depth
        self.live = live
        self.api_keys = self.load_api_keys(api_keys_path)
        self.assets = {}
        self.seen = set()
        self.queue = asyncio.PriorityQueue()
        self.semaphore = asyncio.Semaphore(self.rate)
        self.session = None
        self.resolver = aiodns.DNSResolver()

    def load_api_keys(self, path):
        if not path or not Path(path).exists():
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except:
            print(f"{R}API keys load failed{W}")
            return {}

    async def add_to_queue(self, sub, prio=10):
        clean = sub.lower().strip()
        if clean not in self.seen and clean.endswith(self.domain) and clean != self.domain:
            self.seen.add(clean)
            await self.queue.put((-prio, random.random(), clean))

    async def resolve(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query_dns(name, 'A'), timeout=3.0)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except:
            return []

    async def fetch_source(self, src):
        url = src["url"].format(domain=self.domain)
        headers = {}
        if src["needs_key"]:
            key = self.api_keys.get(src["name"], "")
            if not key:
                print(f"{Y}Skipping {src['name']}: No API key{W}")
                return set()
            headers['X-API-Key'] = key
            headers['apikey'] = key
            headers['Authorization'] = f"Bearer {key}"

        for attempt in range(3):
            try:
                async with self.session.get(url, headers=headers, timeout=15, ssl=False) as resp:
                    if resp.status != 200:
                        print(f"{Y}{src['name']} → {resp.status} (attempt {attempt+1}){W}")
                        await asyncio.sleep(2 ** attempt)
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

                    elif src["name"] == "alienvault_otx":
                        try:
                            data = json.loads(text)
                            for rec in data.get("passive_dns", []):
                                h = rec.get("hostname", "").lower().rstrip(".")
                                if h.endswith(self.domain) and h != self.domain:
                                    subs.add(h)
                        except:
                            pass

                    print(f"{G}{src['name']}: {len(subs)} subs found{W}")
                    return subs
            except Exception as e:
                print(f"{R}{src['name']} failed (attempt {attempt+1}): {str(e)[:60]}{W}")
                await asyncio.sleep(2 ** attempt)

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

                reader, writer = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=3.0)

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
                _, _, sub = await asyncio.wait_for(self.queue.get(), timeout=6.0)
                print(f"{Y}Processing: {sub}{W}")

                if sub in self.assets:
                    continue

                ips = await self.resolve(sub)
                if not ips:
                    print(f"{Y}No IP: {sub}{W}")
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
            await self.collect_passive()

            print(f"\n{Y}Starting {self.threads} workers (rate {self.rate}/sec){W}\n")
            workers = [asyncio.create_task(self.worker()) for _ in range(self.threads)]

            await self.queue.join()
            for w in workers:
                w.cancel()

        except KeyboardInterrupt:
            print(f"\n{Y}Scan stopped by user (Ctrl+C). Saving partial results...{W}")
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
                print(f"{G}Saved {len(self.assets)} subdomains to {filename}{W}")
            else:
                print(f"{Y}No subdomains found or saved this time.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v21.4 - Run: asrecon <domain>")
    parser.add_argument("domain", help="Target domain (example: google.com)")
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--rate", type=int, default=6)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--api-keys", type=str, help="Path to API keys JSON")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live, args.api_keys)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
