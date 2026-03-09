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
    return {"message": "BAJUS Gold Apir is Live! Visit /prices"}

@app.get("/prices")
def get_prices():
    url = "https://www.bonikbarta.com/gold-price"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # বণিক বার্তার টেবিলে সাধারণত গোল্ড ও সিলভারের দাম থাকে
        tables = soup.find_all('table')
        
        results = {"gold": {}, "silver": {}}

        if len(tables) >= 1:
            # প্রথম টেবিল সাধারণত সোনার জন্য
            rows = tables[0].find_all('tr')
            for row in rows[1:]: # হেডার বাদ দিয়ে
                cols = row.find_all('td')
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    results["gold"][label] = value

        if len(tables) >= 2:
            # দ্বিতীয় টেবিল সাধারণত রুপার জন্য
            rows = tables[1].find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    results["silver"][label] = value

        # যদি ডাটা পাওয়া যায়
        if results["gold"] or results["silver"]:
            return {"status": "success", "source": "Bonik Barta", "data": results}
        else:
            return {"status": "error", "message": "Table data not found on the page."}

    except Exception as e:
        return {"status": "error", "message": str(e)}
