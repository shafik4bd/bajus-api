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

def fetch_bajus():
    html, method = None, None
    try:
        with httpx.Client(timeout=12, headers=HEADERS, follow_redirects=True) as c:
            r = c.get(BAJUS_URL)
            if r.status_code == 200: html, method = r.text, "direct"
    except: pass
    if not html:
        key = os.environ.get("SCRAPER_API_KEY")
        if key:
            try:
                with httpx.Client(timeout=30) as c:
                    r = c.get(f"http://api.scraperapi.com?api_key={key}&url={BAJUS_URL}&render=true")
                    if r.status_code == 200: html, method = r.text, "scraperapi"
            except: pass
    if not html: raise RuntimeError("ডেটা আনা সম্ভব হয়নি।")

    soup = BeautifulSoup(html, "lxml")
    gold = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td","th"])]
            if len(cells) < 2: continue
            joined = " ".join(cells).lower()
            if "product" in joined and "description" in joined: continue
            p, d = cells[0], cells[1] if len(cells)>1 else ""
            raw = cells[2] if len(cells)>2 else ""
            pc = re.sub(r"[^\d.]", "", raw) or None
            if p and not re.search(r"silver|রুপা", p, re.IGNORECASE):
                gold.append({"product":p,"description":d,"price_per_gram":pc,"price_per_bhori":gram_to_bhori(pc) if pc else None})
    return {"source":"BAJUS","currency":"BDT","gold":gold,
            "fetched_at":datetime.now(BD_TZ).strftime("%Y-%m-%d %H:%M:%S"),"_meta":{"method":method}}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = fetch_bajus()
            body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
            self.send_response(502)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
