"""
BAJUS Scraper Core
==================
Source   : https://www.bajus.org/gold-price
Structure: Product | Description | Price (BDT/gram)

Cloudflare Bypass (৩ স্তর):
  1. Real browser headers দিয়ে সরাসরি
  2. Google Cache fallback
  3. ScraperAPI fallback (SCRAPER_API_KEY env দিলে)
"""

import re
import os
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

BAJUS_URL = "https://www.bajus.org/gold-price"
BD_TZ = timezone(timedelta(hours=6))

# ── Real Browser Headers (Cloudflare bypass) ──────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language":  "en-US,en;q=0.9,bn;q=0.8",
    "Accept-Encoding":  "gzip, deflate, br",
    "Cache-Control":    "no-cache",
    "Pragma":           "no-cache",
    "Sec-Ch-Ua":        '"Chromium";v="124","Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest":   "document",
    "Sec-Fetch-Mode":   "navigate",
    "Sec-Fetch-Site":   "none",
    "Sec-Fetch-User":   "?1",
    "Upgrade-Insecure-Requests": "1",
    "Referer":          "https://www.google.com/",
    "Connection":       "keep-alive",
}


# ── Helper ────────────────────────────────────────────────────

def gram_to_bhori(price_str: str):
    """১ ভরি = ১১.৬৬৪ গ্রাম"""
    try:
        num = float(re.sub(r"[^\d.]", "", price_str))
        return f"{round(num * 11.664):,}"
    except Exception:
        return None


def bd_now() -> str:
    return datetime.now(BD_TZ).strftime("%Y-%m-%d %H:%M:%S")


# ── HTML Parser ───────────────────────────────────────────────

def parse_html(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    gold, silver = [], []
    effective_from = None

    # "effective from" তারিখ খোঁজা
    body_text = soup.get_text(separator=" ")
    m = re.search(
        r"effective[\s\S]{0,30}?(\d{1,2}[:.]\d{2}\s*(?:am|pm)[\s,]*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        body_text, re.IGNORECASE
    )
    if m:
        effective_from = m.group(1).strip()

    # টেবিল পার্স
    # BAJUS স্ট্রাকচার: Product | Description | Price (BDT/gram)
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(separator=" ", strip=True)
                     for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            joined = " ".join(cells).lower()
            if "product" in joined and "description" in joined:
                continue  # হেডার রো স্কিপ

            product     = cells[0]
            description = cells[1] if len(cells) > 1 else ""
            raw_price   = cells[2] if len(cells) > 2 else ""
            price_clean = re.sub(r"[^\d.]", "", raw_price) or None

            if not product:
                continue

            item = {
                "product":        product,
                "description":    description,
                "price_per_gram": price_clean,
                "price_per_bhori": gram_to_bhori(price_clean) if price_clean else None,
            }

            if re.search(r"silver|রুপা|রূপা", product, re.IGNORECASE):
                silver.append(item)
            else:
                gold.append(item)

    # Fallback: টেবিল না পেলে regex দিয়ে raw text থেকে বের করা
    if not gold:
        patterns = [
            ("22 Karat Gold (Hallmarked)", r"22[- ]?karat[^0-9]*([0-9,]+)"),
            ("21 Karat Gold (Hallmarked)", r"21[- ]?karat[^0-9]*([0-9,]+)"),
            ("18 Karat Gold (Hallmarked)", r"18[- ]?karat[^0-9]*([0-9,]+)"),
            ("Traditional Gold",           r"traditional[^0-9]*([0-9,]+)"),
        ]
        for label, pattern in patterns:
            fm = re.search(pattern, body_text, re.IGNORECASE)
            if fm:
                pc = fm.group(1).replace(",", "")
                gold.append({
                    "product":         label,
                    "description":     "regex fallback",
                    "price_per_gram":  pc,
                    "price_per_bhori": gram_to_bhori(pc),
                })

    return {"gold": gold, "silver": silver, "effective_from": effective_from}


# ── Main Fetch (৩ স্তরের Cloudflare Bypass) ──────────────────

def fetch_bajus() -> dict:
    html = None
    method = None

    # ── স্তর ১: সরাসরি BAJUS (real browser headers) ──
    try:
        with httpx.Client(timeout=12, headers=HEADERS, follow_redirects=True) as client:
            r = client.get(BAJUS_URL)
            if r.status_code == 200:
                html = r.text
                method = "direct"
    except Exception:
        pass

    # ── স্তর ২: Google Cache ──
    if not html:
        try:
            cache_url = (
                "https://webcache.googleusercontent.com/search?q=cache:"
                + BAJUS_URL
            )
            with httpx.Client(timeout=12, headers=HEADERS, follow_redirects=True) as client:
                r = client.get(cache_url)
                if r.status_code == 200:
                    html = r.text
                    method = "google-cache"
        except Exception:
            pass

    # ── স্তর ৩: ScraperAPI (SCRAPER_API_KEY env দিলে সক্রিয়) ──
    if not html:
        api_key = os.environ.get("SCRAPER_API_KEY")
        if api_key:
            try:
                scraper_url = (
                    f"http://api.scraperapi.com"
                    f"?api_key={api_key}"
                    f"&url={BAJUS_URL}"
                    f"&render=true"
                )
                with httpx.Client(timeout=30) as client:
                    r = client.get(scraper_url)
                    if r.status_code == 200:
                        html = r.text
                        method = "scraperapi"
            except Exception:
                pass

    if not html:
        raise RuntimeError(
            "BAJUS সাইট থেকে ডেটা আনা সম্ভব হয়নি। "
            "Vercel → Settings → Environment Variables-এ "
            "SCRAPER_API_KEY যোগ করুন।"
        )

    parsed = parse_html(html)

    return {
        "source":        "BAJUS (বাংলাদেশ জুয়েলার্স সমিতি)",
        "source_url":    BAJUS_URL,
        "currency":      "BDT",
        "gold":          parsed["gold"],
        "silver":        parsed["silver"],
        "effective_from": parsed["effective_from"],
        "fetched_at":    bd_now(),
        "_meta":         {"method": method},
    }
