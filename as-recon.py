#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys

# Color codes for professional output
R = '\033[1;31m' # Red
G = '\033[1;32m' # Green
Y = '\033[1;33m' # Yellow
B = '\033[1;34m' # Blue
C = '\033[1;36m' # Cyan
W = '\033[1;37m' # White
D = '\033[1;30m' # Dark Gray
RESET = '\033[0m'

def logo():
    # Minimalist & Professional ASCII Art (Won't break on mobile)
    # This design is slim and high-tech
    print(f"""
{C}    ___   _____        ____  __________  ______  _   __
{C}   /   | / ___/       / __ \/ ____/ __ \/ ____/ / | / /
{C}  / /| | \__ \______ / /_/ / __/ / / / / /   /  |/ / 
{C} / ___ |___/ /_____// _, _/ /___/ /_/ / /___/ /|  /  
{C}/_/  |_/____/      /_/ |_/_____/\____/\____/_/ |_/   
{D}                                             v4.0-Pro
{D}--------------------------------------------------------
{W}   Author  : {G}@hakspare (Ajijul Shohan)
{W}   Purpose : {G}Fast URL & Subdomain Reconnaissance
{D}--------------------------------------------------------{RESET}
    """)

def run_recon():
    parser = argparse.ArgumentParser(description="AS-RECON by AJIJUL SHOHAN")
    parser.add_argument("-d", "--domain", help="Target domain (e.g. example.com)", required=True)
    parser.add_argument("-o", "--output", help="Save output to a file")

    # If no arguments are passed, show help
    if len(sys.argv) == 1:
        logo()
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    domain = args.domain
    output_file = args.output

    logo()

    print(f"{B}[INFO]{RESET} Starting reconnaissance for: {G}{domain}{RESET}")
    print(f"{D}--------------------------------------------------------{RESET}")

    try:
        # Combining powerful recon tools (Ensure these are installed via setup.sh)
        # Using waybackurls and gau as an example
        cmd = f"waybackurls {domain} && gau --subs {domain}"
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        urls = []
        
        # Live output display with a sleek arrow
        for line in process.stdout:
            url = line.strip()
            if url:
                urls.append(url)
                if not output_file:
                    print(f"{G}➔{RESET} {url}")

        # Wait for process to finish and handle results
        process.communicate()

        # Unique URL processing
        unique_urls = sorted(list(set(urls)))

        if output_file:
            with open(output_file, "w") as f:
                for u in unique_urls:
                    f.write(u + "\n")
            print(f"\n{G}[SUCCESS]{RESET} Total {Y}{len(unique_urls)}{RESET} unique URLs saved to: {C}{output_file}{RESET}")
        else:
            print(f"\n{G}[SUCCESS]{RESET} Found {Y}{len(unique_urls)}{RESET} unique URLs.")

    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopped by user.{RESET}")
        sys.exit()
    except Exception as e:
        print(f"\n{R}[!] Unexpected Error: {e}{RESET}")

if __name__ == "__main__":
    run_recon()
