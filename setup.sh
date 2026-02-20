#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import concurrent.futures
import requests

# Professional Color Codes
R = '\033[1;31m' # Red
G = '\033[1;32m' # Green
Y = '\033[1;33m' # Yellow
B = '\033[1;34m' # Blue
C = '\033[1;36m' # Cyan
W = '\033[1;37m' # White
D = '\033[1;30m' # Dark Gray
RESET = '\033[0m'

def logo():
    print(f"""
{C}    ___   _____        ____  __________  ______  _   __
{C}   /   | / ___/       / __ \/ ____/ __ \/ ____/ / | / /
{C}  / /| | \__ \______ / /_/ / __/ / / / / /   /  |/ / 
{C} / ___ |___/ /_____// _, _/ /___/ /_/ / /___/ /|  /  
{C}/_/  |_/____/      /_/ |_/_____/\____/\____/_/ |_/   
{D}                                             v4.0-Pro
{D}--------------------------------------------------------
{W}   Author  : {G}@hakspare (Ajijul Shohan)
{W}   Feature : {G}Multi-threaded Status Checker
{D}--------------------------------------------------------{RESET}
    """)

# Function to check HTTP Status
def check_status(url):
    try:
        # 5 second timeout helps to keep it fast
        response = requests.get(url, timeout=5, allow_redirects=True)
        status = response.status_code
        
        if status == 200:
            color = G
        elif status >= 400:
            color = R
        else:
            color = Y
            
        print(f"{D}[{color}{status}{D}]{RESET} {url}")
        return f"[{status}] {url}"
    except:
        # If site is down or timeout
        return None

def run_recon():
    parser = argparse.ArgumentParser(description="AS-RECON Pro - High Speed Recon Tool")
    parser.add_argument("-d", "--domain", help="Target domain", required=True)
    parser.add_argument("-o", "--output", help="Save results to file")
    parser.add_argument("-t", "--threads", help="Number of threads (Default 10)", type=int, default=10)
    parser.add_argument("-s", "--silent", help="Show only URLs", action="store_true")

    if len(sys.argv) == 1:
        logo()
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    
    if not args.silent:
        logo()
        print(f"{B}[INFO]{RESET} Fetching URLs for: {G}{args.domain}{RESET}")
        print(f"{B}[INFO]{RESET} Threads: {Y}{args.threads}{RESET}")
        print(f"{D}--------------------------------------------------------{RESET}")

    try:
        # Running subfinder and gau in background
        cmd = f"subfinder -d {args.domain} -silent && gau --subs {args.domain}"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        raw_urls = []
        for line in process.stdout:
            if line.strip():
                raw_urls.append(line.strip())
        
        unique_urls = list(set(raw_urls))
        
        if not args.silent:
            print(f"{B}[INFO]{RESET} Total URLs found: {Y}{len(unique_urls)}{RESET}")
            print(f"{B}[INFO]{RESET} Checking Status Codes... (Please wait)")
            print(f"{D}--------------------------------------------------------{RESET}")

        # Multi-threading Engine
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_url = {executor.submit(check_status, url): url for url in unique_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                if res:
                    results.append(res)

        # Saving Output
        if args.output:
            with open(args.output, "w") as f:
                for line in results:
                    f.write(line + "\n")
            print(f"\n{G}[SUCCESS]{RESET} Results saved in: {C}{args.output}{RESET}")

    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopped by user.{RESET}")
        sys.exit()

if __name__ == "__main__":
    run_recon()
