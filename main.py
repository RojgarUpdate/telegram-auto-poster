import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WHATSAPP_LINK = "https://whatsapp.com/channel/0029VaBLUVk7oQhljhq68b1T"

def get_official_or_fallback_link(page_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(page_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            link_text = a.text.lower()
            if "resultbharat" not in href and href.startswith("http"):
                if any(kw in link_text for kw in ["apply", "official", "registration", "online", "click here", "notification"]):
                    return href
                    
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith("http") and "resultbharat" not in href:
                return href
    except Exception as e:
        print(f"Link extraction error: {e}")
        
    return WHATSAPP_LINK

def send_telegram_photo(image_path, title, final_link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    caption_text = (
        f"🚨 <b>{title}</b>\n\n"
        f"📌 <b>Telegram:</b> @officialrojgarupdate\n\n"
        f"📲 <b>Official Notification & Apply Link:</b> 👇\n"
        f"🔗 <a href='{final_link}'>Click Here To Apply / Details</a>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💚 <b>Join Our WhatsApp Channel for Daily Updates:</b>\n"
        f"👉 <a href='{WHATSAPP_LINK}'>Click Here to Join WhatsApp Channel</a>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    
    with open(image_path, 'rb') as photo:
        resp = requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "HTML"
        }, files={"photo": photo})
        print(f"Telegram API Response Status: {resp.status_code}")

def create_ctr_banner(title):
    template_w, template_h = 1080, 720
    img = Image.new("RGB", (template_w, template_h), color="#0F172A")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, template_w, 100], fill="#1E293B")
    draw.text((50, 35), "ROJGAR UPDATE (OFFICIAL)", fill="#38BDF8")

    draw.rectangle([60, 150, 1020, 520], fill="#1E293B", outline="#38BDF8", width=3)
    display_title = title[:60] + "..." if len(title) > 60 else title
    
    draw.rectangle([60, 150, 410, 210], fill="#DC2626")
    draw.text((80, 168), "URGENT JOB UPDATE", fill="#FFFFFF")

    draw.text((100, 260), "VACANCY / NOTICE DETAILS:", fill="#F59E0B")
    draw.text((100, 330), display_title, fill="#FFFFFF")

    draw.rectangle([60, 550, 500, 650], fill="#0284C7")
    draw.text((120, 585), "✅ VIEW DETAILS", fill="#FFFFFF")
    
    draw.rectangle([580, 550, 1020, 650], fill="#166534")
    draw.text((640, 585), "💻 APPLY NOW", fill="#FFFFFF")
    
    draw.text((430, 685), "@officialrojgarupdate", fill="#FFFFFF")

    output_path = "final_post.png"
    img.save(output_path)
    return output_path

def scrape_and_post():
    url = "https://www.resultbharat.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            raw_title = a.text.strip()
            rb_page_link = a['href'].strip()
            
            if len(raw_title) > 12 and (".html" in rb_page_link or "pdf" in rb_page_link.lower()):
                if not rb_page_link.startswith("http"):
                    rb_page_link = "https://www.resultbharat.com/" + rb_page_link
                
                # Filter unwanted main index pages
                if "resultbharat.com/index" in rb_page_link or rb_page_link == "https://www.resultbharat.com/":
                    continue
                
                title = re.sub(r'(?i)result\s*bharat|main site|\.com', '', raw_title).strip()
                if not title:
                    continue
                
                print(f"Processing Post: {title}")
                final_link = get_official_or_fallback_link(rb_page_link)
                banner_file = create_ctr_banner(title)
                send_telegram_photo(banner_file, title, final_link)
                break
                
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
