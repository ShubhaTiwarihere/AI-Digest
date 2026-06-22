import feedparser
import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

RSS_FEEDS = [
    ("Google News – AI",        "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("TechCrunch AI",           "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("VentureBeat AI",          "https://venturebeat.com/category/ai/feed/"),
    ("The Verge AI",            "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
    ("MIT Technology Review",   "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Wired AI",                "https://www.wired.com/feed/category/artificial-intelligence/latest/rss"),
    ("Ars Technica AI",         "https://feeds.arstechnica.com/arstechnica/index"),
]

def clean_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_articles():
    articles = []
    seen = set()
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:6]:
                title = clean_html(entry.get('title', '')).strip()
                link  = entry.get('link', '')
                raw   = entry.get('summary', entry.get('description', ''))
                summary = clean_html(raw).strip()
                if len(summary) > 350:
                    summary = summary[:350].rsplit(' ', 1)[0] + '…'
                key = title.lower()[:60]
                if key and link and key not in seen:
                    seen.add(key)
                    articles.append({'title': title, 'link': link, 'summary': summary or 'No summary available.', 'source': source})
        except Exception as exc:
            print(f"[WARN] Could not fetch {source}: {exc}")
    return articles[:10]

def build_html(articles, date_str):
    rows = ""
    for i, a in enumerate(articles, 1):
        rows += f"""
        <div style="margin-bottom:22px;">
          <p style="margin:0 0 4px 0;font-size:13px;color:#888;text-transform:uppercase;letter-spacing:.5px;">{a['source']}</p>
          <h3 style="margin:0 0 8px 0;font-size:16px;color:#111;line-height:1.4;">{i}. {a['title']}</h3>
          <p style="margin:0 0 8px 0;font-size:14px;color:#444;line-height:1.6;">{a['summary']}</p>
          <a href="{a['link']}" style="font-size:13px;color:#0066cc;text-decoration:none;">Read more →</a>
        </div>
        <hr style="border:none;border-top:1px solid #eee;margin:0 0 22px 0;">"""
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <div style="max-width:620px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">
    <div style="background:#111;padding:28px 32px;">
      <h1 style="margin:0;color:#fff;font-size:22px;">☀️ Daily AI Digest</h1>
      <p style="margin:6px 0 0;color:#aaa;font-size:14px;">{date_str}</p>
    </div>
    <div style="padding:28px 32px;">
      <p style="margin:0 0 24px;font-size:15px;color:#333;">Hi Shubha, here are today's top 10 AI developments:</p>
      <hr style="border:none;border-top:2px solid #111;margin:0 0 24px 0;">
      {rows}
      <p style="margin:24px 0 0;font-size:12px;color:#bbb;text-align:center;">Sent automatically via GitHub Actions</p>
    </div>
  </div></body></html>"""

def send_email(html, date_str):
    smtp_user = os.environ['GMAIL_USER']
    smtp_pass = os.environ['GMAIL_APP_PASSWORD']
    to_email  = os.environ.get('TO_EMAIL', smtp_user)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"☀️ Your Daily AI Digest — {date_str}"
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
    print(f"✅ Digest sent to {to_email}")

if __name__ == "__main__":
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    print(f"Fetching AI news for {date_str}…")
    articles = fetch_articles()
    print(f"Found {len(articles)} articles")
    send_email(build_html(articles, date_str), date_str)
