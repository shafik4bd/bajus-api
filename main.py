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

# এই রুটটি নিশ্চিত করবে যে হোম পেজে কিছু দেখাচ্ছে
@app.get("/")
def read_root():
    return {"status": "Success", "message": "Welcome to Gold Price API. Access /prices for data."}

@app.get("/prices")
def get_prices():
    url = "https://www.bajus.org/gold-price"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        results = {"gold": {}, "silver": {}}
        if len(tables) >= 1:
            for row in tables[0].find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    results["gold"][cols[0].text.strip()] = cols[1].text.strip()
        if len(tables) >= 2:
            for row in tables[1].find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    results["silver"][cols[0].text.strip()] = cols[1].text.strip()
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
