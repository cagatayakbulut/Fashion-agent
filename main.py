import os
import html
import datetime
import requests
import feedparser

from dotenv import load_dotenv
from openai import OpenAI

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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

Kurallar:
Markdown kullanma.
Yıldız, başlık işareti, çizgi ayırıcı kullanma.
Düz ve temiz metin yaz.
Türkçe karakterleri doğru kullan.

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


def setup_turkish_font():
    font_name = "DejaVuSans"
    font_path = "DejaVuSans.ttf"

    system_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf"
    ]

    for path in system_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(font_name, path))
            print(f"Font sistemden yüklendi: {path}")
            return font_name

    font_url = "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/version_2_37/ttf/DejaVuSans.ttf"

    print("Font indiriliyor...")
    response = requests.get(font_url, timeout=30)
    response.raise_for_status()

    with open(font_path, "wb") as f:
        f.write(response.content)

    pdfmetrics.registerFont(TTFont(font_name, font_path))
    print("Font indirildi ve yüklendi.")

    return font_name


def clean_report_text(text):
    text = text.replace("**", "")
    text = text.replace("#", "")
    text = text.replace("---", "")
    text = text.replace("•", "-")
    return text


def create_pdf(report_text):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"moda_tekstil_trend_raporu_{today}.pdf"

    font_name = setup_turkish_font()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        fontName=font_name,
        fontSize=18,
        leading=24,
        spaceAfter=16
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    story = []

    story.append(Paragraph("Günlük Moda & Tekstil Trend Raporu", title_style))
    story.append(Paragraph(f"Tarih: {today}", body_style))
    story.append(Spacer(1, 16))

    clean_text = clean_report_text(report_text)

    for line in clean_text.split("\n"):
        if line.strip():
            safe_line = html.escape(line.strip())
            story.append(Paragraph(safe_line, body_style))

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
