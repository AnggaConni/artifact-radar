# 🏺 Artifact Radar v5.1 — Global Intelligence Engine 

An automated cultural-heritage protection and geo-intelligence tool. It monitors the global online antiquities market for listings that may involve stolen, looted, or unprovenanced artifacts.

Powered by Google Gemini 2.5 Flash with Google Search Grounding, the engine autonomously crawls marketplaces, news outlets, and forums every 8 days, classifying risks and mapping the origins of suspicious artifacts.

---

## 🏗️ Architecture

Unlike traditional scrapers that get blocked, Artefact Radar v5.1 delegates the search process entirely to Google's infrastructure via AI Tool Grounding, utilising direct REST API calls for maximum stability. This advanced approach ensures that even search results and listings that actively block traditional crawlers can still be detected and analyzed by the AI.


```
GitHub Actions (Daily Cron)
        │
        ▼
  scraper.py (8-Day Interval Guard)
        │
        ├──► Gemini 2.5 Flash REST API + Google Search Tool
        │      ├── Scans global keywords (eBay, Facebook, Forums, Auctions)
        │      └── Extracts strict JSON (Title, Risk, Origin, Provenance)
        │
        ├──► Microlink.io API
        │      └── Generates & backfills missing screenshot URLs
        │
        ▼
  data.json & history.json
        │
        ▼
  Git Commit & Push ──► GitHub Pages ──► Interactive Dashboard & Map
```

---

## Output: `data.json`

```json
{
  "summary": {
    "generated_at": "2025-10-25T02:43:12Z",
    "total_listings": 1240,
    "high_risk_count": 37,
    "medium_risk_count": 112,
    "alerts_by_platform": { "eBay": 14, "Facebook": 8, "Sotheby's": 1 },
    "top_high_risk": [ ... ]
  },
  "listings": [
    {
      "original_title": "Ancient Majapahit Bronze Shiva, NO PROVENANCE",
      "platform": "eBay",
      "url": "https://...",
      "price_usd": 4500,
      "status": "HIGH RISK",
      "risk_score": 9,
      "origin_region": "Southeast Asia — Java, Indonesia",
      "provenance_flag": false,
      "keyword_trigger": "majapahit artifact for sale",
      "reason": "Bronze deity matching known Majapahit iconography, seller explicitly states no provenance documents.",
      "scraped_at": "2025-10-25T02:41:00Z",
      "screenshot_url": "[https://api.microlink.io/?url=](https://api.microlink.io/?url=)..."
    }
  ]
}
```

---

## Setup

### 1. Add your Gemini API key
In your GitHub repository → **Settings → Secrets and variables → Actions**:

| Secret name    | Value                   |
|----------------|-------------------------|
| `GEMINI_API_KEY` | Your Google Gemini key |

Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 2. Place files
```
your-repo/
├── .github/workflows/
│   └── crawler.yml         # GitHub Actions workflow
├── scraper.py              # Main Python intelligence engine
├── index.html              # The Dashboard UI
├── data.json               # Auto-generated results (committed by bot)
└── history.json            # Crawl state tracker (committed by bot)
```

### 3. Run manually

Run Manually (Bypass 8-Day Guard)

Go to Actions → Artifact Radar Auto-Crawler → Run workflow.

Set Force crawl now to true if you want to bypass the 8-day waiting period and scan immediately.

---

## Schedule

The crawler runs on an interval of 8 days.

A built-in 8-day guard in `scraper.py` also prevents redundant re-runs if the workflow is triggered too soon (e.g., after a `git push`).

To change the interval, edit `CRAWL_INTERVAL_DAYS` in `scraper.py`.


---

## Adding more keywords

Edit `ARTIFACT_KEYWORDS` in `scraper.py`:

```python
KEYWORDS = [
    # Add your targeted search patterns here:
    "Roman glass unguentarium sale",
    "stolen archaeological artefact alert",
    "Mayan stela fragment sale"
]
```

⚖️ Disclaimer

This tool is intended for cultural-heritage protection, academic research, and law-enforcement support purposes only, consistent with the 1970 UNESCO Convention on the Means of Prohibiting and Preventing the Illicit Import, Export and Transfer of Ownership of Cultural Property and the UNIDROIT 1995 Convention on stolen cultural objects.

License: MIT
