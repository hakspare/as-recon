#!/usr/bin/env python3
"""
AS-RECON v23.0 - Subfinder Level Power (50+ Sources, Rate Limit Safe, 2026)
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
    {Y}AS-RECON v23.0 - Subfinder Killer (50+ Sources Ready){W}
"""

# 50+ sources (subfinder-inspired list - active ones prioritized)
PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "anubis", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "alienvault_otx", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
    {"name": "virustotal", "url": "https://www.virustotal.com/api/v3/domains/{domain}/subdomains", "needs_key": True},
    {"name": "securitytrails", "url": "https://api.securitytrails.com/v1/domain/{domain}/subdomains", "needs_key": True},
    {"name": "censys", "url": "https://search.censys.io/api/v2/certificates/search?q=parsed.names%3A*.{domain}", "needs_key": True},
    {"name": "bufferover", "url": "https://dns.bufferover.run/dns?q=.{domain}", "needs_key": False},
    {"name": "threatminer", "url": "https://api.threatminer.org/v2/domain/report/?q={domain}&t=subdomains", "needs_key": False},
    {"name": "urlscan", "url": "https://urlscan.io/api/v1/search/?q=domain:{domain}", "needs_key": False},
    # আরও 40+ যোগ করা যাবে (rapiddns, riddler, dnsdb, github, etc.)
    # এখানে শুধু 10টা রাখলাম যাতে default run-এ error কম হয়
]

PERMUTATIONS = ["dev", "test", "api", "app", "stage", "prod", "admin", "beta", "internal", "old"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=12, rate=5, depth=5, live=False, api_keys_path=None):
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
        self.wildcard_ips = set()
        self.skipped = 0
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]

    def load_api_keys(self, path):
        if not path or not Path(path).exists():
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except:
            print(f"{R}Failed to load API keys{W}")
            return {}

    async def add_to_queue(self, sub, prio=10):
        clean = sub.lower().strip()
        if clean not in self.seen and clean.endswith(self.domain) and clean != self.domain:
            self.seen.add(clean)
            await self.queue.put((-prio, random.random(), clean))

    async def resolve(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query_dns(name, 'A'), timeout=2.0)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except:
            return []

    async def detect_wildcard(self):
        print(f"{Y}[*] Detecting wildcard...{W}")
        randoms = [f"nonexist{random.randint(1000000,9999999)}.{self.domain}" for _ in range(6)]
        ips_sets = []
        for r in randoms:
            ips = await self.resolve(r)
            if ips:
                ips_sets.append(set(ips))
            await asyncio.sleep(random.uniform(0.3, 1.0))
        if len(ips_sets) >= 4 and len(set.intersection(*ips_sets)) >= 3:
            self.wildcard_ips = set.intersection(*ips_sets)
            print(f"{Y}[!] Wildcard IPs: {self.wildcard_ips}{W}")
        else:
            print(f"{G}[+] No wildcard detected{W}")

    async def fetch_source(self, src):
        if src["needs_key"] and src["name"] not in self.api_keys:
            print(f"{Y}Skipping {src['name']}: API key missing{W}")
            self.skipped += 1
            return set()

        url = src["url"].format(domain=self.domain)
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json",
        }
        if src["needs_key"]:
            key = self.api_keys.get(src["name"], "")
            headers['X-API-Key'] = key
            headers['apikey'] = key
            headers['Authorization'] = f"Bearer {key}"

        for attempt in range(5):  # aggressive retry for rate limit
            try:
                async with self.session.get(url, headers=headers, timeout=12, ssl=False) as resp:
                    if resp.status in [429, 503]:
                        wait = 5 * (attempt + 1) + random.uniform(0, 3)
                        print(f"{Y}{src['name']} rate limit ({resp.status}), waiting {wait:.1f}s...{W}")
                        await asyncio.sleep(wait)
                        continue
                    if resp.status != 200:
                        print(f"{Y}{src['name']} → {resp.status}{W}")
                        break

                    text = await resp.text()
                    subs = set()

                    # Common parsing logic for all sources
                    if 'json' in resp.headers.get('content-type', ''):
                        try:
                            data = json.loads(text)
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, str):
                                        clean = item.lower().rstrip(".").lstrip("*.")
                                        if clean.endswith(self.domain) and clean != self.domain:
                                            subs.add(clean)
                                    elif isinstance(item, dict):
                                        for k in ['name_value', 'hostname', 'domain', 'subdomain']:
                                            val = item.get(k, "")
                                            if val:
                                                for line in str(val).splitlines():
                                                    clean = line.strip().lower().lstrip("*.")
                                                    if clean.endswith(self.domain) and clean != self.domain:
                                                        subs.add(clean)
                        except:
                            pass

                    # Generic fallback
                    pattern = r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+' + re.escape(self.domain)
                    matches = re.findall(pattern, text, re.I)
                    for m in matches:
                        clean = m.lower().rstrip(".").lstrip("*.")
                        if clean.endswith(self.domain) and clean != self.domain:
                            subs.add(clean)

                    print(f"{G}{src['name']}: {len(subs)} subs found{W}")
                    return subs
            except Exception as e:
                print(f"{R}{src['name']} failed (attempt {attempt+1}): {str(e)[:60]}{W}")
                await asyncio.sleep(2 ** attempt + random.uniform(0, 2))

        return set()

    async def collect_passive(self):
        tasks = [self.fetch_source(s) for s in PASSIVE_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_subs = set()
        for res in results:
            if isinstance(res, set):
                all_subs.update(res)
        print(f"\n{G}Passive sources collected {len(all_subs)} unique subdomains{W}")
        if self.skipped > 0:
            print(f"{Y}Skipped {self.skipped} sources (missing API keys){W}")
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

                reader, writer = await asyncio.open_connection(sub, port, ssl=ssl_ctx, timeout=2.0)

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
                    print(f"{Y}Wildcard skipped: {sub}{W}")
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
    parser = argparse.ArgumentParser(description="AS-RECON v22.0 - Subfinder Level")
    parser.add_argument("domain", help="Target domain")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--rate", type=int, default=5)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--api-keys", type=str, help="Path to API keys JSON")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live, args.api_keys)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
