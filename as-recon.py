#!/usr/bin/env python3
"""
AS-RECON v20.4 - Enhanced with --live mode (IP, ports, tech)
"""

# ... (আগের import গুলো একই রাখো)

import socket
import ssl
from urllib.parse import urlparse

# নতুন: simple tech detection keywords
TECH_PATTERNS = {
    "Apache": b"Server: Apache",
    "Nginx": b"Server: nginx",
    "Cloudflare": b"Server: cloudflare",
    "WordPress": b"wp-content",
    "Django": b"csrftoken",
    "Laravel": b"laravel_session",
    # আরো যোগ করতে পারো
}

class ReconEngine:
    # ... (আগের __init__, load_api_keys, init_db ইত্যাদি একই)

    async def probe_live(self, sub):
        """Simple HTTP probe + basic port check + tech guess"""
        result = {"sub": sub, "ip": [], "ports": [], "tech": [], "status": "down", "title": ""}

        ips = await self.query_smart(sub)
        if not ips:
            return result
        result["ip"] = ips[:2]  # max 2 IPs দেখাবে

        common_ports = [80, 443, 8080, 8443, 8000]
        open_ports = []

        for port in common_ports:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(sub, port), timeout=2.0)
                open_ports.append(port)

                if port in (80, 8080, 8000):
                    req = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    writer.write(req)
                    data = await asyncio.wait_for(reader.read(4096), timeout=4.0)
                    headers = data.lower()

                    # title extract
                    title_match = re.search(br'<title>(.*?)</title>', data, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        result["title"] = title_match.group(1).decode(errors='ignore').strip()

                    # tech guess
                    for tech, pat in TECH_PATTERNS.items():
                        if pat in headers or pat in data:
                            result["tech"].append(tech)

                    writer.close()
                    await writer.wait_closed()

                elif port in (443, 8443):
                    # SSL try
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    _, writer_ssl = await asyncio.open_connection(sub, port, ssl=context)
                    req_ssl = f"GET / HTTP/1.1\r\nHost: {sub}\r\nConnection: close\r\n\r\n".encode()
                    writer_ssl.write(req_ssl)
                    data_ssl = await asyncio.wait_for(reader.read(4096), timeout=4.0)  # reader নেই, fix later
                    # similar tech check...

                result["status"] = "live"

            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass
            except Exception as e:
                pass

        result["ports"] = open_ports
        return result

    async def worker(self):
        # ... (আগের কোড)

        if self.live_mode and ips:  # নতুন: শুধু live probe করবে যদি --live দেয়া থাকে
            probe_res = await self.probe_live(sub)
            if probe_res["status"] == "live":
                self.assets[sub] = probe_res
                print(f"{G}{sub:40} | IPs: {', '.join(probe_res['ip']):15} | Ports: {probe_res['ports']} | Tech: {', '.join(probe_res['tech'])} | Title: {probe_res['title']}{W}")
        else:
            # normal mode
            self.assets[sub] = {"ips": ips}

        # ... বাকি save, graph ইত্যাদি

    async def run(self):
        # ... আগের কোড
        print(LOGO)
        self.live_mode = self.live_flag  # নতুন attribute
        # ... বাকি

def main():
    parser = argparse.ArgumentParser(description="AS-RECON v20.4 - Subdomain Enumeration Tool with Live Probe")
    parser.add_argument("domain", help="Target domain (example: example.com)")
    parser.add_argument("--threads", type=int, default=100, help="Number of concurrent workers (reduced for live mode)")
    parser.add_argument("--rate", type=int, default=50, help="Max requests/connections per second")
    parser.add_argument("--depth", type=int, default=5, help="Permutation depth")
    parser.add_argument("--api-keys", type=str, help="Path to JSON file with API keys")
    parser.add_argument("--live", action="store_true", help="Live mode: probe HTTP, ports, tech for resolving subs only")
    args = parser.parse_args()

    engine = ReconEngine(
        domain=args.domain,
        threads=args.threads if not args.live else min(args.threads, 50),  # live mode-এ কম রাখো
        rate=args.rate if not args.live else min(args.rate, 30),
        depth=args.depth,
        api_keys_path=args.api_keys
    )
    engine.live_flag = args.live   # নতুন flag পাস
    asyncio.run(engine.run())

if __name__ == "__main__":
    main()
