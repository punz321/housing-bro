import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

URL = "https://www.stwdo.de/wohnen/aktuelle-wohnangebote"
DATA_FILE = "data/seen_listings.json"

EMAIL = os.getenv("ALERT_EMAIL")
EMAIL_PASS = os.getenv("ALERT_EMAIL_PASS")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def load_seen():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_seen(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_listings():
    r = requests.get(URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    listings = []
    cards = soup.select(".object-list .object")
    
    for card in cards:
        title = card.select_one(".object__title")
        link = card.find("a", href=True)

        if not title or not link:
            continue

        listings.append({
            "title": title.get_text(strip=True),
            "url": "https://www.stwdo.de" + link["href"]
        })

    return listings

def send_email(new_listings):
    msg = EmailMessage()
    msg["Subject"] = "New Studentenwerk Dortmund housing listing"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    body = "New housing listings detected:\n\n"
    for l in new_listings:
        body += f"- {l['title']}\n  {l['url']}\n\n"

    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, EMAIL_PASS)
        server.send_message(msg)

def main():
    print("Script ran successfully")
    seen = load_seen()
    seen_urls = {item["url"] for item in seen}

    current = fetch_listings()
    new_listings = [l for l in current if l["url"] not in seen_urls]

    if new_listings:
        print("New listings found, sending email...")
        send_email(new_listings)
        seen.extend(new_listings)
        save_seen(seen)
    else:
        print("No new listings.")

if __name__ == "__main__":
    main()