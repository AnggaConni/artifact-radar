"""
=======================================================================
  ARTIFACT RADAR v4.1 — Advanced Global Intelligence
  AI Engine : Google Gemini 1.5 Flash (Google Search Grounding)
  Fixes     : Bypassing SDK Bugs with Direct REST API Calls
=======================================================================
"""

import os
import json
import hashlib
import logging
import random
import re
from datetime import datetime
import requests

# ── Logging Configuration ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")

# ── File Paths ──
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE  = os.path.abspath(__file__)

KEYWORDS = [
    # ── English Keywords ──
    "ancient artifact for sale", "authentic antiquities for sale", "buy ancient artifact online",
    "illegal antiquities trafficking", "stolen archaeological artifact", "majapahit artifact for sale",
    "khmer statue ancient for sale", "roman artifact authentic sale", "egyptian antiquities original",
    "ancient bronze statue authentic", "ancient artifact site:ebay.com", "ancient relic site:etsy.com",
    "antiquities sale site:facebook.com", "illegal antiquities trafficking news", "artifact smuggling investigation",
    "antique archaeological artifact sale", "genuine ancient relic for collectors", "museum quality artifact for sale",
    "rare antiquities private collection sale", "ancient relic dealer listing", "looted artifact for sale",
    "ancient relic no provenance", "artifact found metal detector sale", "burial artifact excavation find",
    "ancient relic found in field", "artifact discovered during excavation", "angkor artifact dealer",
    "greek antiquities dealer", "mesopotamian cuneiform tablet sale", "persian ancient artifact dealer",
    "han dynasty artifact for sale", "ming dynasty porcelain antique sale", "song dynasty celadon bowl sale",
    "jomon pottery artifact", "kofun haniwa figure sale", "mongol empire artifact", "scythian gold artifact",
    "steppe nomad bronze artifact", "ancient jade artifact for sale", "ritual bronze vessel ancient",
    "ancient burial figurine", "temple stone fragment ancient", "ancient coin hoard sale",
    "ancient pottery shard archaeological", "ancient ritual object antique", "ancient religious statue original",
    "ancient artifact site:auction house", "ancient artifact collector forum", "museum artifact repatriation case",
    "looted antiquities returned to museum", "archaeological theft investigation",

    # ── Indonesian Keywords (Lokal) ──
    "jual arca kuno asli", "benda purbakala asli dijual", "temuan arkeologi dijual",
    "artefak candi dijual", "keris kuno asli dijual", "jual artefak kuno majapahit"
]

# ======================================================================
# DATA PERSISTENCE & MIGRATION
# ======================================================================

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    log.info("Migrating old list data to new structured JSON...")
                    return {"summary": {}, "listings": data}
                return data
        except Exception as e:
            log.warning(f"Old database corrupted, starting fresh: {e}")
            
    return {"summary": {}, "listings": []}

def get_hash(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f: h.update(f.read())
        return h.hexdigest()
    except: return "none"

def check_schedule():
    # SELALU JALAN: Diaktifkan sementara untuk testing
    return True 

def calculate_summary(listings):
    high_risk = [x for x in listings if x.get("risk_score", 0) >= 8]
    medium_risk = [x for x in listings if 4 <= x.get("risk_score", 0) <= 7]
    
    platforms = {}
    for item in listings:
        plat = item.get("platform", "Unknown")
        platforms[plat] = platforms.get(plat, 0) + 1
        
    top_high_risk = sorted(high_risk, key=lambda x: x.get("risk_score", 0), reverse=True)[:5]
    
    return {
        "generated_at": datetime.now().isoformat() + "Z",
        "total_listings": len(listings),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "alerts_by_platform": platforms,
        "top_high_risk": top_high_risk
    }

# ======================================================================
# CORE: DIRECT REST API AI ANALYZER
# ======================================================================

def run_ai_search(api_key, existing_urls, target):
    """
    Menggunakan API request langsung untuk menghindari bug pada library Python SDK.
    """
    log.info(f"Targeting: {target}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Gunakan Google Search untuk mencari listing penjualan atau berita nyata mengenai: "{target}".
    Identifikasi marketplace (eBay, FB, Tokopedia), berita pencurian, atau forum kolektor.
    
    Output hasil pencarian HANYA dalam format JSON Array objects.
    Abaikan URL yang sudah ada ini: {list(existing_urls)[:5]}
    
    Struktur JSON Wajib:
    [
      {{
        "original_title": "Judul asli barang atau artikel berita",
        "platform": "Nama Website (contoh: eBay, BBC, Facebook)",
        "url": "URL Lengkap",
        "price_usd": 0,
        "status": "HIGH RISK", 
        "risk_score": 9,
        "origin_region": "Wilayah asal artefak (contoh: Southeast Asia, Middle East)",
        "provenance_flag": false,
        "keyword_trigger": "{target}",
        "reason": "Alasan detail terkait asal usul atau harga",
        "scraped_at": "{datetime.now().isoformat()}Z"
      }}
    ]
    """
    
    # Payload langsung menembak server Google Gemini dengan Grounding Search Tool
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Akan memunculkan error jika HTTP status bukan 200 OK
        data = response.json()
        
        # Ekstrak text dari struktur JSON Google
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            log.error(f"Format respon API tidak terduga: {json.dumps(data)[:200]}")
            return []
            
        log.info(f"Raw AI Output: {text[:150]}...")
        
        # BULLETPROOF JSON EXTRACTOR
        clean_text = text.replace('```json', '').replace('```', '')
        clean_text = re.sub(r'\[\d+\]', '', clean_text)
        
        start_idx = clean_text.find('[')
        end_idx = clean_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = clean_text[start_idx:end_idx+1]
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                log.error(f"JSON Parse Error: {e}")
                return []
        else:
            log.warning("AI did not provide valid JSON Array.")
            return []
            
    except Exception as e:
        log.error(f"AI Search Failed for '{target}': {e}")
        return []

def main():
    if not check_schedule():
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY not found!")
        return 

    try:
        db = load_db()
        listings = db.get("listings", [])
        
        existing_urls = {i.get('url') or i.get('source_link') for i in listings if i.get('url') or i.get('source_link')}

        local_kws = [k for k in KEYWORDS if "jual" in k or "dijual" in k]
        intl_kws = [k for k in KEYWORDS if k not in local_kws]
        
        targets = random.sample(intl_kws, 2) + random.sample(local_kws, 1)
        
        count = 0
        for target in targets:
            # Langsung mengoper api_key ke fungsi kita (tanpa library bawaan google)
            new_items = run_ai_search(api_key, existing_urls, target)
            
            if isinstance(new_items, list):
                for item in new_items:
                    link = item.get('url')
                    if link and link not in existing_urls:
                        item['scraped_at'] = datetime.now().isoformat() + "Z"
                        item['keyword_trigger'] = target
                        listings.append(item)
                        existing_urls.add(link)
                        count += 1

        db["listings"] = listings
        db["summary"] = calculate_summary(listings)

        if count > 0 or not db["summary"].get("generated_at"):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)

        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "last_crawl_date": datetime.now().isoformat(),
                "script_hash": get_hash(SCRIPT_FILE)
            }, f, indent=2)
            
        log.info(f"✅ Selesai. Ditambahkan {count} data baru. Total Listing: {len(listings)}.")

    except Exception as e:
        log.error(f"Fatal Error pada proses utama: {e}")

if __name__ == "__main__":
    main()
