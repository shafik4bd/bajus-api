from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "BAJUS API is Live! Visit /prices"}

@app.get("/prices")
def get_prices():
    url = "https://www.bajus.org/gold-price"
    # ব্রাউজারের মতো অভিনয় করার জন্য শক্তিশালী হেডার
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        # যদি এনকোডিং সমস্যা থাকে তা ফিক্স করা
        response.encoding = 'utf-8' 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # সব টেবিল খুঁজে বের করা
        tables = soup.find_all('table')
        
        results = {"gold": {}, "silver": {}}

        # ডাটা ক্লিন করার ফাংশন
        def clean_text(text):
            return text.replace('\n', '').replace('\t', '').strip()

        if len(tables) >= 1:
            # সোনার ডাটা (প্রথম টেবিল)
            rows = tables[0].find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    key = clean_text(cols[0].text)
                    val = clean_text(cols[1].text)
                    if "K" in key or "Traditional" in key:
                        results["gold"][key] = val

        if len(tables) >= 2:
            # রুপার ডাটা (দ্বিতীয় টেবিল)
            rows = tables[1].find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    key = clean_text(cols[0].text)
                    val = clean_text(cols[1].text)
                    if "K" in key or "Traditional" in key:
                        results["silver"][key] = val

        # যদি ডাটা তবুও না পাওয়া যায় (বিকল্প পদ্ধতি)
        if not results["gold"]:
             return {"status": "error", "message": "Could not find data on the page. Website structure might have changed."}

        return {"status": "success", "data": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
