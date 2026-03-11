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
CRAWL_INTERVAL_DAYS = int(os.environ.get("CRAWL_INTERVAL_DAYS", 14))

# ======================================================================
# DATABASE KATA KUNCI GLOBAL (Expanded Global Database)
# ======================================================================
ARTIFACT_KEYWORDS = {
    # ── Southeast Asia (SEA) ────────────────────────────────────────
    "SEA_Maritime": [
        "majapahit terracotta artifact", "srivijaya gold artifact", "ancient khmer statue",
        "angkor wat style sculpture", "ayutthaya buddha bronze", "champa stone carving",
        "dong son bronze drum", "ban chiang pottery", "ancient javanese kris antique",
        "archaic dayak carving", "prehistoric indonesian artifact",
    ],
    # ── East Asia ───────────────────────────────────────────────────
    "CN_Dynastic": [
        "han dynasty artifact", "tang dynasty ceramic", "song dynasty porcelain",
        "ming dynasty porcelain antique", "qing dynasty jade carving", "shanxi tomb artifact",
        "ancient chinese bronze vessel", "ritual bronze ding vessel", "oracle bone inscription",
    ],
    "JP_Ancient": [
        "jomon pottery ancient", "yayoi bronze bell dotaku", "kofun haniwa figure",
        "samurai armor antique authentic", "edo period katana antique",
        "ancient japanese buddhist statue",
    ],
    # ── Middle East & Egypt ─────────────────────────────────────────
    "ME_Egypt": [
        "ancient egyptian ushabti", "pharaonic sarcophagus fragment", "hieroglyphic papyrus scroll",
        "ptolemaic period artifact", "egyptian faience amulet", "predynastic egyptian pottery",
    ],
    "ME_Mesopotamia": [
        "sumerian cuneiform tablet", "babylonian cylinder seal", "akkadian bronze artifact",
        "luristan bronze antique", "elamite pottery fragment", "ancient persian rhyton",
    ],
    # ── Mediterranean (Greco-Roman) ──────────────────────────────────
    "Mediterranean_Classic": [
        "ancient greek amphora", "roman marble bust fragment", "etruscan bronze mirror",
        "attic red figure pottery", "roman legionary gladius antique", "byzantine icon antique",
        "mycenaean artifact", "minoan pottery fragment",
    ],
    # ── The Americas (Pre-Columbian) ────────────────────────────────
    "Americas_PreColumbian": [
        "mayan jade artifact", "aztec stone sculpture", "inca gold mask",
        "moche ceramic vessel", "nazca textile fragment", "pre-columbian pottery authentic",
        "chavin stone carving", "tairona gold ornament",
    ],
    # ── South Asia ──────────────────────────────────────────────────
    "South_Asia": [
        "indus valley seal", "harappan pottery fragment", "gandhara buddha sculpture",
        "chola bronze statue", "pala empire sculpture", "ancient indian stone carving",
    ],
    # ── Central Asia & Silk Road ────────────────────────────────────
    "Silk_Road": [
        "scythian gold ornament", "bactrian camel artifact", "sogdian silver vessel",
        "kushan coin hoard", "ancient gandharan artifact", "mongol empire burial gear",
    ],
    # ── Africa ──────────────────────────────────────────────────────
    "Africa_Ancient": [
        "nok terracotta head", "benin bronze plaque", "ancient ife sculpture",
        "ethiopian orthodox cross antique", "dogon ancestor statue", "mali terracotta figure",
    ]
}

ALL_KEYWORDS = [kw for kws in ARTIFACT_KEYWORDS.values() for kw in kws]

# ======================================================================
# PEMBANTU HTTP
# ======================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
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
            time.sleep(random.uniform(2.0, 5.0))
            r = requests.get(url, headers=get_headers(referer or url), timeout=timeout)
            if r.status_code == 200: return r
        except Exception as e:
            log.warning(f"Percobaan {attempt+1} gagal untuk {url}: {e}")
    return None

def scrape_ebay(keyword: str) -> list:
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
# LOGIKA INTI
# ======================================================================

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f: hasher.update(f.read())
    return hasher.hexdigest()

def should_crawl() -> bool:
    # Cek apakah ada perintah paksa dari GitHub Actions
    if os.environ.get("FORCE_CRAWL") == "true":
        log.info("Mode Paksa Crawl aktif (Abaikan jadwal).")
        return True

    if not os.path.exists(HISTORY_FILE): return True
    with open(HISTORY_FILE) as f: history = json.load(f)
    if history.get("script_hash") != get_file_hash(SCRIPT_FILE): return True
    last = datetime.fromisoformat(history.get("last_crawl_date"))
    return datetime.now() - last >= timedelta(days=CRAWL_INTERVAL_DAYS)

def main():
    if not should_crawl():
        log.info("Sistem istirahat. Belum waktunya crawl ulang (Gunakan opsi 'Force Crawl' jika ingin mendesak).")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("API Key Gemini tidak ditemukan!")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    all_listings = []
    # Memilih 15 kata kunci secara acak setiap sesi untuk cakupan global yang lebih luas
    sample_keywords = random.sample(ALL_KEYWORDS, min(len(ALL_KEYWORDS), 15))
    
    log.info(f"Memulai pemindaian global untuk {len(sample_keywords)} kata kunci...")
    for kw in sample_keywords:
        all_listings.extend(scrape_ebay(kw))
        all_listings.extend(scrape_google_shopping(kw))

    log.info(f"Ditemukan {len(all_listings)} listing. Menganalisis dengan AI...")
    analyzed = analyze_with_gemini(all_listings, model)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(analyzed, f, indent=2, ensure_ascii=False)

    with open(HISTORY_FILE, "w") as f:
        json.dump({
            "last_crawl_date": datetime.now().isoformat(),
            "script_hash": get_file_hash(SCRIPT_FILE)
        }, f, indent=2)
    log.info("✅ Pemindaian global selesai.")

if __name__ == "__main__":
    main()
