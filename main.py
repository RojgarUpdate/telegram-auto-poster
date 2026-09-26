import os
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def send_telegram_message(title, link):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Error: BOT_TOKEN or CHANNEL_ID missing in repository secrets!")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"📢 <b>{title}</b>\n\n🔗 <a href='{link}'>Click Here for Details</a>"
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    resp = requests.post(url, json=payload)
    print("Telegram Response Status:", resp.status_code)
    print("Telegram Response Text:", resp.text)

def scrape_and_post():
    url = "https://www.resultbharat.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Latest job link dhoondho
        links = soup.find_all('a', href=True)
        for a in links:
            title = a.text.strip()
            link = a['href']
            
            if len(title) > 12 and ("http" in link or ".html" in link or "pdf" in link.lower()):
                if not link.startswith("http"):
                    link = "https://www.resultbharat.com/" + link
                
                print(f"Sending Post: {title} -> {link}")
                send_telegram_message(title, link)
                break
                
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
