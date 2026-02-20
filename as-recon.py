#!/usr/bin/env python3
import argparse, subprocess, os, sys, concurrent.futures, requests

# Color Codes
R, G, Y, B, C, W, D, RESET = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;36m', '\033[1;37m', '\033[1;30m', '\033[0m'

def logo():
    # 'fr' ব্যবহার করা হয়েছে যাতে ইউজারদের কোনো SyntaxWarning না দেখায়
    print(fr"""
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

def check_status(url):
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        status = response.status_code
        color = G if status == 200 else (R if status >= 400 else Y)
        print(f"{D}[{color}{status}{D}]{RESET} {url}")
        return f"[{status}] {url}"
    except: return None

def run_recon():
    parser = argparse.ArgumentParser(description="AS-RECON Pro - High Speed Recon Tool")
    parser.add_argument("-d", "--domain", help="Target domain (e.g. google.com)", required=True)
    parser.add_argument("-o", "--output", help="Save results to a file")
    parser.add_argument("-t", "--threads", help="Number of threads (Default 10)", type=int, default=10)
    parser.add_argument("-s", "--silent", help="Show only URLs", action="store_true")

    args = parser.parse_args()
    if not args.silent: logo()

    try:
        cmd = f"subfinder -d {args.domain} -silent && gau --subs {args.domain}"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        raw_urls = []
        for line in process.stdout:
            if line.strip(): raw_urls.append(line.strip())
        
        unique_urls = list(set(raw_urls))
        if not args.silent: print(f"{B}[INFO]{RESET} Found {Y}{len(unique_urls)}{RESET} unique URLs. Checking status...")

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_url = {executor.submit(check_status, url): url for url in unique_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                if res: results.append(res)

        if args.output:
            with open(args.output, "w") as f:
                for line in results: f.write(line + "\n")
            print(f"\n{G}[SUCCESS]{RESET} Results saved in: {args.output}")

    except KeyboardInterrupt:
        print(f"\n{R}[!] Stopped by user.{RESET}")
        sys.exit()

if __name__ == "__main__":
    run_recon()
