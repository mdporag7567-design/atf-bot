import time
import requests
import os

# ================== আপনার তথ্য ==================
BOT_TOKEN = "8890393981:AAEnDv8bE7I64Rc98rhHmeIxhc1Q8-OA1cs"
ATF_POOL_ADDRESS = "EQC0lyTIQfexMAbcL6-VZk1LDKetJ1PQGALolMjtlQi1KCvW" 

# ইউজারদের Chat ID সেভ রাখার ফাইল
SUBSCRIBERS_FILE = "subscribers.txt"
# ===============================================

last_price = None

def get_subscribers():
    """ফাইল থেকে সব ইউজারের Chat ID পড়ার ফাংশন"""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    with open(SUBSCRIBERS_FILE, "r") as f:
        ids = {line.strip() for line in f if line.strip()}
    return ids

def save_subscriber(chat_id):
    """নতুন ইউজার স্টার্ট চাপলে তার Chat ID সেভ করা"""
    subscribers = get_subscribers()
    if str(chat_id) not in subscribers:
        with open(SUBSCRIBERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")

def broadcast_message(message):
    """বট ওপেন করা সকল ইউজারকে একসাথে মেসেজ পাঠানো"""
    subscribers = get_subscribers()
    for chat_id in subscribers:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=payload, timeout=5)
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")

def check_new_users():
    """কেউ বটে এসে /start চাপলে তাকে ওয়েলকাম মেসেজ দেওয়া"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                for result in data["result"]:
                    if "message" in result and "text" in result["message"]:
                        chat_id = result["message"]["chat"]["id"]
                        text = result["message"]["text"]
                        first_name = result["message"]["chat"].get("first_name", "User")
                        
                        if text == "/start":
                            subscribers = get_subscribers()
                            if str(chat_id) not in subscribers:
                                save_subscriber(chat_id)
                                
                                # ওয়েলকাম মেসেজ
                                welcome_msg = (
                                    f"✨ *হ্যালো {first_name}! Welcome to ATF Tracker Bot* ✨\n\n"
                                    f"🤖 *আমাদের বটের সুবিধা:* \n"
                                    f"• প্রতি ১ মিনিট পর পর অটোমেটিক লাইভ ATF প্রাইস সিগন্যাল পাবেন।\n"
                                    f"• দাম বাড়ছে নাকি কমছে তা সরাসরি দেখতে পারবেন।\n\n"
                                    f"🚀 *আপনাকে সফলভাবে সিগন্যাল লিস্টে যুক্ত করা হয়েছে!*"
                                )
                                
                                welcome_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                                requests.post(welcome_url, data={
                                    "chat_id": chat_id,
                                    "text": welcome_msg,
                                    "parse_mode": "Markdown"
                                })
    except Exception as e:
        print(f"Update Check Error: {e}")

def get_atf_price():
    """GeckoTerminal API থেকে ATF টোকেনের লাইভ মূল্য নেওয়া"""
    url = f"https://api.geckoterminal.com/api/v2/networks/ton/pools/{ATF_POOL_ADDRESS}"
    headers = {'accept': 'application/json'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['data']['attributes']['base_token_price_usd'])
        else:
            return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

print("🤖 Every 1-Minute ATF Price Signal Bot চালু হচ্ছে...")

# মনিটরিং লুপ
while True:
    try:
        # ১. নতুন ইউজারদের চেক করা
        check_new_users()
# ২. লাইভ দাম চেক করা
        current_price = get_atf_price()
        
        if current_price is not None:
            # আগে কোনো প্রাইস সেভ থাকলে ট্রেন্ড চেক করবে (আপ নাকি ডাউন)
            if last_price is not None:
                if current_price > last_price:
                    status_icon = "🚀 UP"
                    bar = "🟢🟢🟢🟢🟢🟢🟢🟢"
                elif current_price < last_price:
                    status_icon = "📉 DOWN"
                    bar = "🔴🔴🔴🔴🔴🔴🔴🔴"
                else:
                    status_icon = "🔄 SAME"
                    bar = "🟡🟡🟡🟡🟡🟡🟡🟡"
            else:
                status_icon = "📊 INITIAL"
                bar = "💎💎💎💎💎💎💎💎"

            # প্রতি ১ মিনিটের সুন্দর সিগন্যাল মেসেজ
            msg = (
                f"⚡ *ATF 1-MINUTE LIVE SIGNAL* ⚡\n\n"
                f"{bar}\n"
                f"💰 *বর্তমান মূল্য:* ${current_price:.6f}\n"
                f"📈 *মার্কেট ট্রেন্ড:* {status_icon}\n"
                f"{bar}\n\n"
                f"⏱ _পরবর্তী আপডেট ১ মিনিট পর..._"
            )
            
            broadcast_message(msg)
            last_price = current_price

    except Exception as e:
        print(f"লুপে ভুল হচ্ছে: {e}")

    # ঠিক ১ মিনিট (৬০ সেকেন্ড) পর পর মেসেজ পাঠাবে
    time.sleep(60)
