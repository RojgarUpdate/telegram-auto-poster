import os
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    official_link = None
    img_url = None
    
    try:
        resp = requests.get(page_url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Image extract karna (sabse pehle content area se)
        content_div = soup.find('div', class_=re.compile(r'entry-content|post-body|content', re.I)) or soup
        for img in content_div.find_all('img'):
            src = img.get('src', '').strip()
            if src and not any(x in src.lower() for x in ['logo', 'icon', 'banner-ad', 'widgets']):
                if not src.startswith("http"):
                    img_url = "https://www.fastjobsearchers.com/" + src.lstrip("/")
                else:
                    img_url = src
                break

        # Official Apply / Notification link extraction
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

def create_fallback_text_banner(title):
    width, height = 1280, 720
    template_path = "job_template.png"
    logo_path = "logo.png"
    
    if os.path.exists(template_path):
        img = Image.open(template_path).convert("RGB").resize((width, height))
    else:
        img = Image.new("RGB", (width, height), color="#092B5A")
        
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font_title = ImageFont.load_default()

    display_title = title[:45] + "..." if len(title) > 45 else title
    
    # Title ko Image ke upar render karo agar original image missing ho
    draw.text((100, 250), "JOB UPDATE", fill="#FFCC00", font=font_title)
    draw.text((100, 320), display_title.upper(), fill="#FFFFFF", font=font_title)

    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((150, 150))
            img.paste(logo, (width - 170, 20), logo)
        except Exception as e:
            print(f"Logo error: {e}")

    output_path = "final_banner.png"
    img.save(output_path)
    return output_path

def process_banner_with_watermark(img_url, title):
    output_path = "final_banner.png"
    logo_path = "logo.png"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if img_url:
            resp = requests.get(img_url, headers=headers, timeout=8)
            if resp.status_code == 200 and len(resp.content) > 1000:
                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                
                # Watermark add karna
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path).convert("RGBA")
                    logo.thumbnail((int(img.width * 0.20), int(img.height * 0.20)))
                    position = (img.width - logo.width - 20, 20)
                    img.paste(logo, position, logo)

                img.convert("RGB").save(output_path)
                return output_path

        # Image na milne par text-banner fallback
        return create_fallback_text_banner(title)

    except Exception as e:
        print(f"Image processing error: {e}")
        return create_fallback_text_banner(title)

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

def scrape_and_post():
    url = "https://www.fastjobsearchers.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    posted_urls = load_posted_urls()
    
    # Generic category names jinhe title nahi banana hai
    ignored_titles = [
        "home", "current job", "latest job", "result", "admit card", 
        "answer key", "syllabus", "view all", "contact us", "privacy policy"
    ]
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        
        for a in all_links:
            raw_title = a.text.strip()
            job_page_link = a['href'].strip()

            if len(raw_title) > 10 and ("fastjobsearchers.com" in job_page_link or job_page_link.startswith("/") or ".php" in job_page_link):
                if not job_page_link.startswith("http"):
                    job_page_link = "https://www.fastjobsearchers.com/" + job_page_link.lstrip("/")
                
                # Title clean karna
                clean_title = re.sub(r'(?i)fast\s*job\s*searchers|fastjobsearchers|\.com', '', raw_title).strip()
                
                # Category titles ignore karo
                if not clean_title or clean_title.lower() in ignored_titles:
                    continue

                # Check Duplicate
                if job_page_link in posted_urls:
                    continue
                
                print(f"Processing Post: {clean_title}")
                final_link, img_url = get_official_or_fallback_link_and_img(job_page_link)
                
                banner_file = process_banner_with_watermark(img_url, clean_title)
                send_telegram_photo(banner_file, clean_title, final_link)
                
                save_posted_url(job_page_link)
                break

    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
