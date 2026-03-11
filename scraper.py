"""
=======================================================================
  ARTIFACT RADAR v3 — Global Intelligence (Market, News, & Forums)
  AI Engine : Google Gemini 2.5 Flash (with Google Search Tool)
  Method    : Incremental Append + Multi-Source Monitoring
=======================================================================
"""

import os, json, hashlib, logging, random, re
from datetime import datetime, timedelta
import google.generativeai as genai

# ── Jalur File ────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE  = os.path.abspath(__file__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")

# ======================================================================
# DATABASE KATA KUNCI GLOBAL (Diverse Sources)
# ======================================================================
KEYWORDS = [
    # Marketplace Focus
    "rare majapahit artifact for sale", "authentic egyptian ushabti auction", 
    "ancient roman sword private listing", "pre-columbian pottery authentic for sale",
    # News & Reports Focus
    "stolen artifacts news BBC CNN", "illegal antiquity trafficking report 2024",
    "looted cultural heritage news", "repatriation of stolen artifacts news",
    # Forum & Community Focus
    "ancient coin identification forum reddit", "artifact collecting discussion illicit",
    "identifying looted antiquities forum"
]

# ======================================================================
# FUNGSI DATA PERSISTENCE
# ======================================================================

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []
    return []

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f: hasher.update(f.read())
    return hasher.hexdigest()

def should_crawl():
    if os.environ.get("FORCE_CRAWL") == "true": return True
    if not os.path.exists(HISTORY_FILE): return True
    with open(HISTORY_FILE) as f: history = json.load(f)
    last = datetime.fromisoformat(history.get("last_crawl_date"))
    return datetime.now() - last >= timedelta(days=1) # Diubah ke 1 hari agar lebih update

# ======================================================================
# CORE: GEMINI INTELLIGENCE WITH SEARCH
# ======================================================================

def fetch_and_analyze(model, existing_links):
    """
    Menggunakan Gemini untuk mencari di Marketplace, Berita, dan Forum.
    """
    target = random.choice(KEYWORDS)
    log.info(f"Targeting: {target}")
    
    prompt = f"""
    Using Google Search, find the latest information about: "{target}".
    
    I want to monitor three types of data:
    1. MARKETPLACE: Listings of potentially illicit/stolen artifacts.
    2. NEWS: Recent articles about looting, artifact smuggling, or seizures (e.g., from BBC, Al Jazeera).
    3. FORUMS: Discussions about suspicious or unidentified ancient objects.

    For each find, provide a JSON array. 
    EXCLUDE these existing links: {list(existing_links)[:10]}
    
    JSON Structure:
    [
      {{
        "item_name": "Title of listing or News headline",
        "source_name": "Name of the website (e.g., BBC News, eBay, Reddit)",
        "source_type": "Marketplace | News | Forum",
        "status": "Suspected Illicit | Looting Report | Discussion",
        "risk_score": 1-10,
        "reason": "Brief analysis of why this is relevant",
        "source_link": "Full URL",
        "price_info": "Price if applicable, or 'N/A'"
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text_output = response.text
        # Bersihkan output agar hanya JSON yang diambil
        json_match = re.search(r'\[.*\]', text_output, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return []
    except Exception as e:
        log.error(f"Pencarian Gagal: {e}")
        return []

def main():
    if not should_crawl():
        log.info("Sistem istirahat.")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{'google_search': {}}]
    )

    # 1. Load data lama
    db = load_existing_data()
    existing_links = {item.get('source_link') for item in db if item.get('source_link')}

    # 2. Cari data baru
    new_findings = fetch_and_analyze(model, existing_links)
    
    # 3. Gabungkan (Incremental)
    added_count = 0
    for item in new_findings:
        link = item.get('source_link')
        if link and link not in existing_links:
            item['timestamp'] = datetime.now().isoformat()
            db.append(item)
            existing_links.add(link)
            added_count += 1

    # 4. Simpan
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    with open(HISTORY_FILE, "w") as f:
        json.dump({
            "last_crawl_date": datetime.now().isoformat(),
            "script_hash": get_file_hash(SCRIPT_FILE)
        }, f, indent=2)
        
    log.info(f"✅ Selesai. Menambahkan {added_count} data baru. Total: {len(db)}")

if __name__ == "__main__":
    main()
