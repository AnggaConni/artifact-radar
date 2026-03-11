"""
=======================================================================
  ARTIFACT RADAR v3.1 — Global Intelligence (Market, News, & Forums)
  AI Engine : Google Gemini 1.5 Flash (Google Search Grounding)
  Method    : Robust Incremental Update
=======================================================================
"""

import os
import json
import hashlib
import logging
import random
import re
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
# DATABASE KATA KUNCI GLOBAL
# ======================================================================
KEYWORDS = [
    "illegal antiquity trafficking news BBC",
    "looted artifacts for sale auction",
    "stolen khmer statues news 2024",
    "Egyptian artifact repatriation news",
    "illicit cultural property marketplace",
    "identifying looted antiquities forum discussion",
    "stolen majapahit gold news"
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
        except Exception as e:
            log.warning(f"Gagal memuat data lama: {e}")
            return []
    return []

def get_file_hash(filepath):
    try:
        hasher = hashlib.md5()
        with open(filepath, "rb") as f: hasher.update(f.read())
        return hasher.hexdigest()
    except: return "unknown"

def should_crawl():
    if os.environ.get("FORCE_CRAWL") == "true": return True
    if not os.path.exists(HISTORY_FILE): return True
    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
        last = datetime.fromisoformat(history.get("last_crawl_date"))
        return datetime.now() - last >= timedelta(days=1)
    except: return True

# ======================================================================
# CORE: GEMINI INTELLIGENCE WITH SEARCH
# ======================================================================

def fetch_and_analyze(model, existing_links):
    target = random.choice(KEYWORDS)
    log.info(f"Targeting: {target}")
    
    prompt = f"""
    Using Google Search, find the latest information about: "{target}".
    
    Identify:
    1. MARKETPLACE: Listings of potentially illicit/stolen artifacts.
    2. NEWS: Recent articles about looting, smuggled artifacts, or repatriations.
    3. FORUMS: Online discussions about suspicious ancient objects.

    Output format: STRICT JSON ARRAY only.
    Exclude these URLs: {list(existing_links)[:5]}
    
    JSON Structure:
    [
      {{
        "item_name": "Headline or Product Name",
        "source_name": "Website Name",
        "source_type": "Marketplace | News | Forum",
        "status": "Suspected Illicit | Looting Report | Discussion",
        "risk_score": 1-10,
        "reason": "Analysis of relevance",
        "source_link": "Full URL",
        "price_info": "Price or N/A"
      }}
    ]
    """
    
    try:
        # Menjalankan AI dengan Grounding
        response = model.generate_content(prompt)
        text_output = response.text
        
        # Bersihkan output (terkadang AI memberikan backticks ```json)
        # Mencari teks di antara kurung siku [ ... ]
        json_match = re.search(r'\[.*\]', text_output, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        
        log.warning("AI tidak memberikan format JSON yang valid.")
        return []
    except Exception as e:
        log.error(f"Pencarian Gagal: {e}")
        return []

def main():
    if not should_crawl():
        log.info("Sistem dalam masa istirahat sesuai jadwal.")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY tidak ditemukan di GitHub Secrets!")
        exit(1) # Keluar dengan error agar user tahu API Key bermasalah

    try:
        genai.configure(api_key=api_key)
        
        # Perbaikan Nama Tool: google_search_retrieval adalah yang paling akurat saat ini
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{'google_search_retrieval': {}}]
        )

        # 1. Load data lama
        db = load_existing_data()
        existing_links = {item.get('source_link') for item in db if item.get('source_link')}

        # 2. Cari data baru
        new_findings = fetch_and_analyze(model, existing_links)
        
        # 3. Gabungkan (Incremental)
        added_count = 0
        if isinstance(new_findings, list):
            for item in new_findings:
                link = item.get('source_link')
                if link and link not in existing_links:
                    item['timestamp'] = datetime.now().isoformat()
                    db.append(item)
                    existing_links.add(link)
                    added_count += 1

        # 4. Simpan kembali ke file
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

        # 5. Simpan history
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "last_crawl_date": datetime.now().isoformat(),
                "script_hash": get_file_hash(SCRIPT_FILE)
            }, f, indent=2)
            
        log.info(f"✅ Sukses. Ditambahkan {added_count} data baru. Total database: {len(db)}")

    except Exception as e:
        log.error(f"Terjadi kesalahan fatal pada main: {e}")
        exit(1)

if __name__ == "__main__":
    main()
