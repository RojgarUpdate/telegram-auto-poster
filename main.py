import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Aapka Fixed WhatsApp Channel Link
WHATSAPP_LINK = "https://whatsapp.com/channel/0029VaBLUVk7oQhljhq68b1T"

def get_official_or_fallback_link(page_url):
    """
    Result Bharat ke detail page se official government link nikalega.
    Agar official link nahi milta, toh WhatsApp channel link return karega.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(page_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for official apply links inside tables or action buttons
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            link_text = a.text.lower()
            
            # Identify official links (Exclude Result Bharat and internal pages)
            if "resultbharat" not in href and href.startswith("http"):
                if any(kw in link_text for kw in ["apply", "official", "registration", "online", "click here", "notification"]):
                    print(f"Found Official Link: {href}")
                    return href
                    
        # If no explicit official link matched keyword, find any external non-ResultBharat link
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith("http") and "resultbharat" not in href:
                return href

    except Exception as e:
        print(f"Error fetching official link: {e}")
        
    # Result Bharat ka link kabhi mat do -> Fallback to WhatsApp Channel
    print("Official link not found. Falling back to WhatsApp Channel Link.")
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
        print(f"Telegram API Status: {resp.status_code}")

def create_ctr_banner(title):
    template_w, template_h = 1080, 720
    img = Image.new("RGB", (template_w, template_h), color="#0F172A")
    draw = ImageDraw.Draw(img)

    # Header Banner
    draw.rectangle([0, 0, template_w, 100], fill="#1E293B")
    draw.text((50, 35), "ROJGAR UPDATE (OFFICIAL)", fill="#38BDF8")

    # Content Box
    draw.rectangle([60, 150, 1020, 520], fill="#1E293B", outline="#38BDF8", width=3)
    
    display_title = title[:60] + "..." if len(title) > 60 else title
    
    # Red Badge
    draw.rectangle([60, 150, 410, 210], fill="#DC2626")
    draw.text((80, 168), "URGENT JOB UPDATE", fill="#FFFFFF")

    # Notice Details
    draw.text((100, 260), "VACANCY / NOTICE DETAILS:", fill="#F59E0B")
    draw.text((100, 330), display_title, fill="#FFFFFF")

    # Action Buttons
    draw.rectangle([60, 550, 500, 650], fill="#0284C7")
    draw.text((120, 585), "✅ VIEW DETAILS", fill="#FFFFFF")
    
    draw.rectangle([580, 550, 1020, 650], fill="#166534")
    draw.text((640, 585), "💻 APPLY NOW", fill="#FFFFFF")
    
    draw.text((430, 685), "@officialrojgarupdate", fill="#FFFFFF")

    output_path = "final_post.png"
    img.save(output_path)
    return output_path

def scrape_and_post():
    url = "https://www.resultbharat.com/index-job.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for post in soup.select('div.mainbox-content a', href=True):
            title = post.text.strip()
            rb_page_link = post['href']
            
            if len(title) > 10 and (".html" in rb_page_link or "pdf" in rb_page_link.lower()):
                if not rb_page_link.startswith("http"):
                    rb_page_link = "https://www.resultbharat.com/" + rb_page_link
                
                # Skip homepage/index links
                if "resultbharat.com/index" in rb_page_link or rb_page_link == "https://www.resultbharat.com/":
                    continue
                
                title = re.sub(r'(?i)result\s*bharat|main site', '', title).strip()

                # Get Official Direct Link (or WhatsApp link as fallback)
                final_link = get_official_or_fallback_link(rb_page_link)

                banner_file = create_ctr_banner(title)
                send_telegram_photo(banner_file, title, final_link)
                break
                
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
