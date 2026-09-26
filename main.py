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

def get_job_full_details(page_url):
    """
    Extracts official link, original image, dates, fee, and vacancy info.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    official_link = None
    img_url = None
    details = {
        "dates": "Check Notification",
        "fee": "Check Notification",
        "vacancy": "Various Posts"
    }
    
    try:
        resp = requests.get(page_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Original Banner Extraction
        for img in soup.find_all('img'):
            src = img.get('src', '').strip()
            if src and any(k in src.lower() for k in ['uploads', 'post', 'job', 'banner', 'wp-content']):
                if not any(x in src.lower() for x in ['logo', 'icon', 'ad', 'widgets']):
                    img_url = src if src.startswith("http") else "https://www.fastjobsearchers.com/" + src.lstrip("/")
                    break

        # 2. Extract Dates, Fee, Vacancy Details from page text
        page_text = soup.get_text()
        
        # Extract Vacancy / Total Posts
        vacancy_match = re.search(r'(?:total\s*post|total\s*vacancy|vacancies|posts?)\s*[:\-]\s*([\w\d\s+]+)', page_text, re.IGNORECASE)
        if vacancy_match:
            details["vacancy"] = vacancy_match.group(1).strip()[:30]

        # Extract Application Fee
        fee_match = re.search(r'(?:application\s*fee|fee)\s*[:\-]\s*([^\n]+)', page_text, re.IGNORECASE)
        if fee_match:
            details["fee"] = fee_match.group(1).strip()[:40]

        # Extract Dates
        date_match = re.search(r'(?:apply\s*date|important\s*dates?|last\s*date)\s*[:\-]\s*([^\n]+)', page_text, re.IGNORECASE)
        if date_match:
            details["dates"] = date_match.group(1).strip()[:50]

        # 3. Direct Official Apply / Notification Link Extraction
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
        print(f"Detail extraction error: {e}")
        
    if not official_link:
        official_link = WHATSAPP_LINK

    return official_link, img_url, details

def watermark_original_banner(img_url):
    """
    Downloads original banner from website and overlays logo.png (Rojgar Update).
    """
    output_path = "final_banner.png"
    logo_path = "logo.png"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if img_url:
            resp = requests.get(img_url, headers=headers, timeout=8)
            if resp.status_code == 200 and len(resp.content) > 1000:
                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                
                # Overlay logo.png on top-right corner
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path).convert("RGBA")
                    logo.thumbnail((int(img.width * 0.22), int(img.height * 0.22)))
                    position = (img.width - logo.width - 20, 20)
                    img.paste(logo, position, logo)

                img.convert("RGB").save(output_path)
                return output_path
    except Exception as e:
        print(f"Watermark processing error: {e}")
        
    return None

def send_telegram_post(image_path, title, final_link, details):
    caption_text = (
        f"🚨 <b>{title}</b>\n\n"
        f"📅 <b>Important Dates:</b> {details['dates']}\n"
        f"💰 <b>Application Fee:</b> {details['fee']}\n"
        f"🔢 <b>Total Vacancy:</b> {details['vacancy']}\n\n"
        f"📌 <b>Telegram:</b> @officialrojgarupdate\n\n"
        f"📲 <b>Official Apply & Details Link:</b> 👇\n"
        f"🔗 <a href='{final_link}'>Click Here To Apply / Details</a>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💚 <b>Join Our WhatsApp Channel for Daily Updates:</b>\n"
        f"👉 <a href='{WHATSAPP_LINK}'>Click Here to Join WhatsApp Channel</a>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    
    if image_path and os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as photo:
            resp = requests.post(url, data={
                "chat_id": CHANNEL_ID,
                "caption": caption_text,
                "parse_mode": "HTML"
            }, files={"photo": photo})
            print(f"Photo Post Status Code: {resp.status_code}")
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "text": caption_text,
            "parse_mode": "HTML"
        })
        print(f"Text Post Status Code: {resp.status_code}")

def scrape_and_post():
    url = "https://www.fastjobsearchers.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    posted_urls = load_posted_urls()
    
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
                
                clean_title = re.sub(r'(?i)fast\s*job\s*searchers|fastjobsearchers|\.com', '', raw_title).strip()
                
                if not clean_title or clean_title.lower() in ignored_titles:
                    continue

                if job_page_link in posted_urls:
                    continue
                
                print(f"Processing Post: {clean_title}")
                final_link, img_url, details = get_job_full_details(job_page_link)
                
                banner_file = watermark_original_banner(img_url)
                send_telegram_post(banner_file, clean_title, final_link, details)
                
                save_posted_url(job_page_link)
                break

    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    scrape_and_post()
