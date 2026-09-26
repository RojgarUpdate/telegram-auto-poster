import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def send_telegram_photo(image_path, caption, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    caption_text = f"📢 <b>{caption}</b>\n\n🔗 <a href='{link}'>Click Here for Details</a>"
    
    with open(image_path, 'rb') as photo:
        resp = requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "HTML"
        }, files={"photo": photo})
        print("Telegram Photo API Status:", resp.status_code, resp.text)

def send_telegram_text(caption, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = f"📢 <b>{caption}</b>\n\n🔗 <a href='{link}'>Click Here for Details</a>"
    resp = requests.post(url, json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    })
    print("Telegram Text API Status:", resp.status_code, resp.text)

def process_and_post(title, link):
    banner_sent = False
    
    # Try sending with Template Image
    if os.path.exists("job_template.png"):
        try:
            template = Image.open("job_template.png")
            draw = ImageDraw.Draw(template)
            draw.text((360, 80), title[:45], fill="#0A192F")
            
            output_path = "final_banner.png"
            template.save(output_path)
            send_telegram_photo(output_path, title, link)
            banner_sent = True
        except Exception as e:
            print(f"Banner creation failed, falling back to text: {e}")
            
    # Fallback to Text if Banner fails
    if not banner_sent:
        send_telegram_text(title, link)

def scrape_and_post():
    url = "https://www.resultbharat.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            title = a.text.strip()
            link = a['href']
            
            if len(title) > 12 and ("http" in link or ".html" in link or "pdf" in link.lower()):
                if not link.startswith("http"):
                    link = "https://www.resultbharat.com/" + link
                
                print(f"Processing: {title}")
                process_and_post(title, link)
                break
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
