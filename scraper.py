"""
=======================================================================
  ARTIFACT RADAR v3.5 — Ultra-Robust Intelligence Crawler
  AI Engine : Google Gemini 1.5 Flash
  Fixes     : Bulletproof JSON Extractor & Always-On Debug Mode
=======================================================================
"""

import os
import json
import hashlib
import logging
import random
import re
from datetime import datetime
import google.generativeai as genai

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
    "ancient artifact for sale",
    "authentic antiquities for sale",
    "buy ancient artifact online",
    "illegal antiquities trafficking",
    "stolen archaeological artifact",
    "majapahit artifact for sale",
    "khmer statue ancient for sale",
    "roman artifact authentic sale",
    "egyptian antiquities original",
    "ancient bronze statue authentic",
    "ancient artifact site:ebay.com",
    "ancient relic site:etsy.com",
    "antiquities sale site:facebook.com",
    "illegal antiquities trafficking news",
    "artifact smuggling investigation",

    # ── Indonesian Keywords (Lokal) ──
    "jual arca kuno asli",
    "benda purbakala asli dijual",
    "temuan arkeologi dijual",
    "artefak candi dijual",
    "keris kuno asli dijual",
    "jual artefak kuno majapahit"

        # ── Direct Artifact Sale ─────────────────────────────
    "ancient artifact for sale",
    "authentic antiquities for sale",
    "buy ancient artifact online",
    "antique archaeological artifact sale",
    "genuine ancient relic for collectors",
    "museum quality artifact for sale",
    "rare antiquities private collection sale",
    "ancient relic dealer listing",

    # ── Looted / Suspicious Signals ──────────────────────
    "looted artifact for sale",
    "illegal antiquities trafficking",
    "stolen archaeological artifact",
    "ancient relic no provenance",
    "artifact found metal detector sale",
    "burial artifact excavation find",
    "ancient relic found in field",
    "artifact discovered during excavation",

    # ── Civilization Specific ────────────────────────────
    "majapahit artifact for sale",
    "khmer statue ancient for sale",
    "angkor artifact dealer",
    "roman artifact authentic sale",
    "greek antiquities dealer",
    "egyptian antiquities original",
    "mesopotamian cuneiform tablet sale",
    "persian ancient artifact dealer",
    "han dynasty artifact for sale",
    "ming dynasty porcelain antique sale",
    "song dynasty celadon bowl sale",
    "jomon pottery artifact",
    "kofun haniwa figure sale",
    "mongol empire artifact",
    "scythian gold artifact",
    "steppe nomad bronze artifact",

    # ── Object Type Signals ──────────────────────────────
    "ancient bronze statue authentic",
    "ancient jade artifact for sale",
    "ritual bronze vessel ancient",
    "ancient burial figurine",
    "temple stone fragment ancient",
    "ancient coin hoard sale",
    "ancient pottery shard archaeological",
    "ancient ritual object antique",
    "ancient religious statue original",

    # ── Marketplace Discovery ────────────────────────────
    "ancient artifact site:ebay.com",
    "ancient relic site:etsy.com",
    "antiquities sale site:facebook.com",
    "ancient artifact site:auction house",
    "ancient artifact collector forum",

    # ── News & Monitoring ─────────────────────────────────
    "illegal antiquities trafficking news",
    "artifact smuggling investigation",
    "museum artifact repatriation case",
    "looted antiquities returned to museum",
    "archaeological theft investigation",

    # ── Indonesian / Local Search Terms ──────────────────
    "jual arca kuno asli",
    "benda purbakala asli dijual",
    "temuan arkeologi dijual",
    "artefak candi dijual",
    "keris kuno asli dijual",

]

# ======================================================================
# DATA PERSISTENCE
# ======================================================================

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            log.warning(f"Old database corrupted, starting fresh: {e}")
            return []
    return []

def get_hash(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f: h.update(f.read())
        return h.hexdigest()
    except: return "none"

def check_schedule():
    # SELALU JALAN: Diaktifkan sementara agar Anda tidak perlu menunggu jadwal
    return True 

# ======================================================================
# CORE: AI ANALYZER WITH FALLBACK
# ======================================================================

def run_ai_search(model, existing_links, target):
    log.info(f"Targeting: {target}")
    
    prompt = f"""
    Use Google Search to find real information and listings regarding: "{target}".
    Identify marketplace listings (FB, Tokopedia, eBay, etc.), theft news, or discussion forums.
    
    Output the result ONLY in a JSON Array format.
    JSON Output Structure:
    [
      {{
        "item_name": "Item/News Title",
        "source_name": "Website (e.g., eBay, Tokopedia, BBC)",
        "source_type": "Marketplace | News | Forum",
        "status": "Suspected Illicit | News | Discussion",
        "risk_score": 1-10,
        "reason": "Brief reason",
        "source_link": "Full URL",
        "price_info": "Price or N/A"
      }}
    ]
    """
    
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        text = response.text
        
        # LOG RAW TEXT: Menampilkan jawaban mentah AI di GitHub Actions Log
        log.info(f"--- RAW AI RESPONSE ---\n{text[:500]}\n-----------------------")
        
        # BULLETPROOF JSON EXTRACTOR
        # 1. Bersihkan format markdown (```json dan ```)
        clean_text = text.replace('```json', '').replace('```', '')
        # 2. Bersihkan sitasi angka dari Google Search seperti [1], [2]
        clean_text = re.sub(r'\[\d+\]', '', clean_text)
        
        # 3. Ambil teks hanya dari kurung siku pembuka pertama hingga penutup terakhir
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
            log.warning("AI did not provide a valid JSON Array structure.")
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
        genai.configure(api_key=api_key)
        
        # Menggunakan google_search tool untuk live web grounding
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{'google_search': {}}]
        )

        db = load_db()
        links = {i.get('source_link') for i in db if i.get('source_link')}

        # Memilih 1 keyword lokal dan 2 keyword internasional secara paksa
        local_kws = [k for k in KEYWORDS if "jual" in k or "dijual" in k]
        intl_kws = [k for k in KEYWORDS if k not in local_kws]
        
        targets = random.sample(intl_kws, 2) + random.sample(local_kws, 1)
        
        count = 0
        for target in targets:
            new_items = run_ai_search(model, links, target)
            
            if isinstance(new_items, list):
                for item in new_items:
                    link = item.get('source_link')
                    # Hanya tambahkan jika link belum ada di database
                    if link and link not in links:
                        item['timestamp'] = datetime.now().isoformat()
                        item['keyword_matched'] = target
                        db.append(item)
                        links.add(link)
                        count += 1

        # Simpan database & history
        if count > 0:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)

        # Selalu update history agar kita tahu script berjalan lancar
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "last_crawl_date": datetime.now().isoformat(),
                "script_hash": get_hash(SCRIPT_FILE)
            }, f, indent=2)
            
        log.info(f"✅ Done. Added {count} new items. Total: {len(db)} items.")

    except Exception as e:
        log.error(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
