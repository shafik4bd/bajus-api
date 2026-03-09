import re, os, json, httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler

BAJUS_URL = "https://www.bajus.org/gold-price"
BD_TZ = timezone(timedelta(hours=6))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
}

def gram_to_bhori(p):
    try: return f"{round(float(re.sub(r'[^\\d.]', '', p)) * 11.664):,}"
    except: return None

def parse_html(html):
    soup = BeautifulSoup(html, "lxml")
    gold, silver = [], []
    body_text = soup.get_text(separator=" ")

    # effective_from তারিখ
    effective_from = None
    m = re.search(r"effective[\s\S]{0,40}?(\d{1,2}[:.]\d{2}\s*(?:am|pm)[\s,]*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})", body_text, re.IGNORECASE)
    if m:
        effective_from = m.group(1).strip()

    # ── পদ্ধতি ১: table থেকে পার্স ──
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2: continue
            joined = " ".join(cells).lower()
            if "product" in joined and "description" in joined: continue
            product     = cells[0].strip()
            description = cells[1].strip() if len(cells) > 1 else ""
            raw_price   = cells[2].strip() if len(cells) > 2 else ""
            price_clean = re.sub(r"[^\d.]", "", raw_price) or None
            if not product: continue
            item = {
                "product": product,
                "description": description,
                "price_per_gram": price_clean,
                "price_per_bhori": gram_to_bhori(price_clean) if price_clean else None,
            }
            if re.search(r"silver|রুপা|রূপা", product, re.IGNORECASE):
                silver.append(item)
            else:
                gold.append(item)

    # ── পদ্ধতি ২: div/td যেকোনো জায়গা থেকে "KARAT" খোঁজা ──
    if not gold:
        for tag in soup.find_all(["td", "div", "p", "li", "span"]):
            text = tag.get_text(separator=" ", strip=True)
            # "22 KARAT GOLD PER GRAM" এর পর দাম থাকে
            km = re.search(r"(2[124]|18)\s*KARAT", text, re.IGNORECASE)
            pm = re.search(r"(\d{3,6})\s*(BDT|৳|TK)?", text, re.IGNORECASE)
            if km and pm:
                karat = km.group(1)
                pc = pm.group(1)
                gold.append({
                    "product": f"{karat} Karat Gold",
                    "description": text[:80],
                    "price_per_gram": pc,
                    "price_per_bhori": gram_to_bhori(pc),
                })

    # ── পদ্ধতি ৩: raw text থেকে regex ──
    if not gold:
        patterns = [
            ("22 Karat Gold (Hallmarked)", r"22\s*karat[^0-9]{0,30}?(\d{4,6})"),
            ("21 Karat Gold (Hallmarked)", r"21\s*karat[^0-9]{0,30}?(\d{4,6})"),
            ("18 Karat Gold (Hallmarked)", r"18\s*karat[^0-9]{0,30}?(\d{4,6})"),
            ("Traditional Gold",           r"traditional[^0-9]{0,30}?(\d{4,6})"),
            ("22 Karat Gold",              r"6[5-9]\d{2}|[78]\d{3}"),  # দাম সরাসরি range দিয়ে
        ]
        for label, pattern in patterns[:4]:
            fm = re.search(pattern, body_text, re.IGNORECASE)
            if fm:
                pc = fm.group(1)
                gold.append({"product": label, "description": "regex", "price_per_gram": pc, "price_per_bhori": gram_to_bhori(pc)})

    # ── পদ্ধতি ৪: JSON/script tag থেকে ──
    if not gold:
        for script in soup.find_all("script"):
            st = script.string or ""
            jm = re.findall(r'"price"\s*:\s*"?(\d{4,6})"?', st, re.IGNORECASE)
            if jm:
                gold.append({"product": "Gold (script)", "description": "script tag", "price_per_gram": jm[0], "price_per_bhori": gram_to_bhori(jm[0])})
                break

    return {"gold": gold, "silver": silver, "effective_from": effective_from}

def fetch_bajus():
    html, method = None, None

    # স্তর ১: ScraperAPI (সবার আগে — সবচেয়ে নির্ভরযোগ্য)
    key = os.environ.get("SCRAPER_API_KEY")
    if key:
        for render in ["true", "false"]:
            try:
                url = f"http://api.scraperapi.com?api_key={key}&url={BAJUS_URL}&render={render}&country_code=bd"
                with httpx.Client(timeout=45) as c:
                    r = c.get(url)
                    if r.status_code == 200 and len(r.text) > 500:
                        html, method = r.text, f"scraperapi-render={render}"
                        break
            except: pass

    # স্তর ২: সরাসরি BAJUS
    if not html:
        try:
            with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as c:
                r = c.get(BAJUS_URL)
                if r.status_code == 200:
                    html, method = r.text, "direct"
        except: pass

    # স্তর ৩: Google Cache
    if not html:
        try:
            cache_url = "https://webcache.googleusercontent.com/search?q=cache:" + BAJUS_URL
            with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as c:
                r = c.get(cache_url)
                if r.status_code == 200:
                    html, method = r.text, "google-cache"
        except: pass

    if not html:
        raise RuntimeError("BAJUS সাইট থেকে ডেটা আনা সম্ভব হয়নি।")

    parsed = parse_html(html)
    return {
        "source": "BAJUS (বাংলাদেশ জুয়েলার্স সমিতি)",
        "source_url": BAJUS_URL,
        "currency": "BDT",
        "gold": parsed["gold"],
        "silver": parsed["silver"],
        "effective_from": parsed["effective_from"],
        "fetched_at": datetime.now(BD_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "_meta": {"method": method},
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = fetch_bajus()
            body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
            self.send_response(502)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=7200")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
