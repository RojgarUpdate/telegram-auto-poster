import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

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

def create_branded_banner(title):
    width, height = 1280, 720
    
    # Load template image
    if os.path.exists("job_template.png"):
        img = Image.open("job_template.png").convert("RGB").resize((width, height))
    else:
        img = Image.new("RGB", (width, height), color="#092B5A")
        
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font_title = font_body = ImageFont.load_default()

    # Title Alignment (Top Right Header)
    display_title = title[:40] + "..." if len(title) > 40 else title
    draw.text((450, 48), display_title.upper(), fill="#092B5A", font=font_title)
    
    # Template Boxes Text Placement (X, Y Coordinates)
    draw.text((560, 205), "LATEST VACANCY", fill="#092B5A", font=font_body)
    draw.text((560, 260), "CHECK NOTIFICATION", fill="#092B5A", font=font_body)
    
    draw.text((540, 415), "VARIOUS POSTS", fill="#092B5A", font=font_body)
    draw.text((540, 495), "UPDATED TODAY", fill="#092B5A", font=font_body)
    draw.text((540, 575), "CHECK DETAILS BELOW", fill="#092B5A", font=font_body)
    draw.text((540, 655), "OFFICIAL WEBSITE", fill="#092B5A", font=font_body)

    output_path = "final_post.png"
    img.save(output_path)
    return output_path

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

def scrape_and_post():
    url = "https://www.resultbharat.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            raw_title = a.text.strip()
            rb_page_link = a['href'].strip()
            
            if len(raw_title) > 12 and (".html" in rb_page_link or "pdf" in rb_page_link.lower()):
                if not rb_page_link.startswith("http"):
                    rb_page_link = "https://www.resultbharat.com/" + rb_page_link
                
                if "resultbharat.com/index" in rb_page_link or rb_page_link == "https://www.resultbharat.com/":
                    continue
                
                title = re.sub(r'(?i)result\s*bharat|main site|\.com', '', raw_title).strip()
                if not title:
                    continue
                
                final_link = get_official_or_fallback_link(rb_page_link)
                banner_file = create_branded_banner(title)
                send_telegram_photo(banner_file, title, final_link)
                break
                
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
