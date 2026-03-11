"""
=======================================================================
  ARTIFACT RADAR v5.0 — Global Intelligence Engine
  AI Engine : Google Gemini 2.5 Flash (Google Search Grounding)
  Mode      : Full English, Global Scope, 8-Day Interval
=======================================================================
"""

import os
import json
import hashlib
import logging
import random
import re
from datetime import datetime, timedelta
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

# ======================================================================
# GLOBAL KEYWORD DATABASE (Full English)
# ======================================================================
KEYWORDS = [
    # ── Southeast Asia ──
    "majapahit artifact for sale", "khmer ancient statue sale", "srivijaya gold artifact",
    "angkor wat style antiquity", "ayutthaya bronze buddha sale", "champa stone carving authentic",
    "dong son bronze drum auction", "ban chiang pottery for sale", "prehistoric indonesian artifact",
    "borobudur temple stone fragment", "prambanan relief fragment sale", "khmer temple sculpture fragment",

    # ── East Asia ──
    "han dynasty artifact sale", "tang dynasty ceramic authentic", "song dynasty porcelain auction",
    "ming dynasty porcelain antique", "qing dynasty jade carving", "ancient chinese bronze vessel",
    "jomon pottery authentic", "yayoi bronze bell dotaku", "kofun haniwa figure",
    "ancient chinese burial figurine", "tang sancai pottery authentic", "song celadon bowl sale",

    # ── Middle East & Egypt ──
    "ancient egyptian ushabti for sale", "pharaonic sarcophagus fragment", "egyptian faience amulet authentic",
    "sumerian cuneiform tablet private sale", "babylonian cylinder seal authentic",
    "akkadian bronze artifact", "luristan bronze antiquity", "ancient persian rhyton",
    "mesopotamian clay tablet cuneiform", "palmyra relief fragment sale",

    # ── Mediterranean (Greco-Roman) ──
    "ancient greek amphora sale", "roman marble bust fragment authentic", "etruscan bronze antiquity",
    "attic red figure pottery", "roman legionary gladius authentic", "byzantine icon antique",
    "mycenaean artifact for sale", "minoan pottery fragment",
    "roman bronze figurine authentic", "ancient greek kylix pottery",

    # ── The Americas (Pre-Columbian) ──
    "mayan jade artifact sale", "aztec stone sculpture authentic", "inca gold antiquity",
    "moche ceramic vessel", "nazca textile fragment", "pre-columbian pottery authentic",
    "chavin stone carving", "tairona gold ornament sale",
    "olmec jade mask authentic", "pre columbian artifact auction",

    # ── South Asia & Silk Road ──
    "indus valley seal authentic", "gandhara buddha sculpture sale", "chola bronze statue",
    "pala empire sculpture", "scythian gold ornament", "bactrian camel artifact authentic",
    "sogdian silver vessel sale", "kushan coin hoard",
    "ancient silk road artifact", "central asian burial artifact",

    # ── Looting & Trafficking Intelligence ──
    "illegal antiquities trafficking news", "artifact smuggling investigation report",
    "stolen archaeological artifact alert", "looted antiquity returned to museum",
    "artifact found metal detector sale", "ancient relic no provenance sale",
    "repatriation of stolen cultural heritage", "black market antiquities discussion",

    # ── Seller Camouflage Terms ──
    "ancient object found in field", "metal detector ancient find sale",
    "old stone statue unknown origin", "burial artifact excavation find",
    "ancient relic estate sale", "unknown ancient artifact identification"
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
                    log.info("Migrating old list format to structured JSON...")
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
    """Run automatically every 8 days, or immediately if FORCE_CRAWL is true."""
    if os.environ.get("FORCE_CRAWL") == "true": 
        log.info("FORCE_CRAWL is active. Bypassing schedule.")
        return True
        
    if not os.path.exists(HISTORY_FILE): return True
    try:
        with open(HISTORY_FILE) as f:
            h = json.load(f)
        last = datetime.fromisoformat(h.get("last_crawl_date"))
        
        # 8-DAY INTERVAL CHECK
        days_passed = (datetime.now() - last).days
        if days_passed >= 8:
            log.info(f"{days_passed} days have passed. Executing scheduled crawl.")
            return True
        else:
            log.info(f"Only {days_passed} days passed since last crawl. Waiting for 8-day mark.")
            return False
    except: return True

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
    log.info(f"Targeting keyword: {target}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Use Google Search to find real marketplace listings, auctions, or news regarding: "{target}".
    Identify marketplace listings (eBay, Facebook, auction houses), theft news, or collector forums.
    
    Output the result STRICTLY as a JSON Array of objects.
    Ignore these already captured URLs: {list(existing_urls)[:5]}
    
    Mandatory JSON Structure:
    [
      {{
        "original_title": "Original title of the item or news article",
        "platform": "Website Name (e.g., eBay, BBC, Facebook, Sotheby's)",
        "url": "Full URL",
        "price_usd": 0,
        "status": "HIGH RISK | MEDIUM RISK | INFO ONLY", 
        "risk_score": 9,
        "origin_region": "Origin of the artifact (e.g., Southeast Asia, Middle East, Unknown)",
        "provenance_flag": false,
        "keyword_trigger": "{target}",
        "reason": "Detailed reasoning regarding its provenance, risk, or price",
        "scraped_at": "{datetime.now().isoformat()}Z"
      }}
    ]
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code != 200:
            log.error(f"Google API Error ({response.status_code}): {response.text}")
            return []

        data = response.json()
        
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            log.error("Empty or rejected API response.")
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
            log.warning("AI did not provide a valid JSON Array.")
            return []
            
    except Exception as e:
        log.error(f"AI Search Failed for '{target}': {e}")
        return []

def main():
    if not check_schedule():
        return
    
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        log.error("GEMINI_API_KEY not found or empty!")
        return 

    try:
        db = load_db()
        listings = db.get("listings", [])
        
        existing_urls = {i.get('url') for i in listings if i.get('url')}
        
        # Pick 3 random global keywords per run
        targets = random.sample(KEYWORDS, min(len(KEYWORDS), 3))
        
        count = 0
        for target in targets:
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
            
        log.info(f"✅ Run Complete. Added {count} new items. Total Database: {len(listings)} items.")

    except Exception as e:
        log.error(f"Fatal Error during main execution: {e}")

if __name__ == "__main__":
    main()
