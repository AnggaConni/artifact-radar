# 🏺 Artifact Radar

Automated cultural-heritage protection tool that monitors major online marketplaces for listings that may involve stolen or looted artifacts. Runs on GitHub Actions every **2 weeks** and uses **Google Gemini AI** to classify risk.

---

## Architecture

```
GitHub Actions (bi-weekly cron)
        │
        ▼
  scraper.py  ──────────────────────────────────────────────────────────┐
        │                                                                │
        ▼                                                                ▼
  PHASE 1 — Crawl                                              PHASE 2 — AI Analysis
  ├── eBay               (direct HTTP)                         Gemini 2.5 Flash
  ├── Etsy               (direct HTTP)                         ├── Risk classification
  ├── Amazon             (direct HTTP)                         ├── Origin region detection
  ├── OLX Indonesia      (direct HTTP)                         ├── Provenance flag check
  ├── Carousell          (direct HTTP)                         └── Risk score 1–10
  ├── Tokopedia          (DuckDuckGo proxy)
  ├── Shopee ID/SG/MY    (DuckDuckGo proxy)
  └── Facebook Marketplace (DuckDuckGo proxy)
        │
        ▼
  data.json  +  history.json  →  git push → repository
```

---

## Output: `data.json`

```json
{
  "summary": {
    "generated_at": "2025-01-15T02:43:12Z",
    "total_listings": 1240,
    "high_risk_count": 37,
    "medium_risk_count": 112,
    "alerts_by_platform": { "eBay": 14, "Etsy": 8, "Tokopedia": 7 },
    "top_high_risk": [ ... ]
  },
  "listings": [
    {
      "original_title": "Ancient Majapahit Bronze Shiva, NO PROVENANCE, private sale",
      "platform": "eBay",
      "url": "https://...",
      "price_usd": 4500,
      "status": "HIGH RISK",
      "risk_score": 9,
      "origin_region": "Southeast Asia — Java, Indonesia",
      "provenance_flag": false,
      "keyword_trigger": "majapahit bronze statue sale",
      "reason": "Bronze deity matching known Majapahit iconography, seller explicitly states no provenance documents, priced below auction market value.",
      "scraped_at": "2025-01-15T02:41:00Z"
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
├── .github/
│   └── workflows/
│       └── crawler.yml      ← GitHub Actions workflow
├── scraper.py               ← Main scraper
├── data.json                ← Auto-generated results (committed by bot)
├── history.json             ← Crawl state tracker (committed by bot)
└── scraper.log              ← Latest run log (uploaded as artifact)
```

### 3. Run manually
Go to **Actions → Artifact Radar Auto Crawler → Run workflow**.

---

## Schedule

The crawler runs on the **1st and 15th of every month at 02:00 UTC**.

A built-in 14-day guard in `scraper.py` also prevents redundant re-runs if the workflow is triggered too soon (e.g., after a `git push`).

To change the interval, edit `CRAWL_INTERVAL_DAYS` in `scraper.py`.

---

## Adding more keywords

Edit `ARTIFACT_KEYWORDS` in `scraper.py`:

```python
ARTIFACT_KEYWORDS = [
    "belitung shipwreck artifact sale",
    "your new keyword here",   # ← add here
    ...
]
```

---

## Limitations & Notes

| Platform | Method | Notes |
|----------|--------|-------|
| eBay | Direct HTTP | Works well; rich structured data |
| Etsy | Direct HTTP | Works; may return fewer results |
| Amazon | Direct HTTP | May be rate-limited; adds captchas |
| OLX ID | Direct HTTP | Works for Indonesian listings |
| Carousell | Direct HTTP | Partial (static HTML only) |
| Tokopedia | DuckDuckGo proxy | Indirect; limited depth |
| Shopee (ID/SG/MY) | DuckDuckGo proxy | Indirect; limited depth |
| Facebook Marketplace | DuckDuckGo proxy | Very limited — FB blocks crawlers heavily |

For deeper FB/Shopee/Tokopedia coverage, consider integrating:
- [Apify](https://apify.com) marketplace scrapers
- [Oxylabs](https://oxylabs.io) or [BrightData](https://brightdata.com) residential proxies
- Official marketplace APIs where available

---

## Disclaimer

This tool is intended for cultural-heritage protection research and law-enforcement support purposes only, consistent with the 1970 UNESCO Convention and UNIDROIT 1995 Convention on stolen cultural objects.
