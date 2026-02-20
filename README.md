# 🚀 AS-RECON v4.0 (Pro)

**AS-RECON** (Ajijul Shohan Recon) একটি শক্তিশালী এবং ডাইনামিক রিকন টুল। এটি মূলত বাগ বাউন্টি হান্টারদের জন্য তৈরি করা হয়েছে যাতে তারা দ্রুত কোনো ডোমেইনের সব ইউআরএল (URLs) খুঁজে বের করতে পারে।

---

## 🌟 ফিচারসমূহ:
- **v4.0 Pro Logic:** আগের চেয়ে অনেক দ্রুত এবং নির্ভুল।
- **Dynamic Mode:** সরাসরি টার্মিনাল ডিসপ্লেতে আউটপুট দেখার সুবিধা।
- **Save to File:** `-o` ফ্ল্যাগ ব্যবহার করে সরাসরি ফাইলে সেভ করার অপশন।
- **Native Command:** সিস্টেমের যেকোনো জায়গা থেকে শুধু `as-recon` লিখে চালানো যায়।

---

## 🛠 Installation Guide

This tool is compatible with **Kali Linux**, **Kali Nethunter**, **Parrot OS**, and **Termux**.

### 📱 For Termux Users
```bash
pkg update && pkg upgrade -y
pkg install python golang git -y
git clone [https://github.com/hakspare/as-recon](https://github.com/hakspare/as-recon)
cd as-recon
chmod +x setup.sh
./setup.sh
# Fix path for Termux
cp ~/go/bin/* $PREFIX/bin/
cp as-recon.py $PREFIX/bin/as-recon

###🐉 For Kali Linux / Nethunter / Parrot OS Users
sudo apt update && sudo apt upgrade -y
sudo apt install python3 golang git -y
git clone [https://github.com/hakspare/as-recon](https://github.com/hakspare/as-recon)
cd as-recon
chmod +x setup.sh
sudo ./setup.sh


🚀 Usage
​ইনস্টলেশন শেষ হলে যেকোনো জায়গায় টার্মিনালে লিখুন:
as-recon -d example.com 
অথবা ফাইলে সেভ করতে চাইলে:
as-recon -d example.com -o results.txt

## ⚠️ Disclaimer
এই টুলটি শুধুমাত্র **Educational Purpose** এবং **Authorized Security Testing** এর জন্য তৈরি করা হয়েছে। অনুমতি ছাড়া কারো ডোমেইনে এটি ব্যবহার করা আইনত দণ্ডনীয়। এর কোনো অপব্যবহারের জন্য লেখক দায়ী থাকবেন না।

Author: Ajijul Shohan (@hakspare)
**Stay Legal, Stay Ethical! 🚀**
