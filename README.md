# 🏺 Artifact Radar v6.0 — Global Intelligence Engine 

An automated cultural-heritage protection and geo-intelligence tool. It monitors the global online antiquities market for listings that may involve stolen, looted, or unprovenanced artifacts.

Powered by Google Gemini 2.5 Flash with Google Search Grounding, the engine autonomously crawls marketplaces, news outlets, and forums every 8 days, classifying risks and mapping the origins of suspicious artifacts.

**v6.0** adds a **multi-agent pipeline**: **Collector** (search-grounded candidates) → **Classifier** (ICOM-style rubric) → **Reasoner** (narrative, uncertainty flags, evidence gaps). Append-only **step logs** default to `pipeline.jsonl`. If collection or classification fails or is empty, a **repair pass** re-prompts with a narrower, factual prompt.

---

## 🏗️ Architecture

Unlike traditional scrapers that get blocked, Artifact Radar delegates discovery to Google's infrastructure via AI Tool Grounding and direct REST calls. (If a listing thumbnail shows "Image Unavailable", the host may block embeds—the listing was still found via search grounding.)


```
GitHub Actions (Daily Cron)
        │
        ▼
  scraper.py (8-Day Interval Guard)
        │
        ▼
  artifact_radar/orchestrator.py
        │
        ├──► Collector — Gemini + Google Search → candidate URLs (JSON)
        │      └── Repair collector if empty / failed
        ├──► Classifier — Gemini → status, risk_score, provenance_flag
        │      └── Repair classifier if parse / call failed
        ├──► Reasoner — synthesis → reason, uncertainty_flags, confidence
        │
        ├──► Microlink.io screenshots + normalized URL dedupe
        │
        ▼
  data.json, history.json, pipeline.jsonl (optional)
        │
        ▼
  Git Commit & Push ──► GitHub Pages ──► Dashboard & Map
```

Listings may include a **`pipeline`** metadata object (`uncertainty_flags`, `evidence_that_would_change_assessment`, `confidence`, repair-pass flags). The dashboard renders these on each card when present; XML export adds matching `dcterms:*` extension fields.

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Required |
| `FORCE_CRAWL` | `true` bypasses 8-day guard |
| `ARTIFACT_PIPELINE_LOG` | JSONL log path (default `./pipeline.jsonl`). Empty string disables file logging |
| `ARTIFACT_MAX_CANDIDATES_PER_KEYWORD` | Cap listings processed per keyword after collection (default `5`, max `15`) |

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
├── artifact_radar/         # Multi-agent pipeline package
├── scraper.py              # Entrypoint + schedule + persistence
├── index.html              # The Dashboard UI
├── data.json               # Auto-generated results (committed by bot)
├── history.json            # Crawl state tracker (committed by bot)
└── pipeline.jsonl          # Step log (local / optional commit)
```

### 3. Run manually

Run Manually (Bypass 8-Day Guard)

Go to Actions → Artifact Radar Auto-Crawler → Run workflow.

Set Force crawl now to true if you want to bypass the 8-day waiting period and scan immediately.

### 4. Run tests (local)

```bash
pip install -r requirements-dev.txt
pytest
```

On GitHub, the **Tests** workflow runs `pytest` on every push and pull request to `main` / `master`.

---

## Schedule

The crawler runs on an interval of 8 days.

A built-in 8-day guard in `scraper.py` also prevents redundant re-runs if the workflow is triggered too soon (e.g., after a `git push`).

To change the interval, edit the day check in `check_schedule()` in `scraper.py` (currently 8 days).


---

## Adding more keywords

Edit `KEYWORDS` in `scraper.py`:

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

License: AGPL
