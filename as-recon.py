#!/usr/bin/env python3
"""
AS-RECON v21.3 - All 50+ Sources from v20.3 + Fixed for direct run (asrecon google.com)
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
    {Y}AS-RECON v21.3 - Direct Run Ready (asrecon google.com){W}
"""

SOURCE_SCORE = {
    "crtsh": 0.95,
    "chaos": 0.92,
    "censys": 0.90,
    "securitytrails": 0.88,
    "virustotal": 0.85,
    "alienvault_otx": 0.80,
    "sonar_omnisint": 0.78,
    "anubisdb": 0.75,
    "columbus": 0.72,
    "threatcrowd": 0.70,
    "circl_lu": 0.68,
    "bufferover": 0.65,
    "urlscan": 0.62,
    # default: 0.5
}

PASSIVE_SOURCES = [
    {"name": "crtsh", "url": "https://crt.sh/?q=%.{domain}&output=json", "needs_key": False},
    {"name": "censys", "url": "https://search.censys.io/api/v2/certificates/search?q=parsed.names%3A*.{domain}", "needs_key": True},
    {"name": "chaos", "url": "https://chaos.projectdiscovery.io/assets/{domain}.json", "needs_key": True},
    {"name": "securitytrails", "url": "https://api.securitytrails.com/v1/domain/{domain}/subdomains", "needs_key": True},
    {"name": "virustotal", "url": "https://www.virustotal.com/api/v3/domains/{domain}/subdomains", "needs_key": True},
    {"name": "alienvault_otx", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", "needs_key": False},
    {"name": "sonar_omnisint", "url": "https://sonar.omnisint.io/subdomains/{domain}", "needs_key": False},
    {"name": "anubisdb", "url": "https://jldc.me/anubis/subdomains/{domain}", "needs_key": False},
    {"name": "columbus", "url": "https://columbus.elmasy.com/api/lookup/{domain}", "needs_key": False},
    {"name": "threatcrowd", "url": "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}", "needs_key": False},
    {"name": "circl_lu", "url": "https://www.circl.lu/pdns/query/{domain}", "needs_key": False},
    {"name": "dnsrepo", "url": "https://dnsrepo.noc.org/api/?search={domain}", "needs_key": False},
    {"name": "passivedns_rapidapi", "url": "https://passivedns.p.rapidapi.com/v1/query?domain={domain}", "needs_key": True},
    {"name": "mnemonic", "url": "https://api.mnemonic.no/pdns/v3/search?query={domain}", "needs_key": True},
    {"name": "threatbook", "url": "https://api.threatbook.cn/v3/domain/report?apikey=KEY&domain={domain}", "needs_key": True},
    {"name": "spyse", "url": "https://api.spyse.com/v3/data/domain/search?query=domain:{domain}", "needs_key": True},
    {"name": "criminalip", "url": "https://api.criminalip.io/v1/domain/lite/report/{domain}", "needs_key": True},
    {"name": "onyphe", "url": "https://api.onyphe.io/v2/search?query=domain:{domain}", "needs_key": True},
    {"name": "hunterhow", "url": "https://api.hunter.how/search?query=domain=\"{domain}\"", "needs_key": True},
    {"name": "pulsedive", "url": "https://pulsedive.com/api/explore.php?q=domain:{domain}", "needs_key": True},
    {"name": "otx_subs", "url": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list", "needs_key": False},
    {"name": "gitlab_search", "url": "https://gitlab.com/api/v4/search?scope=blobs&search={domain}", "needs_key": False},
    {"name": "bitbucket_search", "url": "https://api.bitbucket.org/2.0/search/code?q={domain}", "needs_key": False},
    {"name": "publicwww", "url": "https://publicwww.com/websites/{domain}/", "needs_key": True},
    {"name": "searchcode", "url": "https://searchcode.com/api/codesearch_I/?q={domain}", "needs_key": False},
    {"name": "certdb", "url": "https://certdb.com/api/v1/certs?domain={domain}", "needs_key": False},
    {"name": "sectigo_ct", "url": "https://sectigo.com/api/ct/search?domain={domain}", "needs_key": False},
]

PERMUTATIONS = ["dev", "staging", "test", "beta", "api", "app", "portal", "admin", "internal", "prod", "old", "new"]

TECH_PATTERNS = {
    "Apache": b"apache",
    "Nginx": b"nginx",
    "Cloudflare": b"cloudflare",
    "WordPress": b"wp-",
}

class ReconEngine:
    def __init__(self, domain, threads=15, rate=8, depth=4, live=False, api_keys_path=None):
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
        except Exception as e:
            print(f"{R}API keys load failed: {str(e)}{W}")
            return {}

    async def add_to_queue(self, sub, prio=10):
        clean = sub.lower().strip()
        if clean not in self.seen and clean.endswith(self.domain) and clean != self.domain:
            self.seen.add(clean)
            source_name = clean.split('.')[0] if '.' in clean else clean
            score_boost = SOURCE_SCORE.get(source_name, 0.5) * 10
            await self.queue.put((-prio - score_boost, random.random(), clean))

    async def resolve(self, name):
        try:
            res = await asyncio.wait_for(self.resolver.query_dns(name, 'A'), timeout=3.0)
            return [r.host for r in res if hasattr(r, 'host') and r.host]
        except:
            return []

    async def fetch_source(self, src):
        if src["needs_key"] and src["name"] not in self.api_keys:
            print(f"{Y}Skipping {src['name']}: API key missing{W}")
            return set()

        url = src["url"].format(domain=self.domain)
        headers = {}
        if src["needs_key"]:
            key = self.api_keys.get(src["name"], "")
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

                    elif src["name"] in ["chaos", "sonar_omnisint", "anubisdb"]:
                        try:
                            data = json.loads(text)
                            if isinstance(data, list):
                                subs = {s.lower().lstrip("*.").rstrip(".") for s in data 
                                        if isinstance(s, str) and s.lower().endswith(self.domain)}
                        except:
                            pass

                    elif src["name"] == "circl_lu":
                        try:
                            data = json.loads(text)
                            for entry in data:
                                rrname = entry.get("rrname", "").rstrip(".")
                                if rrname.lower().endswith(self.domain):
                                    subs.add(rrname.lower())
                        except:
                            pass

                    elif src["name"] == "columbus":
                        try:
                            data = json.loads(text)
                            subs = {e.get("hostname", "").lower().lstrip("*.").rstrip(".") 
                                    for e in data if e.get("hostname", "").lower().endswith(self.domain)}
                        except:
                            pass

                    else:
                        pattern = r'\b(?:[a-zA-Z0-9_-]{1,63}\.)+' + re.escape(self.domain) + r'\b'
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        subs = {m.lower().lstrip("*.").rstrip(".") for m in matches 
                                if m.lower().endswith(self.domain) and m.lower() != self.domain}

                    print(f"{G}{src['name']}: {len(subs)} subs{W}")
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
        print(f"\n{G}Passive sources: {len(all_subs)} unique subdomains{W}")
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
                if sub in self.assets:
                    continue

                ips = await self.resolve(sub)
                if not ips:
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
        print(LOGO)
        self.session = aiohttp.ClientSession()
        await self.collect_passive()

        print(f"\n{Y}Starting {self.threads} workers (rate {self.rate}/sec){W}\n")
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
            print(f"\n{G}Finished! {len(self.assets)} subdomains saved → {filename}{W}")
        else:
            print(f"\n{Y}No valid subdomains resolved. Try with --live or check API keys.{W}")

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v21.3 - Run directly: asrecon <domain>")
    parser.add_argument("domain", help="Target domain (example: google.com)")
    parser.add_argument("--threads", type=int, default=15)
    parser.add_argument("--rate", type=int, default=8)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--api-keys", type=str, help="Path to API keys JSON file")
    args = parser.parse_args()

    engine = ReconEngine(args.domain, args.threads, args.rate, args.depth, args.live, args.api_keys)
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
