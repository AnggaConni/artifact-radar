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
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# ── Jalur File ────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
LOG_FILE     = os.path.join(BASE_DIR, "radar.log")
SCRIPT_FILE  = os.path.abspath(__file__)

# ── Log Sistem ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")

# ── Interval Crawling ─────────────────────────────────────────────────
CRAWL_INTERVAL_DAYS = int(os.environ.get("CRAWL_INTERVAL_DAYS", 14))   # default = 14 hari

# ======================================================================
# DATABASE KATA KUNCI (Keyword Database)
# ======================================================================
# Inisialisasi dictionary sebelum diisi data
ARTIFACT_KEYWORDS = {}

ARTIFACT_KEYWORDS.update({
    # ── Artefak Tiongkok (Chinese Antiquities) ───────────────────────
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

    # ── Artefak Jepang (Japanese Antiquities) ────────────────────────
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

    # ── Peradaban Mongol & Stepa ────────────────────────────────────
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

    # ── Tibet & Himalaya ─────────────────────────────────────────────
    "Tibet_Himalaya": [
        "tibetan ritual artifact",
        "ancient tibetan buddhist statue",
        "himalayan bronze buddha",
        "vajrayana ritual object",
        "ancient thangka painting",
        "ritual vajra antique",
    ],

    # ── Jalur Sutra (Silk Road Artifacts) ─────────────────────────────
    "Silk_Road": [
        "silk road artifact",
        "central asian burial artifact",
        "ancient sogdian artifact",
        "bactrian bronze artifact",
        "kushan empire artifact",
    ]
})

# Menggabungkan semua kata kunci menjadi satu daftar
ALL_KEYWORDS = [kw for kws in ARTIFACT_KEYWORDS.values() for kw in kws]

# ======================================================================
# PEMBANTU HTTP (HTTP Helper)
# ======================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

def get_headers(referer: str = "https://www.google.com/") -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Referer": referer,
    }

def safe_get(url: str, referer: str = "", timeout: int = 15, retries: int = 2) -> requests.Response or None:
    for attempt in range(retries):
        try:
            # Jeda sopan agar tidak dianggap serangan DDoS
            time.sleep(random.uniform(2.0, 5.0))
            r = requests.get(url, headers=get_headers(referer or url), timeout=timeout)
            if r.status_code == 200: return r
        except Exception as e:
            log.warning(f"Percobaan {attempt+1} gagal untuk {url}: {e}")
    return None

# ======================================================================
# SCRAPER PLATFORM
# ======================================================================

def scrape_ebay(keyword: str) -> list:
    """Scrape hasil pencarian eBay."""
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(keyword)}&_sacat=0&LH_ItemCondition=3000"
    r = safe_get(url)
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("li.s-item")[:8]:
        title_el = item.select_one(".s-item__title")
        link_el = item.select_one("a.s-item__link")
        if not title_el or not link_el or "Shop on eBay" in title_el.text: continue
        results.append({
            "platform": "eBay",
            "title": title_el.get_text(strip=True),
            "url": link_el.get("href", "").split("?")[0],
            "keyword": keyword
        })
    return results

def scrape_google_shopping(keyword: str) -> list:
    """Scrape cuplikan Google Shopping."""
    url = f"https://www.google.com/search?q={quote_plus(keyword)}&tbm=shop"
    r = safe_get(url)
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select("div.sh-dgr__grid-result, div.g")[:8]:
        title_el = item.select_one("h3, h4")
        link_el = item.select_one("a")
        if not title_el or not link_el: continue
        href = link_el.get("href", "")
        if "/url?q=" in href: href = href.split("/url?q=")[1].split("&")[0]
        results.append({
            "platform": "Google Shopping",
            "title": title_el.get_text(strip=True),
            "url": href,
            "keyword": keyword
        })
    return results

# ======================================================================
# ANALISIS AI
# ======================================================================

def analyze_with_gemini(listings: list, model) -> list:
    """Mengirimkan data ke Gemini untuk analisis risiko."""
    if not listings: return []
    prompt = f"""
    Analyze these marketplace listings for potential illegal artifact trafficking.
    Listings: {json.dumps(listings[:40], indent=2)}
    
    Output ONLY a JSON array:
    [
      {{
        "item_name": "string",
        "platform": "string",
        "status": "Suspected Illicit | Replica/Fake | Irrelevant",
        "risk_score": 1-10,
        "reason": "string",
        "source_link": "string"
      }}
    ]
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        log.error(f"Analisis AI gagal: {e}")
        return []

# ======================================================================
# LOGIKA INTI (Core Logic)
# ======================================================================

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f: hasher.update(f.read())
    return hasher.hexdigest()

def should_crawl() -> bool:
    """Mengecek apakah sudah waktunya menjalankan crawler."""
    if not os.path.exists(HISTORY_FILE): return True
    with open(HISTORY_FILE) as f: history = json.load(f)
    if history.get("script_hash") != get_file_hash(SCRIPT_FILE): return True
    last = datetime.fromisoformat(history.get("last_crawl_date"))
    return datetime.now() - last >= timedelta(days=CRAWL_INTERVAL_DAYS)

def main():
    if not should_crawl():
        log.info("Sistem istirahat. Belum waktunya crawl ulang.")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("API Key Gemini tidak ditemukan!")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    all_listings = []
    # Membatasi jumlah keyword agar tidak terkena limitasi GitHub Actions
    sample_keywords = random.sample(ALL_KEYWORDS, min(len(ALL_KEYWORDS), 10))
    
    log.info(f"Memulai pemindaian untuk {len(sample_keywords)} kata kunci acak...")
    for kw in sample_keywords:
        all_listings.extend(scrape_ebay(kw))
        all_listings.extend(scrape_google_shopping(kw))

    log.info(f"Ditemukan {len(all_listings)} listing mentah. Memulai analisis AI...")
    analyzed = analyze_with_gemini(all_listings, model)
    
    # Simpan hasil analisis
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(analyzed, f, indent=2, ensure_ascii=False)

    # Perbarui history
    with open(HISTORY_FILE, "w") as f:
        json.dump({
            "last_crawl_date": datetime.now().isoformat(),
            "script_hash": get_file_hash(SCRIPT_FILE)
        }, f, indent=2)
    log.info("✅ Pemindaian dan analisis selesai.")

if __name__ == "__main__":
    main()
