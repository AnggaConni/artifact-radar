"""
=======================================================================
  ARTIFACT RADAR — Multi-Platform Illegal Antiquity Detector
  Platforms : eBay · Etsy · Tokopedia · Shopee · Amazon · Craigslist
              + Google Shopping snippets (fallback for FB Marketplace)
  AI Engine : Google Gemini 2.5 Flash
  Schedule  : Every 2 weeks via GitHub Actions (also supports manual)
=======================================================================
"""

import os, json, re, time, hashlib, logging, random
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
LOG_FILE     = os.path.join(BASE_DIR, "radar.log")
SCRIPT_FILE  = os.path.abspath(__file__)

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")

# ── Crawl interval ────────────────────────────────────────────────────
CRAWL_INTERVAL_DAYS = int(os.environ.get("CRAWL_INTERVAL_DAYS", 14))   # default = 2 weeks

# ======================================================================
# KEYWORD DATABASE
# Categories: Southeast Asian · Middle Eastern · Greco-Roman · General
# ======================================================================
ARTIFACT_KEYWORDS.update({

    # ── Chinese Antiquities ─────────────────────────────────────────
    "CN_Dynastic": [
        "han dynasty artifact",
        "tang dynasty ceramic",
        "song dynasty porcelain",
        "ming dynasty porcelain antique",
        "qing dynasty jade carving",
        "shanxi tomb artifact",
        "ancient chinese bronze vessel",
        "ritual bronze ding vessel",
        "oracle bone inscription",
        "ancient chinese burial artifact",
    ],

    "CN_Objects": [
        "ancient chinese jade pendant",
        "chinese ritual bronze",
        "ancient chinese burial figurine",
        "terracotta tomb figure",
        "ming burial pottery",
        "ancient chinese coin string",
        "song dynasty celadon bowl",
        "tang sancai pottery",
        "ancient chinese lacquerware",
    ],

    # ── Japanese Antiquities ────────────────────────────────────────
    "JP_Ancient": [
        "jomon pottery ancient",
        "yayoi bronze bell dotaku",
        "kofun haniwa figure",
        "samurai armor antique authentic",
        "edo period katana antique",
        "ancient japanese temple artifact",
        "shinto ritual object antique",
        "japanese burial artifact kofun",
    ],

    "JP_Cultural": [
        "ancient netsuke original",
        "samurai tsuba antique",
        "edo period artifact",
        "ancient japanese buddhist statue",
        "temple bell japan antique",
    ],

    # ── Mongol & Steppe Civilizations ───────────────────────────────
    "Steppe_Mongol": [
        "mongol empire artifact",
        "mongolian burial artifact",
        "steppe nomad bronze ornament",
        "ancient steppe horse gear",
        "mongol warrior artifact",
        "scythian gold artifact",
        "xiongnu bronze artifact",
        "steppe burial treasure",
    ],

    # ── Tibetan & Himalayan ─────────────────────────────────────────
    "Tibet_Himalaya": [
        "tibetan ritual artifact",
        "ancient tibetan buddhist statue",
        "himalayan bronze buddha",
        "vajrayana ritual object",
        "ancient thangka painting",
        "ritual vajra antique",
    ],

    # ── Silk Road Artifacts ─────────────────────────────────────────
    "Silk_Road": [
        "silk road artifact",
        "central asian burial artifact",
        "ancient sogdian artifact",
        "bactrian bronze artifact",
        "kushan empire artifact",
    ],
}

# Flatten into a single list for iteration
ALL_KEYWORDS = [kw for kws in ARTIFACT_KEYWORDS.values() for kw in kws]

# ======================================================================
# HTTP HELPER
# ======================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def get_headers(referer: str = "https://www.google.com/") -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": referer,
        "DNT": "1",
    }

def safe_get(url: str, referer: str = "", timeout: int = 15, retries: int = 2) -> requests.Response | None:
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.5))          # polite delay
            r = requests.get(url, headers=get_headers(referer or url),
                             timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r
            log.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
    return None

# ======================================================================
# PLATFORM SCRAPERS
# ======================================================================

# ── eBay ──────────────────────────────────────────────────────────────
def scrape_ebay(keyword: str) -> list[dict]:
    """Scrape eBay search results for a keyword."""
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(keyword)}&_sacat=0&LH_ItemCondition=3000"
    r = safe_get(url, referer="https://www.ebay.com/")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("li.s-item")[:15]:
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        link_el  = item.select_one("a.s-item__link")
        if not title_el or not link_el:
            continue
        title = title_el.get_text(strip=True)
        if "Shop on eBay" in title:
            continue
        results.append({
            "platform": "eBay",
            "title": title,
            "price_raw": price_el.get_text(strip=True) if price_el else "N/A",
            "url": link_el.get("href", "").split("?")[0],
            "keyword": keyword,
        })
    log.info(f"  eBay: {len(results)} items for '{keyword}'")
    return results


# ── Etsy ──────────────────────────────────────────────────────────────
def scrape_etsy(keyword: str) -> list[dict]:
    url = f"https://www.etsy.com/search?q={quote_plus(keyword)}&explicit=1"
    r = safe_get(url, referer="https://www.etsy.com/")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("div[data-search-results-item]")[:10]:
        title_el = item.select_one("h3")
        price_el = item.select_one("span.currency-value")
        link_el  = item.select_one("a[href*='/listing/']")
        if not title_el or not link_el:
            continue
        results.append({
            "platform": "Etsy",
            "title": title_el.get_text(strip=True),
            "price_raw": price_el.get_text(strip=True) if price_el else "N/A",
            "url": "https://www.etsy.com" + link_el.get("href", "").split("?")[0],
            "keyword": keyword,
        })
    log.info(f"  Etsy: {len(results)} items for '{keyword}'")
    return results


# ── Tokopedia ─────────────────────────────────────────────────────────
def scrape_tokopedia(keyword: str) -> list[dict]:
    """
    Tokopedia renders via JS, but their search API endpoint is accessible.
    We fall back to Google-indexed Tokopedia pages if the API is blocked.
    """
    api_url = (
        f"https://ace.tokopedia.com/search/v2.5/product"
        f"?q={quote_plus(keyword)}&rows=20&start=0&source=search"
    )
    r = safe_get(api_url, referer="https://www.tokopedia.com/")
    results = []
    if r:
        try:
            data = r.json()
            for p in data.get("data", {}).get("products", [])[:15]:
                results.append({
                    "platform": "Tokopedia",
                    "title": p.get("name", ""),
                    "price_raw": f"IDR {p.get('price', {}).get('text_idr', 'N/A')}",
                    "url": p.get("url", ""),
                    "keyword": keyword,
                })
        except Exception:
            pass

    # Fallback: scrape the HTML search page
    if not results:
        url = f"https://www.tokopedia.com/search?st=product&q={quote_plus(keyword)}"
        r2 = safe_get(url, referer="https://www.tokopedia.com/")
        if r2:
            soup = BeautifulSoup(r2.text, "html.parser")
            for item in soup.select("div[data-testid='lstCL2ProductList'] a")[:12]:
                title = item.get("aria-label", "") or item.get_text(strip=True)
                href  = item.get("href", "")
                if title and href:
                    results.append({
                        "platform": "Tokopedia",
                        "title": title,
                        "price_raw": "N/A",
                        "url": href if href.startswith("http") else "https://www.tokopedia.com" + href,
                        "keyword": keyword,
                    })

    log.info(f"  Tokopedia: {len(results)} items for '{keyword}'")
    return results


# ── Shopee ────────────────────────────────────────────────────────────
def scrape_shopee(keyword: str) -> list[dict]:
    """
    Shopee has an internal search API. Region: ID (shopee.co.id).
    """
    api_url = (
        f"https://shopee.co.id/api/v4/search/search_items"
        f"?by=relevancy&keyword={quote_plus(keyword)}&limit=20&newest=0"
        f"&order=desc&page_type=search&version=2"
    )
    r = safe_get(api_url, referer="https://shopee.co.id/")
    results = []
    if r:
        try:
            data = r.json()
            for item in data.get("items", [])[:15]:
                info = item.get("item_basic", item)
                name     = info.get("name", "")
                price    = info.get("price", 0) / 100000  # Shopee stores in micro-IDR
                shop_id  = info.get("shopid", "")
                item_id  = info.get("itemid", "")
                url = f"https://shopee.co.id/product/{shop_id}/{item_id}"
                results.append({
                    "platform": "Shopee",
                    "title": name,
                    "price_raw": f"IDR {price:,.0f}",
                    "url": url,
                    "keyword": keyword,
                })
        except Exception as e:
            log.warning(f"Shopee JSON parse failed: {e}")

    log.info(f"  Shopee: {len(results)} items for '{keyword}'")
    return results


# ── Amazon ────────────────────────────────────────────────────────────
def scrape_amazon(keyword: str) -> list[dict]:
    url = f"https://www.amazon.com/s?k={quote_plus(keyword)}&i=collectibles"
    r = safe_get(url, referer="https://www.amazon.com/")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("div[data-component-type='s-search-result']")[:12]:
        title_el = item.select_one("h2 span")
        price_el = item.select_one("span.a-price > span.a-offscreen")
        link_el  = item.select_one("h2 a")
        if not title_el or not link_el:
            continue
        results.append({
            "platform": "Amazon",
            "title": title_el.get_text(strip=True),
            "price_raw": price_el.get_text(strip=True) if price_el else "N/A",
            "url": "https://www.amazon.com" + link_el.get("href", "").split("?")[0],
            "keyword": keyword,
        })
    log.info(f"  Amazon: {len(results)} items for '{keyword}'")
    return results


# ── Google Shopping (covers FB Marketplace + others via indexing) ──────
def scrape_google_shopping(keyword: str) -> list[dict]:
    """
    FB Marketplace requires login, so we rely on Google Shopping snippets
    which often index FB listings, plus Craigslist, local dealers, etc.
    """
    url = f"https://www.google.com/search?q={quote_plus(keyword)}&tbm=shop"
    r = safe_get(url, referer="https://www.google.com/")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("div.sh-dgr__grid-result, div.g")[:12]:
        title_el = item.select_one("h3, h4")
        price_el = item.select_one("span.a8Pemb, span[aria-label]")
        link_el  = item.select_one("a[href]")
        if not title_el:
            continue
        href = link_el.get("href", "") if link_el else ""
        if href.startswith("/url?q="):
            href = re.search(r"/url\?q=([^&]+)", href)
            href = href.group(1) if href else ""
        results.append({
            "platform": "Google Shopping",
            "title": title_el.get_text(strip=True),
            "price_raw": price_el.get_text(strip=True) if price_el else "N/A",
            "url": href,
            "keyword": keyword,
        })
    log.info(f"  Google Shopping: {len(results)} items for '{keyword}'")
    return results


# ── Craigslist ────────────────────────────────────────────────────────
def scrape_craigslist(keyword: str) -> list[dict]:
    url = f"https://www.craigslist.org/search/clt?query={quote_plus(keyword)}&category_auto=1"
    r = safe_get(url, referer="https://www.craigslist.org/")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("li.cl-search-result")[:10]:
        title_el = item.select_one(".cl-search-title, a.posting-title")
        price_el = item.select_one(".priceinfo")
        link_el  = item.select_one("a[href]")
        if not title_el:
            continue
        results.append({
            "platform": "Craigslist",
            "title": title_el.get_text(strip=True),
            "price_raw": price_el.get_text(strip=True) if price_el else "N/A",
            "url": link_el.get("href", "") if link_el else "",
            "keyword": keyword,
        })
    log.info(f"  Craigslist: {len(results)} items for '{keyword}'")
    return results


# ======================================================================
# ORCHESTRATOR — collect from all platforms
# ======================================================================
SCRAPERS = {
    "ebay":             scrape_ebay,
    "etsy":             scrape_etsy,
    "tokopedia":        scrape_tokopedia,
    "shopee":           scrape_shopee,
    "amazon":           scrape_amazon,
    "google_shopping":  scrape_google_shopping,
    "craigslist":       scrape_craigslist,
}

# Allow disabling specific platforms via env var  e.g. SKIP_PLATFORMS=shopee,amazon
SKIP = set(os.environ.get("SKIP_PLATFORMS", "").lower().split(","))

def collect_all_listings(keywords: list[str]) -> list[dict]:
    all_items = []
    seen_titles = set()

    for keyword in keywords:
        log.info(f"🔍 Keyword: '{keyword}'")
        for name, fn in SCRAPERS.items():
            if name in SKIP:
                continue
            try:
                items = fn(keyword)
                for item in items:
                    key = item["title"].lower().strip()
                    if key not in seen_titles and len(key) > 5:
                        seen_titles.add(key)
                        all_items.append(item)
            except Exception as e:
                log.error(f"  ❌ {name} scraper failed for '{keyword}': {e}")

    log.info(f"✅ Total unique listings collected: {len(all_items)}")
    return all_items


# ======================================================================
# SCHEDULING LOGIC
# ======================================================================
def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def should_crawl() -> bool:
    if os.environ.get("FORCE_CRAWL", "").lower() in ("1", "true", "yes"):
        log.info("FORCE_CRAWL is set — skipping schedule check.")
        return True
    if not os.path.exists(HISTORY_FILE):
        return True
    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except Exception:
        return True

    # Re-run if script changed
    if history.get("script_hash") != get_file_hash(SCRIPT_FILE):
        log.info("Script changed — forcing crawl.")
        return True

    # Re-run if interval elapsed
    last = history.get("last_crawl_date")
    if last:
        elapsed = datetime.now() - datetime.fromisoformat(last)
        if elapsed >= timedelta(days=CRAWL_INTERVAL_DAYS):
            log.info(f"Interval ({CRAWL_INTERVAL_DAYS}d) elapsed — crawling.")
            return True
        log.info(f"Next crawl in {CRAWL_INTERVAL_DAYS - elapsed.days} days. Exiting.")
        return False
    return True


# ======================================================================
# AI ANALYSIS — Gemini 2.5 Flash
# ======================================================================
SYSTEM_PROMPT = """
You are a forensic expert specialising in detecting the illegal trade of stolen antiquities
and looted cultural artifacts. Your jurisdictions include Southeast Asia (Indonesia, Malaysia,
Philippines, Vietnam, Thailand, Myanmar), South Asia, the Middle East (Iraq, Syria, Iran,
Afghanistan), and Greco-Roman antiquity markets.

You will receive raw marketplace listings. For each listing, determine:
1. Is this a genuine/suspected stolen or looted artifact, a modern replica, or irrelevant?
2. What is the risk score (1–10, where 10 = highly likely to be illicit)?
3. What specific red flags are present (no provenance, suspicious pricing, cultural sensitivity)?
4. Which jurisdiction / cultural heritage category does it belong to?

Respond ONLY with a valid JSON array, no preamble, no markdown fences.
"""

ANALYSIS_SCHEMA = """
[
  {
    "item_name": "string",
    "platform": "string",
    "price_usd": number_or_null,
    "price_raw": "string",
    "status": "Suspected Illicit | Replica/Fake | Legitimate Antique | Irrelevant",
    "risk_score": 1-10,
    "heritage_category": "string (e.g. Indonesian Maritime, Persian, Greco-Roman)",
    "red_flags": ["list", "of", "flags"],
    "reason": "string",
    "source_link": "string",
    "keyword_matched": "string"
  }
]
"""

def chunk_listings(listings: list[dict], size: int = 40) -> list[list[dict]]:
    return [listings[i:i+size] for i in range(0, len(listings), size)]

def analyze_with_gemini(listings: list[dict], model) -> list[dict]:
    analyzed = []
    chunks = chunk_listings(listings)
    log.info(f"Sending {len(listings)} listings to Gemini in {len(chunks)} batches…")

    for i, chunk in enumerate(chunks):
        prompt = f"""
{SYSTEM_PROMPT}

Here are {len(chunk)} marketplace listings to analyze:

{json.dumps(chunk, indent=2, ensure_ascii=False)}

Output format required:
{ANALYSIS_SCHEMA}
"""
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text.strip()
            # Strip any accidental markdown fences
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
            batch_result = json.loads(text)
            if isinstance(batch_result, list):
                analyzed.extend(batch_result)
                log.info(f"  Batch {i+1}/{len(chunks)}: {len(batch_result)} results")
        except Exception as e:
            log.error(f"  Batch {i+1} analysis failed: {e}")
        time.sleep(2)  # respect rate limit

    return analyzed


# ======================================================================
# OUTPUT HELPERS
# ======================================================================
def load_existing_data() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def merge_and_deduplicate(old: list[dict], new: list[dict]) -> list[dict]:
    """Keep all historical results; add new ones, avoiding exact duplicates."""
    seen = {(r.get("item_name", ""), r.get("source_link", "")) for r in old}
    merged = list(old)
    added = 0
    for item in new:
        key = (item.get("item_name", ""), item.get("source_link", ""))
        if key not in seen:
            item["first_seen"] = datetime.now().isoformat()
            merged.append(item)
            seen.add(key)
            added += 1
    log.info(f"Merged dataset: {len(merged)} total ({added} new)")
    return merged

def save_summary(data: list[dict]):
    """Print a quick human-readable risk summary."""
    high_risk = [d for d in data if d.get("risk_score", 0) >= 7]
    high_risk.sort(key=lambda x: -x.get("risk_score", 0))
    log.info("=" * 60)
    log.info(f"  HIGH-RISK DETECTIONS (score ≥ 7): {len(high_risk)}")
    for item in high_risk[:20]:
        log.info(
            f"  [{item.get('risk_score')}/10] {item.get('item_name', 'N/A')}"
            f"  | {item.get('platform', '')} | {item.get('price_raw', '')}"
        )
    log.info("=" * 60)


# ======================================================================
# MAIN
# ======================================================================
def main():
    log.info("🏺 Artifact Radar starting…")

    if not should_crawl():
        return

    # ── Gemini setup ─────────────────────────────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not set. Aborting.")
        return
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # ── Optional: limit keywords for faster CI runs ──────────────────
    max_kw = int(os.environ.get("MAX_KEYWORDS", len(ALL_KEYWORDS)))
    keywords = ALL_KEYWORDS[:max_kw]
    log.info(f"Using {len(keywords)} keywords across {len(SCRAPERS) - len(SKIP)} platforms")

    # ── Scrape ───────────────────────────────────────────────────────
    raw_listings = collect_all_listings(keywords)
    if not raw_listings:
        log.warning("No listings collected — check network / platform availability.")
        return

    # ── AI Analysis ──────────────────────────────────────────────────
    analyzed = analyze_with_gemini(raw_listings, model)
    if not analyzed:
        log.error("AI analysis returned empty results.")
        return

    # ── Merge with historical data ────────────────────────────────────
    old_data = load_existing_data()
    merged   = merge_and_deduplicate(old_data, analyzed)

    # ── Persist ──────────────────────────────────────────────────────
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    history = {
        "last_crawl_date": datetime.now().isoformat(),
        "script_hash": get_file_hash(SCRIPT_FILE),
        "total_records": len(merged),
        "new_records_this_run": len(analyzed),
        "high_risk_total": len([x for x in merged if x.get("risk_score", 0) >= 7]),
        "interval_days": CRAWL_INTERVAL_DAYS,
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    save_summary(merged)
    log.info(f"✅ Done. {len(merged)} records in data.json")


if __name__ == "__main__":
    main()
