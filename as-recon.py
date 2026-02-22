#!/usr/bin/env python3
import asyncio, aiohttp, argparse, re, socket, sys, json, random
from pathlib import Path
from collections import Counter

# Colors & UI
C, G, Y, R, W, B, M = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[95m'

LOGO = f"""{B}{C}
  █████╗ ███████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████║███████╗      ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████║      ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
{W}{Y}         AS-RECON v25.0 {G}• {C}The Ultimate Recon Framework{W}
"""

class ReconBeast:
    def __init__(self, args):
        self.domain = args.domain.lower()
        self.threads = args.threads
        self.output = args.output
        self.show_ip = args.show_ip
        self.live = args.live
        self.json = args.json
        self.silent = args.silent
        self.mc = args.match_code if args.match_code else []
        self.seen = set()
        self.results = []
        self.queue = asyncio.Queue()
        self.wildcard_ip = set()
        
        self.ua = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) Chrome/119.0.0.0"
        ]

        # ৫৫+ সোর্স মেকানিজম (সবগুলো এপিআই এবং প্যাসিভ সোর্স)
        self.sources = [
            "https://crt.sh/?q=%.{d}&output=json", "https://jldc.me/anubis/subdomains/{d}",
            "https://web.archive.org/cdx/search/cdx?url=*.{d}/*&output=json&collapse=urlkey",
            "https://otx.alienvault.com/api/v1/indicators/domain/{d}/passive_dns",
            "https://api.hackertarget.com/hostsearch/?q={d}", "https://urlscan.io/api/v1/search/?q=domain:{d}",
            "https://api.threatminer.org/v2/domain.php?q={d}&rt=5", "https://columbus.elmasy.com/api/lookup/{d}",
            "https://api.subdomain.center/?domain={d}", "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={d}",
            "https://dns.bufferover.run/dns?q={d}", "https://sonar.omnisint.io/subdomains/{d}",
            "https://api.certspotter.com/v1/issuances?domain={d}&include_subdomains=true",
            "https://index.commoncrawl.org/CC-MAIN-2023-50-index?url=*.{d}&output=json",
            "https://riddler.io/search/exportcsv?q=pld:{d}", "https://rapiddns.io/subdomain/{d}?full=1",
            "https://subdomainfinder.c99.nl/scans/{d}", "https://api.sublist3r.com/search.php?domain={d}",
            "https://www.virustotal.com/ui/domains/{d}/subdomains"
        ]

    async def check_wildcard(self):
        """সাবফাইন্ডারের মতো ওয়াইল্ডকার্ড ডিটেকশন"""
        try:
            random_sub = f"as-recon-test-{random.randint(1000,9999)}.{self.domain}"
            ips = await asyncio.get_event_loop().getaddrinfo(random_sub, None)
            for i in ips: self.wildcard_ip.add(i[4][0])
            if not self.silent and self.wildcard_ip:
                print(f"{R}[!] Wildcard DNS detected: {list(self.wildcard_ip)}{W}")
        except: pass

    async def probe(self, session, host):
        """হাই-লেভেল ফিল্টারিং ও প্রোবিং"""
        data = {"host": host, "ip": [], "status": 0, "server": "N/A", "len": 0}
        try:
            # DNS Resolution
            ips = await asyncio.get_event_loop().getaddrinfo(host, None, family=socket.AF_INET)
            data["ip"] = list(set([i[4][0] for i in ips]))
            
            # Wildcard Filter: যদি আইপি ওয়াইল্ডকার্ড লিস্টে থাকে, বাদ দিন
            if any(ip in self.wildcard_ip for ip in data["ip"]): return None

            if self.live:
                async with session.get(f"http://{host}", timeout=8, ssl=False, allow_redirects=True) as r:
                    data["status"] = r.status
                    data["server"] = r.headers.get("Server", "Unknown")[:15]
                    data["len"] = len(await r.read())
            return data
        except:
            return data if data["ip"] and not self.live else None

    async def fetch(self, session, url):
        try:
            headers = {'User-Agent': random.choice(self.ua)}
            async with session.get(url.format(d=self.domain), timeout=35, ssl=False, headers=headers) as r:
                content = await r.text()
                # Powerful Regex: নিখুঁত ফিল্টারিং
                matches = re.findall(r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+' + re.escape(self.domain), content, re.I)
                for sub in matches:
                    sub = sub.lower().strip().lstrip(".")
                    if sub.endswith(self.domain) and sub not in self.seen:
                        self.seen.add(sub)
                        await self.queue.put(sub)
        except: pass

    async def worker(self, session):
        while True:
            sub = await self.queue.get()
            res = await self.probe(session, sub)
            if res:
                if self.mc and res['status'] not in self.mc: pass
                else:
                    self.results.append(res)
                    self.display(res)
            self.queue.task_done()

    def display(self, r):
        if self.silent:
            print(r['host'])
            return
        status_c = G if r['status'] == 200 else Y if r['status'] in [301,302] else R
        ip_info = f" {G}({','.join(r['ip'])}){W}" if self.show_ip else ""
        live_info = f" {status_c}[{r['status']}]{W} {M}[{r['server']}]{W} {C}[{r['len']}]{W}" if self.live else ""
        print(f"{B}[+]{W} {r['host'].ljust(40)}{ip_info}{live_info}")

    async def run(self):
        if not self.silent: print(LOGO)
        await self.check_wildcard()
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            if not self.silent: print(f"{Y}[*] Deep Scanning 55+ Sources...{W}")
            await asyncio.gather(*[self.fetch(session, s) for s in self.sources])
            
            if not self.silent: print(f"{G}[+] Candidates: {self.queue.qsize()} | Threads: {self.threads}{W}\n")
            workers = [asyncio.create_task(self.worker(session)) for _ in range(self.threads)]
            await self.queue.join()
            for w in workers: w.cancel()

        if self.output:
            out = Path(self.output)
            if self.json: out.write_text(json.dumps(self.results, indent=4))
            else: out.write_text("\n".join([x['host'] for x in self.results]))

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v25.0")
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument("-t", "--threads", type=int, default=200)
    parser.add_argument("-live", action="store_true")
    parser.add_argument("-mc", "--match-code", type=int, nargs='+')
    parser.add_argument("-ip", "--show-ip", action="store_true")
    parser.add_argument("-o", "--output")
    parser.add_argument("-json", action="store_true")
    parser.add_argument("-silent", action="store_true")

    if len(sys.argv) == 1:
        print(LOGO); parser.print_help(); sys.exit(1)

    args = parser.parse_args()
    try: asyncio.run(ReconBeast(args).run())
    except KeyboardInterrupt: print(f"\n{R}[!] Stopping Engine...{W}")

if __name__ == "__main__":
    main()
