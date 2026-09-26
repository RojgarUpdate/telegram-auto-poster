import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WHATSAPP_LINK = "https://whatsapp.com/channel/0029VaBLUVk7oQhljhq68b1T"

HISTORY_FILE = "posted_urls.txt"

def load_posted_urls():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_posted_url(url):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{url}\n")

def get_official_or_fallback_link_and_img(page_url):
    """
    Detail page se official link aur post ka original banner image extract karta hai.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    official_link = None
    img_url = None
    
    try:
        resp = requests.get(page_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Post Banner Image URL
        img_tag = soup.find('img', src=re.compile(r'uploads|post|job', re.I)) or soup.find('img')
        if img_tag and img_tag.get('src'):
            src = img_tag['src'].strip()
            if not src.startswith("http"):
                img_url = "https://www.fastjobsearchers.com/" + src.lstrip("/")
            else:
                img_url = src

        # 2. Official Link Extraction
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            link_text = a.text.lower()
            if "fastjobsearchers" not in href and href.startswith("http"):
                if any(kw in link_text for kw in ["apply", "official", "registration", "online", "click here", "notification", "download"]):
                    official_link = href
                    break
                    
        if not official_link:
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith("http") and "fastjobsearchers" not in href:
                    official_link = href
                    break

    except Exception as e:
        print(f"Extraction error: {e}")
        
    if not official_link:
        official_link = WHATSAPP_LINK

    return official_link, img_url

def process_banner_with_watermark(img_url):
    """
    Website se banner download karta hai aur top corner me logo.png / QR stamp karta hai.
    """
    output_path = "final_banner.png"
    logo_path = "logo.png"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if img_url:
            resp = requests.get(img_url, headers=headers, timeout=8)
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
        else:
            # Fallback blank canvas if no image found on post
            img = Image.new("RGBA", (1280, 720), color="#092B5A")

        # Overlay Logo / QR Code
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            # Logo/QR size proportional to image
            logo.thumbnail((int(img.width * 0.20), int(img.height * 0.20)))
            # Paste on top-right corner
            position = (img.width - logo.width - 20, 20)
            img.paste(logo, position, logo)

        img.convert("RGB").save(output_path)
        return output_path

    except Exception as e:
        print(f"Image processing error: {e}")
        return None

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
    
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            resp = requests.post(url, data={
                "chat_id": CHANNEL_ID,
                "caption": caption_text,
                "parse_mode": "HTML"
            }, files={"photo": photo})
            print(f"Photo Post Status Code: {resp.status_code}")
    else:
        # Fallback to Text if image failed
        url_msg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url_msg, data={
            "chat_id": CHANNEL_ID,
            "text": caption_text,
            "parse_mode": "HTML"
        })

def scrape_and_post():
    url = "https://www.fastjobsearchers.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    posted_urls = load_posted_urls()
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        
        for a in all_links:
            raw_title = a.text.strip()
            job_page_link = a['href'].strip()

            if len(raw_title) > 8 and ("fastjobsearchers.com" in job_page_link or job_page_link.startswith("/") or ".php" in job_page_link):
                if not job_page_link.startswith("http"):
                    job_page_link = "https://www.fastjobsearchers.com/" + job_page_link.lstrip("/")
                
                # Check for Duplicate
                if job_page_link in posted_urls:
                    continue

                title = re.sub(r'(?i)fast\s*job\s*searchers|fastjobsearchers|\.com', '', raw_title).strip()
                if not title or title.lower() in ["home", "contact us", "about us", "privacy policy"]:
                    continue
                
                print(f"Processing Post: {title}")
                final_link, img_url = get_official_or_fallback_link_and_img(job_page_link)
                
                # Download original banner & stamp logo/QR
                banner_file = process_banner_with_watermark(img_url)
                
                # Post to Telegram
                send_telegram_photo(banner_file, title, final_link)
                
                # Save URL
                save_posted_url(job_page_link)
                break

    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
