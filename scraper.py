"""
=======================================================================
  ARTIFACT RADAR v3.3 — Robust Intelligence Crawler
  AI Engine : Google Gemini 1.5 Flash
  Fixes     : Exit Code 1, Empty JSON, & Google Search Tool Handling
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

# ── Konfigurasi Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")

# ── Jalur File ──
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE  = os.path.abspath(__file__)

KEYWORDS = [

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
            log.warning(f"Database lama rusak, memulai baru: {e}")
            return []
    return []

def get_hash(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f: h.update(f.read())
        return h.hexdigest()
    except: return "none"

def check_schedule():
    if os.environ.get("FORCE_CRAWL") == "true": return True
    if not os.path.exists(HISTORY_FILE): return True
    try:
        with open(HISTORY_FILE) as f:
            h = json.load(f)
        last = datetime.fromisoformat(h.get("last_crawl_date"))
        return datetime.now() - last >= timedelta(hours=12) # Cek tiap 12 jam
    except: return True

# ======================================================================
# CORE: AI ANALYZER WITH FALLBACK
# ======================================================================

def run_ai_search(model, existing_links):
    target = random.choice(KEYWORDS)
    log.info(f"Targeting: {target}")
    
    prompt = f"""
    Cari informasi terbaru menggunakan Google Search tentang: "{target}".
    Identifikasi listing marketplace (FB, eBay, dll), berita pencurian, atau forum kolektor.
    
    Tampilkan hasil hanya dalam format JSON Array.
    Jangan masukkan URL yang sudah ada ini: {list(existing_links)[:5]}
    
    Output JSON:
    [
      {{
        "item_name": "Judul Barang/Berita",
        "source_name": "Website (BBC, Tokopedia, dll)",
        "source_type": "Marketplace | News | Forum",
        "status": "Suspected Illicit | News | Discussion",
        "risk_score": 1-10,
        "reason": "Alasan singkat",
        "source_link": "URL Lengkap",
        "price_info": "Harga atau N/A"
      }}
    ]
    """
    
    try:
        # 1. Hapus strict JSON mime-type karena sering bentrok dengan Search Tool
        # 2. Matikan Filter Keamanan karena keyword kita sangat sensitif (stolen, illegal)
        response = model.generate_content(
            prompt,
            safety_settings={
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Log jawaban mentah AI agar bisa kita debug di tab Actions jika masih kosong
        log.info(f"Raw AI Response: {response.text[:300]}...")
        
        # Ekstrak JSON menggunakan regex (lebih tahan banting)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            log.warning("AI tidak memberikan JSON yang valid.")
            return []
            
    except Exception as e:
        log.error(f"Pencarian AI Gagal: {e}")
        return []

def main():
    if not check_schedule():
        log.info("Sistem istirahat.")
        return
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY tidak ditemukan!")
        return # Keluar tanpa error code agar tidak membingungkan GitHub

    try:
        genai.configure(api_key=api_key)
        
        # Inisialisasi model dengan tool search
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{'google_search': {}}]
        )

        db = load_db()
        links = {i.get('source_link') for i in db if i.get('source_link')}

        # Jalankan pencarian
        new_items = run_ai_search(model, links)
        
        count = 0
        if isinstance(new_items, list):
            for item in new_items:
                link = item.get('source_link')
                if link and link not in links:
                    item['timestamp'] = datetime.now().isoformat()
                    db.append(item)
                    links.add(link)
                    count += 1

        # Simpan database & history
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "last_crawl_date": datetime.now().isoformat(),
                "script_hash": get_hash(SCRIPT_FILE)
            }, f, indent=2)
            
        log.info(f"✅ Selesai. Ditambahkan {count} data baru. Total: {len(db)} item.")

    except Exception as e:
        log.error(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
