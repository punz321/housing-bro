import json
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#Config
TARGET_URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"
SNAPSHOT_FILE = "snapshots/stwdo.json"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

#Helpers

def fetch_page():
    resp = requests.get(TARGET_URL, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_listings(html):
    soup = BeautifulSoup(html, "lxml")
    listings = []

    for link in soup.select("a[href*='/wohnen/']"):
        title = link.get_text(strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        listings.append({
            "title": title,
            "url": "https://www.stwdo.de" + href
        })

    # remove duplicates
    unique = {item["url"]: item for item in listings}
    return list(unique.values())


def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        return []

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(data):
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def detect_new(old, new):
    old_urls = {item["url"] for item in old}
    return [item for item in new if item["url"] not in old_urls]


def send_email(new_listings):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "🏠 New Studentenwerk Dortmund Housing Offer(s)"

    body_lines = [
        "New housing offer(s) detected:\n"
    ]

    for item in new_listings:
        body_lines.append(f"- {item['title']}\n  {item['url']}\n")

    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


#main
def main():
    html = fetch_page()
    current_listings = parse_listings(html)
    previous_listings = load_snapshot()

    new_listings = detect_new(previous_listings, current_listings)

    if new_listings:
        send_email(new_listings)
        save_snapshot(current_listings)
        print(f"✅ {len(new_listings)} new listing(s) found. Email sent.")
    else:
        print("ℹ️ No new listings.")


if __name__ == "__main__":
    main()