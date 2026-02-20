#!/usr/bin/env python3
import argparse, subprocess, os, sys, concurrent.futures, requests

# Professional Color Codes
R, G, Y, B, C, W, D, RESET = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;36m', '\033[1;37m', '\033[1;30m', '\033[0m'

def logo():
    print(fr"""
{C}     ___    ____        ____  __________  ______  _   __
{C}    /   |  / ___/      / __ \/ ____/ __ \/ ____/ / | / /
{C}   / /| |  \__ \______/ /_/ / __/ / / / / /   /  |/ / 
{C}  / ___ | ___/ /_____/ _, _/ /___/ /_/ / /___/ /|  /  
{C} /_/  |_/____/     /_/ |_/_____/\____/\____/_/ |_/   
{D}                                             v4.0-Pro
{D}--------------------------------------------------------
{W}   Author  : {G}@hakspare (Ajijul Islam Shohan)
{W}   Feature : {G}Multi-threaded Status Checker
{D}--------------------------------------------------------{RESET}
    """)

def check_status(url):
    """Enhanced status checker that saves data even on connection issues"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # verify=False handles SSL, timeout is balanced for speed vs accuracy
        response = requests.get(url, timeout=5, allow_redirects=True, headers=headers, verify=False)
        status = response.status_code
        color = G if status == 200 else (R if status >= 400 else Y)
        print(f"{D}[{color}{status}{D}]{RESET} {url}")
        return f"[{status}] {url}"
    except requests.exceptions.RequestException:
        # If connection fails (Timeout/Refused), we still save it as [LIVE?] or [ERR]
        # This ensures your results won't show only 4 lines
        print(f"{D}[{R}ERR{D}]{RESET} {url}")
        return f"[Live/Unreachable] {url}"
    except:
        return None

def run_recon():
    parser = argparse.ArgumentParser(description="AS-RECON Pro")
    parser.add_argument("-d", "--domain", help="Target domain", required=True)
    parser.add_argument("-o", "--output", help="Save results to a file")
    parser.add_argument("-t", "--threads", help="Number of threads (Default 30)", type=int, default=30)
    parser.add_argument("-s", "--silent", help="Show only URLs", action="store_true")

    args = parser.parse_args()
    requests.packages.urllib3.disable_warnings()
    
    if not args.silent: logo()

    try:
        if not args.silent: print(f"{B}[INFO]{RESET} Fetching data for: {G}{args.domain}{RESET}...")
        
        cmd = f"subfinder -d {args.domain} -silent && gau --subs {args.domain}"
        raw_data = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        
        urls = list(set([line.strip() for line in raw_data.splitlines() if line.strip()]))
        
        if not urls:
            if not args.silent: print(f"{R}[!] No URLs found.{RESET}")
            sys.exit(0)

        if not args.silent:
            print(f"{B}[INFO]{RESET} Found {Y}{len(urls)}{RESET} unique URLs. Checking status...\n")

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_to_url = {executor.submit(check_status, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                if res:
                    results.append(res)

        if args.output:
            with open(args.output, "w") as f:
                for r in sorted(results): # Sorting results for better readability
                    f.write(r + "\n")
            if not args.silent:
                print(f"\n{G}[SUCCESS]{RESET} Total {Y}{len(results)}{RESET} results saved in: {C}{args.output}{RESET}")

    except Exception as e:
        if not args.silent: print(f"{R}[!] Error: {e}{RESET}")

if __name__ == "__main__":
    run_recon()
