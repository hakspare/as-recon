#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

G, R, C, Y, W = '\033[1;32m', '\033[1;31m', '\033[1;36m', '\033[1;33m', '\033[0m'

def logo():
    print(f"""{C}
 █████╗ ███████╗    ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝    ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
███████║███████╗    ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██║╚════██║    ██╔══██╗██╔════╝██║     ██║   ██║██║╚██╗██║
██║  ██║███████║    ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
 {G}[+] Dynamic Command Mode {Y}v4.0 (pro){W}
    """)

def run_recon():
    parser = argparse.ArgumentParser(description="AS-RECON by AJIJUL")
    parser.add_argument("domain", help="Target domain (e.g. canva.com)")
    parser.add_argument("-o", "--output", help="Save output to a file (e.g. -o sub.txt)")
    
    args = parser.parse_args()
    domain = args.domain
    output_file = args.output

    logo()
    print(f"{G}[*] Fetching URLs for: {domain}{W}")
    print(f"{Y}" + "-"*40 + f"{W}")

    try:
        cmd = f"waybackurls {domain} && gau --subs {domain}"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        urls = []
        for line in process.stdout:
            url = line.strip()
            if url:
                urls.append(url)
                if not output_file:
                    print(url)
        
        if output_file:
            unique_urls = sorted(list(set(urls)))
            with open(output_file, "w") as f:
                for u in unique_urls:
                    f.write(u + "\n")
            print(f"\n{G}[✓] Total {len(unique_urls)} unique URLs saved to: {output_file}{W}")
            
    except Exception as e:
        print(f"{R}[!] Error: {e}{W}")

if __name__ == "__main__":
    run_recon()
