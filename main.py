import os
import datetime
import requests
import feedparser
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

RSS_FEEDS = [
    "https://www.dezeen.com/fashion/feed/",
    "https://fashionunited.com/rss/news",
    "https://sourcingjournal.com/feed/",
    "https://www.textiletoday.com.bd/feed/"
]

def collect_trends():
    items = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:5]:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")
            })

    return items[:20]

def create_ai_report(items):
    content = "\n\n".join([
        f"Başlık: {item['title']}\nÖzet: {item['summary']}\nLink: {item['link']}"
        for item in items
    ])

    prompt = f"""
Sen moda ve tekstil sektörünü takip eden profesyonel bir trend analistisin.

Aşağıdaki haberlerden Türkçe günlük bir trend raporu hazırla.

Rapor formatı:
1. Günün kısa özeti
2. Öne çıkan 5 trend
3. Kumaş / materyal sinyalleri
4. Renk / desen sinyalleri
5. Perakende ve tüketici davranışı
6. Tekstil sektörü için fırsatlar
7. Kısa aksiyon önerileri

Kaynak içerikler:
{content}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text

def create_pdf(report_text):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"moda_tekstil_trend_raporu_{today}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Günlük Moda & Tekstil Trend Raporu", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Tarih: {today}", styles["Normal"]))
    story.append(Spacer(1, 24))

    for line in report_text.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["BodyText"]))
            story.append(Spacer(1, 8))

    doc.build(story)
    return filename

def send_pdf_to_telegram(filename):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    with open(filename, "rb") as file:
        files = {"document": file}
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": "Günlük Moda & Tekstil Trend Raporu hazırlandı."
        }

        response = requests.post(url, data=data, files=files)

    if response.status_code != 200:
        raise Exception(f"Telegram gönderim hatası: {response.text}")

def main():
    items = collect_trends()

    if not items:
        raise Exception("Trend kaynaklarından içerik alınamadı.")

    report = create_ai_report(items)
    pdf_file = create_pdf(report)
    send_pdf_to_telegram(pdf_file)

    print("Rapor başarıyla oluşturuldu ve Telegram'a gönderildi.")

if __name__ == "__main__":
    main()