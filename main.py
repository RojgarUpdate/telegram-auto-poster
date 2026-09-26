import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

def create_job_banner(title, post_url):
    template = Image.open("job_template.png")
    draw = ImageDraw.Draw(template)
    
    # Title text placement on blue template
    draw.text((360, 80), title[:45], fill="#0A192F")
    
    output_path = "final_banner.png"
    template.save(output_path)
    send_telegram(output_path, title, post_url)

def create_notice_banner(title, pdf_url):
    template = Image.open("notice_template.png")
    
    res = requests.get(pdf_url)
    with open("temp.pdf", "wb") as f:
        f.write(res.content)
    
    pdf_images = convert_from_path("temp.pdf")
    notice_crop = pdf_images[0].resize((980, 420))
    
    template.paste(notice_crop, (110, 120))
    
    output_path = "final_banner.png"
    template.save(output_path)
    send_telegram(output_path, title, pdf_url)

def send_telegram(image_path, caption, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    caption_text = f"<b>{caption}</b>\n\n🔗 <a href='{link}'>Click Here for Full Details</a>"
    
    with open(image_path, 'rb') as photo:
        requests.post(url, data={
            "chat_id": CHANNEL_ID,
            "caption": caption_text,
            "parse_mode": "HTML"
        }, files={"photo": photo})

def scrape_result_bharat():
    url = "https://www.resultbharat.com/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    posted_file = "posted.txt"
    posted_links = set()
    if os.path.exists(posted_file):
        with open(posted_file, "r") as f:
            posted_links = set(f.read().splitlines())

    for a in soup.find_all('a', href=True):
        link = a['href']
        title = a.text.strip()
        
        if link not in posted_links and len(title) > 10:
            if "pdf" in link.lower() or "notice" in link.lower():
                create_notice_banner(title, link)
            else:
                create_job_banner(title, link)
            
            with open(posted_file, "a") as f:
                f.write(link + "\n")
            break

if __name__ == "__main__":
    scrape_result_bharat()
