import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def clean_title(title):
    # Remove Result Bharat name and unwanted domain mentions
    cleaned = re.sub(r'(?i)result\s*bharat|\.com|official|archives', '', title)
    cleaned = re.sub(r'[\s|:-]+$', '', cleaned.strip())
    return cleaned if len(cleaned) > 5 else title

def create_custom_banner(title):
    width, height = 1200, 675
    
    # Template load ya fir custom branded background
    if os.path.exists("job_template.png"):
        img = Image.open("job_template.png").resize((width, height))
    else:
        # Dark Professional Theme
        img = Image.new("RGB", (width, height), color="#0F172A")
        draw_temp = ImageDraw.Draw(img)
        # Header Box
        draw_temp.rectangle([0, 0, width, 100], fill="#1E293B")
        draw_temp.text((50, 30), "ROJGAR UPDATE OFFICIAL", fill="#38BDF8")

    draw = ImageDraw.Draw(img)
    
    # Content Card Box
    draw.rectangle([60, 150, 1140, 525], fill="#1E293B", outline="#38BDF8", width=3)
    
    # Clean Title Text
    display_title = title[:60] + "..." if len(title) > 60 else title
    draw.text((100, 280), "NEW VACANCY / UPDATE", fill="#F59E0B")
    draw.text((100, 340), display_title, fill="#FFFFFF")
    
    # Footer Branding
    draw.rectangle([0, 585, width, height], fill="#0284C7")
    draw.text((400, 615), "Telegram: @officialrojgarupdate", fill="#FFFFFF")
    
    output_path = "final_post.png"
    img.save(output_path)
    return output_path

def send_telegram_photo(image_path, title, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    # Custom Clean Caption without Result Bharat mention
    caption = (
        f"🚨 <b>{title}</b>\n\n"
        f"📌 <b>Channel:</b> @officialrojgarupdate\n"
        f"📲 Complete Details & Apply Link 👇\n\n"
        f"🔗 <a href='{link}'>Click Here To Apply / Read Notification</a>"
    )
    
    with open(image_path, 'rb') as photo:
        resp = requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }, files={"photo": photo})
        print("Telegram API Response Status:", resp.status_code)

def scrape_and_post():
    url = "https://www.resultbharat.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            raw_title = a.text.strip()
            link = a['href']
            
            if len(raw_title) > 12 and ("http" in link or ".html" in link or "pdf" in link.lower()):
                if not link.startswith("http"):
                    link = "https://www.resultbharat.com/" + link
                
                # Filter out direct main site link
                if "resultbharat.com/index" in link or link == "https://www.resultbharat.com/":
                    continue
                
                title = clean_title(raw_title)
                banner_file = create_custom_banner(title)
                send_telegram_photo(banner_file, title, link)
                break
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
