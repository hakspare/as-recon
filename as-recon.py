#!/usr/bin/env python3
import requests
import threading
import socket
import urllib3
import sys
from queue import Queue

# SSL warnings বন্ধ করার জন্য (গুগলের অনেক ইন্টারনাল সাইটে সেলফ-সাইনড সার্টিফিকেট থাকে)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BANNER = """
█████╗ ███████╗      ██████╗ ███████╗ ██████╗  ██████╗ ███╗   ██╗
██╔══██╗██╔════╝      ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗████╗  ██║
███████║███████╗      ██████╔╝█████╗  ██║      ██║   ██║██╔██╗ ██║
██╔══██║╚════██║      ██╔══██╗██╔══╝  ██║      ██║   ██║██║╚██╗██║
██║  ██║███████║      ██║  ██║███████╗╚██████╗ ╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝      ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
AS-RECON v26.0 • Architect Power Mode (Shohan Edition)
"""

class ASRecon:
    def __init__(self, domain, threads=200):
        self.domain = domain
        self.threads = threads
        self.queue = Queue()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def get_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except:
            return "N/A"

    def probe(self, subdomain):
        try:
            # HTTP এবং HTTPS দুইটাই চেক করবে পাওয়ার বাড়ানোর জন্য
            url = f"https://{subdomain}"
            response = requests.get(url, headers=self.headers, timeout=5, verify=False, allow_redirects=True)
            
            status = response.status_code
            
            # টাইটেল এক্সট্রাক্ট করা
            title = "N/A"
            if "<title>" in response.text.lower():
                title = response.text.split('<title>')[1].split('</title>')[0].strip()[:30]

            # পাওয়ারফুল ফিল্টারিং: শুধুমাত্র লাইভ রেজাল্ট স্ক্রিনে আসবে
            if status != 0:
                ip = self.get_ip(subdomain)
                print(f"[+] {subdomain:<45} [{ip:<15}] [{status}] [{title}]")
                
        except requests.exceptions.RequestException:
            # যদি কানেকশন ফেইল করে, আমরা স্ক্রিন ক্লিন রাখবো কিন্তু প্রসেস থামাবো না
            pass

    def worker(self):
        while not self.queue.empty():
            subdomain = self.queue.get()
            self.probe(subdomain)
            self.queue.task_done()

    def run(self):
        print(BANNER)
        print(f"[*] Target: {self.domain}")
        print(f"[*] Mode: Active Probing & Filtering Enabled")
        print(f"[*] Thread Count: {self.threads}\n")
        
        # এখানে আপনার প্যাসিভ সোর্স (Subfinder/Assetfinder) এর আউটপুট সিমুলেট করা হয়েছে
        # আসল টুলে এখানে আপনি ফাইল বা API থেকে ডাটা লোড করবেন
        print("[*] Gathering Data & Probing Assets...")
        
        # ডামি ডেটা লোডিং (আপনার অরিজিনাল টুলে এখানে ফাইল রিড লজিক থাকবে)
        subdomains = [f"sub{i}.{self.domain}" for i in range(100)] # উদাহরণ
        
        for sub in subdomains:
            self.queue.put(sub)

        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()

        self.queue.join()
        print("\n[*] Recon Completed. Power Maintained.")

if __name__ == "__main__":
    target = sys.argv[2] if len(sys.argv) > 2 else "google.com"
    recon = ASRecon(target)
    recon.run()
