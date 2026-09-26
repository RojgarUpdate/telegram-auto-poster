import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def create_job_banner(title, post_url):
    try:
        template = Image.open("job_template.png")
        draw = ImageDraw.Draw(template)
        
        # Title text overlay on template
        draw.text((360, 80), title[:45], fill="#0A192F")
        
        output_path = "final_banner.png"
        template.save(output_path)
        send_telegram_photo(output_path, title, post_url)
    except Exception as e:
        print(f"Error creating banner: {e}")

def send_telegram_photo(image_path, caption, link):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Secrets missing!")
        return
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    caption_text = f"📢 <b>{caption}</b>\n\n🔗 <a href='{link}'>Click Here for Details</a>"
    
    with open(image_path, 'rb') as photo:
        requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "HTML"
        }, files={"photo": photo})

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
                
                create_job_banner(title, link)
                break
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
