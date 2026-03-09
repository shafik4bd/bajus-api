# BAJUS সোনা ও রুপার দাম API 🥇
**Python + Vercel Serverless Functions**

---

## ⚡ Vercel Deploy (৫ মিনিটে)

### ধাপ ১ — GitHub-এ push করুন
```bash
git init
git add .
git commit -m "BAJUS price API"
# GitHub-এ নতুন repo বানিয়ে push করুন
git remote add origin https://github.com/YOUR_USERNAME/bajus-price-api.git
git push -u origin main
```

### ধাপ ২ — Vercel deploy
1. [vercel.com/new](https://vercel.com/new) → GitHub repo import করুন
2. Framework: **Other** সিলেক্ট করুন
3. **Deploy** বাটন চাপুন → লিংক পেয়ে যাবেন ✅

### ধাপ ৩ — Cloudflare Bypass (ScraperAPI ফ্রি)
1. [scraperapi.com](https://scraperapi.com) → ফ্রি account → API Key কপি
2. Vercel → আপনার Project → **Settings → Environment Variables**
3. `SCRAPER_API_KEY` = `your_key_here` যোগ করুন
4. Redeploy করুন

---

## একটি লিংকে সব কিছু

| URL | কী পাবেন |
|---|---|
| `your-app.vercel.app/` | Live Dashboard |
| `your-app.vercel.app/api/prices` | সোনা + রুপার দাম (JSON) |
| `your-app.vercel.app/api/prices/gold` | শুধু সোনা (JSON) |
| `your-app.vercel.app/api/prices/silver` | শুধু রুপা (JSON) |

---

## Cloudflare Bypass — ৩ স্তর

| স্তর | পদ্ধতি | সফলতার হার |
|---|---|---|
| ১ | Browser headers দিয়ে সরাসরি | ~৬০% |
| ২ | Google Cache | ~৮০% |
| ৩ | ScraperAPI (key দিলে) | ~৯৯% |

---

## Project Structure

```
bajus-python-api/
├── vercel.json                     # Vercel config
├── requirements.txt                # Python packages
├── api/
│   ├── _scraper.py                 # Core scraper (shared)
│   └── prices/
│       ├── index.py                # GET /api/prices
│       ├── gold/index.py           # GET /api/prices/gold
│       └── silver/index.py         # GET /api/prices/silver
└── public/
    └── index.html                  # Live dashboard
```
