"""
=======================================================================
  ARTIFACT RADAR v6.0 — Medsos Hunter (Responses API)
  AI Engine : Grok 4.20 Reasoning + web_search (Official Recommended)
  Status    : Fixed - Using new xAI Responses API
  Date      : 26 April 2026
=======================================================================
"""
import os
import json
import hashlib
import logging
import random
import re
import time
from datetime import datetime
import requests
from openai import OpenAI
# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("ArtifactRadar")
# ── Configuration ──
MODEL_NAME = "grok-4.20-reasoning"
XAI_API_KEY = None
client = None
# ── File Paths ──
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE    = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE  = os.path.abspath(__file__)

# ======================================================================
# GLOBAL KEYWORD DATABASE (Full English)
# ======================================================================
KEYWORDS = [
# ══════════════════════════════════════════════════════
# SOUTHEAST ASIA
# ══════════════════════════════════════════════════════
"majapahit artifact for sale", "khmer ancient statue sale", "srivijaya gold artifact",
"angkor wat style antiquity", "ayutthaya bronze buddha sale", "champa stone carving authentic",
"dong son bronze drum auction", "ban chiang pottery for sale", "prehistoric indonesian artifact",
"borobudur temple stone fragment", "prambanan relief fragment sale", "khmer temple sculpture fragment",
# — new —
"khmer sandstone deity sale", "thai bronze deity authentic", "lao buddha image antique",
"burmese lacquerware antique auction", "vietnamese cham artifact sale", "ancient cambodia sculpture buy",
"java hindu statue authentic", "bali ceremonial artifact sale", "philippine gold artifact precolonial",
"brunei sultanate artifact", "sulawesi ancient artifact", "borneo tribal artifact auction",
"pyu kingdom artifact myanmar", "dvaravati buddha sale", "funan period artifact",
"sukhothai buddha image sale", "lopburi artifact auction", "mon kingdom bronze sale",

# ══════════════════════════════════════════════════════
# EAST ASIA
# ══════════════════════════════════════════════════════
"han dynasty artifact sale", "tang dynasty ceramic authentic", "song dynasty porcelain auction",
"ming dynasty porcelain antique", "qing dynasty jade carving", "ancient chinese bronze vessel",
"jomon pottery authentic", "yayoi bronze bell dotaku", "kofun haniwa figure",
"ancient chinese burial figurine", "tang sancai pottery authentic", "song celadon bowl sale",
# — new —
"shang dynasty oracle bone sale", "zhou dynasty bronze ritual vessel", "warring states jade belt hook",
"han jade burial suit fragment", "tang dynasty horse ceramic", "yuan dynasty blue white porcelain",
"ancient chinese silk fragment", "chinese neolithic pottery sale", "liangzhu jade cong authentic",
"sanxingdui bronze mask sale", "goryeo celadon korea auction", "silla gold crown artifact",
"baekje bronze mirror sale", "joseon dynasty artifact", "goguryeo tomb artifact",
"ancient korean bronze dagger", "ryukyu kingdom artifact sale", "ainu artifact authentic japan",
"nanban lacquerware antique", "edo period sword tsuba auction",

# ══════════════════════════════════════════════════════
# MIDDLE EAST & EGYPT
# ══════════════════════════════════════════════════════
"ancient egyptian ushabti for sale", "pharaonic sarcophagus fragment", "egyptian faience amulet authentic",
"sumerian cuneiform tablet private sale", "babylonian cylinder seal authentic",
"akkadian bronze artifact", "luristan bronze antiquity", "ancient persian rhyton",
"mesopotamian clay tablet cuneiform", "palmyra relief fragment sale",
# — new —
"ancient egyptian canopic jar sale", "egyptian shabtis collection auction", "cartouche stele fragment",
"ptolemaic egyptian artifact", "coptic textile fragment sale", "meroitic nubian artifact",
"ancient nubian gold jewelry", "phoenician glass vessel sale", "canaanite bronze figurine",
"ugarit ivory carving sale", "assyrian lamassu fragment", "neo-babylonian amulet sale",
"achaemenid persian seal authentic", "sassanid silver plate sale", "parthian coin hoard",
"nabataean artifact sale", "south arabian bronze artifact", "yemeni pre-islamic artifact",
"minean sabaean inscription fragment", "syrian mosaic fragment sale", "levantine bronze age artifact",
"dead sea scroll fragment private", "ancient hebrew inscription stone",

# ══════════════════════════════════════════════════════
# MEDITERRANEAN (GRECO-ROMAN)
# ══════════════════════════════════════════════════════
"ancient greek amphora sale", "roman marble bust fragment authentic", "etruscan bronze antiquity",
"attic red figure pottery", "roman legionary gladius authentic", "byzantine icon antique",
"mycenaean artifact for sale", "minoan pottery fragment",
"roman bronze figurine authentic", "ancient greek kylix pottery",
# — new —
"greek geometric period pottery sale", "corinthian helmet authentic", "spartan bronze artifact",
"hellenistic gold jewelry sale", "roman gold aureus coin", "roman mosaic tesserae fragment",
"pompeii artifact for sale", "roman glass unguentarium sale", "etruscan bucchero pottery",
"villanovan bronze artifact", "magna graecia pottery authentic", "sicilian greek coin auction",
"roman oil lamp collection sale", "ancient greek terracotta figurine", "cycladic idol authentic",
"thracian gold treasure sale", "illyrian helmet authentic", "celtic torque authentic auction",
"dacian gold bracelet sale", "scythian gold pectoral fragment",

# ══════════════════════════════════════════════════════
# THE AMERICAS (PRE-COLUMBIAN)
# ══════════════════════════════════════════════════════
"mayan jade artifact sale", "aztec stone sculpture authentic", "inca gold antiquity",
"moche ceramic vessel", "nazca textile fragment", "pre-columbian pottery authentic",
"chavin stone carving", "tairona gold ornament sale",
"olmec jade mask authentic", "pre columbian artifact auction",
# — new —
"mayan stela fragment sale", "mayan codex page authentic", "zapotec funerary urn sale",
"mixtec gold pendant auction", "teotihuacan mask sale", "veracruz hacha artifact",
"totonac smiling figurine sale", "huastec stone sculpture", "west mexico shaft tomb figure",
"colima dog figurine authentic", "chimu silver vessel sale", "wari textile fragment",
"tiwanaku puma figure sale", "paracas embroidered textile", "sipan gold artifact lord",
"mississippian gorget artifact sale", "hopewell burial artifact", "anasazi pottery authentic",
"cahokia copper artifact sale", "pueblo pottery ancient authentic", "northwest coast totem fragment",
"caribbean taino artifact sale", "florida archaic artifact", "amazonian burial urn ancient",

# ══════════════════════════════════════════════════════
# SOUTH ASIA & SILK ROAD
# ══════════════════════════════════════════════════════
"indus valley seal authentic", "gandhara buddha sculpture sale", "chola bronze statue",
"pala empire sculpture", "scythian gold ornament", "bactrian camel artifact authentic",
"sogdian silver vessel sale", "kushan coin hoard",
"ancient silk road artifact", "central asian burial artifact",
# — new —
"mathura red sandstone sculpture sale", "amaravati relief fragment", "hoysala temple sculpture sale",
"vijayanagara bronze artifact", "kerala temple bronze antique", "odisha temple sculpture fragment",
"mughal jade artifact sale", "rajput artifact authentic", "ancient indian coin hoard sale",
"harappan terracotta figurine", "mauryan artifact authentic", "gupta period gold coin",
"nepali gilt bronze buddha", "tibetan thangka antique authentic", "tibetan ritual object sale",
"himalayan bronze artifact", "bactrian gold hoard private", "parthian artifact sale",
"oxus treasure type artifact", "kushan buddha fragment sale", "bukhara artifact authentic",
"samarkand artifact antique", "khwarezm artifact sale", "ancient afghanistan artifact",

# ══════════════════════════════════════════════════════
# AFRICA (SUB-SAHARAN)
# ══════════════════════════════════════════════════════
"benin bronze head sale", "ife bronze figure authentic", "nok terracotta figure sale",
"yoruba artifact auction", "akan goldweight collection", "ashanti gold artifact sale",
"dogon mask artifact authentic", "mali empire artifact sale", "african tribal artifact auction",
"kongo kingdom artifact", "zulu ceremonial artifact sale", "ethiopian artifact antique",
"aksumite coin hoard", "great zimbabwe artifact", "ancient mali gold artifact",
"sao civilization terracotta", "west african brass casting sale", "igbo ukwu bronze authentic",

# ══════════════════════════════════════════════════════
# EUROPE (PREHISTORIC & EARLY MEDIEVAL)
# ══════════════════════════════════════════════════════
"viking artifact sale authentic", "anglo-saxon brooch auction", "roman britain artifact sale",
"iron age celtic artifact", "bronze age hoard fragment sale", "neolithic stone tool authentic",
"merovingian gold fibula sale", "visigoth artifact auction", "carolingian artifact sale",
"medieval pilgrim badge authentic", "illuminated manuscript page sale", "viking sword authentic",
"migration period artifact sale", "hunnic artifact authentic", "avar gold artifact sale",
"slavic ancient artifact", "prehistoric cave bear tooth sale", "mesolithic flint tool",

# ══════════════════════════════════════════════════════
# OCEANIA & PACIFIC
# ══════════════════════════════════════════════════════
"aboriginal artifact for sale", "maori taonga artifact", "papua new guinea tribal artifact",
"polynesian artifact authentic auction", "melanesian artifact sale", "easter island artifact",
"hawaiian feather artifact", "fijian artifact authentic", "micronesian artifact sale",
"torres strait islander artifact",

# ══════════════════════════════════════════════════════
# PLATFORM-SPECIFIC SEARCH PATTERNS
# ══════════════════════════════════════════════════════
# Marketplace / classifieds
"ancient artifact ebay listing", "etsy ancient artifact seller",
"craigslist ancient relic sale", "facebook marketplace antiquity",
"catawiki antiquity lot auction", "liveauctioneers antiquity no provenance",
"invaluable ancient artifact listing", "bonhams ancient art sale",
"christies antiquities private sale", "sothebys antiquity auction lot",
"worthpoint ancient artifact value", "ruby lane ancient artifact",
"1stdibs antiquity listing", "chairish ancient artifact",
"ancient artifact alibaba seller", "taobao antique artifact sale",
"mercari ancient artifact sale", "vinted antique artifact listing",

# Forums / communities
"ancient artifact reddit found", "treasure net forum ancient find sale",
"metal detecting forum ancient find",  "artifact hunters forum sale",
"antiquities collectors forum", "ancient coins forum sale",
"numismatic ancient coin forum", "artifact identification forum sell",
"history forum artifact found sale", "collectors weekly ancient artifact",

# Social media patterns
"ancient artifact instagram sale", "telegram antiquities channel",
"whatsapp artifact dealer group", "tiktok ancient artifact found",
"youtube artifact found unearthed", "pinterest ancient artifact collection",
"discord antiquity server", "artifact dealer facebook group",

# Dark/encrypted market signals
"antiquity tor market sale", "artifact escrow payment anonymous",
"antiquity bitcoin payment accepted", "crypto payment ancient artifact",
"artifact shipped discreetly", "no questions asked ancient object",

# ══════════════════════════════════════════════════════
# LOOTING & TRAFFICKING INTELLIGENCE
# ══════════════════════════════════════════════════════
"illegal antiquities trafficking news", "artifact smuggling investigation report",
"stolen archaeological artifact alert", "looted antiquity returned to museum",
"artifact found metal detector sale", "ancient relic no provenance sale",
"repatriation of stolen cultural heritage", "black market antiquities discussion",
# — new —
"INTERPOL stolen artifact database", "UNESCO cultural property theft",
"art loss register antiquity match", "carabinieri TPC artifact seizure",
"homeland security artifact trafficking", "ICE HSI cultural property seizure",
"FBI art crime team artifact", "customs seized antiquity auction",
"looted artifact repatriated news", "archaeological site looted report",
"conflict antiquity ISIS daesh sale", "war zone artifact smuggling route",
"conflict zone cultural heritage looting", "mali timbuktu manuscript theft",
"afghan artifact looted kabul", "iraq museum stolen artifact",
"libyan artifact smuggling route", "syrian artifact trafficking network",
"yemen artifact stolen sale", "haiti artifact looted earthquake",
"ukraine cultural property looted", "occupied territory artifact removal",

# ══════════════════════════════════════════════════════
# SELLER CAMOUFLAGE & OBFUSCATION TERMS
# ══════════════════════════════════════════════════════
"ancient object found in field", "metal detector ancient find sale",
"old stone statue unknown origin", "burial artifact excavation find",
"ancient relic estate sale", "unknown ancient artifact identification",
# — new —
"inherited ancient artifact sell", "grandmother collection ancient object",
"estate lot ancient artifacts", "antique curiosity cabinet contents",
"old object attic find identification", "flea market ancient find",
"barn find ancient artifact", "car boot ancient object sale",
"garage sale ancient object", "auction house unknown ancient object",
"no papers ancient artifact", "document missing provenance artifact",
"export certificate needed artifact", "old find possibly ancient",
"pre-1970 artifact collection sale", "pre-1973 UNESCO cutoff artifact",
"family heirloom ancient relic sell", "deaccessioned museum artifact sale",
"legitimate provenance ancient object buy", "old collection cleanup sale",
"private collector downsizing antiquity", "bulk lot ancient artifacts",
"mixed ancient artifact lot auction", "ancient object fragment sale cheap",
"genuine ancient artifact no reserve",

# ══════════════════════════════════════════════════════
# PROVENANCE-EVASION & LEGAL GREY-ZONE LANGUAGE
# ══════════════════════════════════════════════════════
"pre-ban ivory artifact sale", "antique ivory carving authentic",
"ancient artifact export permit included", "artifact COA certificate authenticity",
"thermoluminescence tested artifact sale", "TL test certificate ancient pottery",
"Oxford authentication artifact sale", "ancient artifact customs cleared",
"art loss register checked artifact", "no stolen property artifact guarantee",
"artifact legally imported collection", "swiss collection artifact provenance",
"london trade artifact authentic", "old european collection antiquity",
"japanese private collection artifact", "belgium collection ancient artifact",
"ancient artifact sold as is", "mineral specimen artifact disguised",
"ethnographic object not antiquity listed"
]

# ======================================================================
# DATA PERSISTENCE & MIGRATION
# ======================================================================

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {"summary": {}, "listings": data}
        except Exception as e:
            log.warning(f"Database error: {e}")
    return {"summary": {}, "listings": []}
def get_hash(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f: h.update(f.read())
        return h.hexdigest()
    except: return "none"
def check_schedule():
    if os.environ.get("FORCE_CRAWL") == "true":
        log.info("FORCE_CRAWL is active. Bypassing schedule.")
        return True
    if not os.path.exists(HISTORY_FILE): return True
    try:
        with open(HISTORY_FILE) as f:
            h = json.load(f)
        last = datetime.fromisoformat(h.get("last_crawl_date"))
        return (datetime.now() - last).days >= 8
    except:
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
def get_screenshot_url(url):
    if not url or url.lower() == "n/a": return "N/A"
    encoded = requests.utils.quote(url)
    return f"https://api.microlink.io/?url={encoded}&screenshot=true&meta=false&embed=screenshot.url"
def extract_json_array(text: str):
    if not text or not isinstance(text, str): return []
    clean = text.replace('```json', '').replace('```', '').strip()
    clean = re.sub(r'^.*?\[', '[', clean, flags=re.DOTALL)
    start = clean.find('[')
    end = clean.rfind(']') + 1
    if start == -1 or end <= start: return []
    json_str = clean[start:end]
    try:
        data = json.loads(json_str)
        return data if isinstance(data, list) else []
    except:
        try: return json.loads(json_str + "]")
        except: return []
# ======================================================================
# CORE - Menggunakan Responses API (V6.0)
# ======================================================================
def run_grok_search(existing_urls, target):
    log.info(f"🔎 Hunting keyword: {target} [Grok 4.20 + web_search]")
    system_prompt = """
You are a senior OSINT analyst specializing in illicit antiquities trafficking according to the 1970 UNESCO Convention.
Use the web_search tool to find real, current listings on Facebook Marketplace, Instagram, Telegram, TikTok, auction sites, and forums.
Never hallucinate URLs or listings. Return ONLY a valid JSON array. No explanation outside the JSON.
"""
    user_prompt = f"""
Search for current listings or discussions about: "{target}"
Ignore these already processed URLs: {list(existing_urls)[:25]}
Return ONLY a JSON array in this exact format:
[
  {{
    "original_title": "Exact title or post caption",
    "platform": "Facebook Marketplace | Instagram | Telegram | LiveAuctioneers | Sothebys | etc",
    "url": "full valid URL",
    "price_usd": 0,
    "status": "HIGH RISK | MEDIUM RISK | INFO ONLY",
    "risk_score": 8,
    "origin_region": "Southeast Asia | China | India | Papua New Guinea | Ukraine | etc",
    "provenance_flag": false,
    "keyword_trigger": "{target}",
    "reason": "Specific red flags and connection to 1970 UNESCO Convention",
    "scraped_at": "2026-04-26T18:38:00Z",
    "screenshot_url": ""
  }}
]
"""
    try:
        response = client.responses.create(
            model=MODEL_NAME,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=[{"type": "web_search"}],
            temperature=0.1,
            max_output_tokens=8192,
            response_format={"type": "json_object"}
        )
        # Responses API structure berbeda
        output = response.output_text if hasattr(response, 'output_text') else str(response)
        results = extract_json_array(output)
        
        log.info(f"Found {len(results)} result(s) from Grok for '{target}'")
        return results
    except Exception as e:
        log.error(f"Grok hunting error for '{target}': {e}")
        return []
def main():
    global client, XAI_API_KEY
    
    if not check_schedule():
        return
    XAI_API_KEY = os.environ.get("XAI_API_KEY", "").strip()
    if not XAI_API_KEY:
        log.error("❌ XAI_API_KEY is missing!")
        return
    client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
    try:
        db = load_db()
        listings = db.get("listings", [])
        existing_urls = {i.get('url') for i in listings if i.get('url')}
        targets = random.sample(KEYWORDS, min(len(KEYWORDS), 3))
        
        log.info("🚀 Starting Artifact Radar v6.0 — Medsos Hunter (Responses API)")
        log.info(f"Selected keywords: {targets}")
        
        count = 0
        for target in targets:
            new_items = run_grok_search(existing_urls, target)
            if isinstance(new_items, list) and new_items:
                for item in new_items:
                    url = item.get('url')
                    if url and url.startswith("http") and url not in existing_urls:
                        item.setdefault('scraped_at', datetime.now().isoformat() + "Z")
                        item.setdefault('screenshot_url', get_screenshot_url(url))
                        listings.append(item)
                        existing_urls.add(url)
                        count += 1
                        log.info(f"✅ Added | Risk: {item.get('risk_score', 0)} | {item.get('platform')}")
            else:
                log.info(f"No new valid items from: {target}")
            time.sleep(6)
        db["listings"] = listings
        db["summary"] = calculate_summary(listings)
        if count > 0:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            log.info(f"✅ Database updated. Added {count} new items.")
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "last_crawl_date": datetime.now().isoformat(),
                "script_hash": get_hash(SCRIPT_FILE),
                "ai_engine": MODEL_NAME
            }, f, indent=2)
            
        log.info("✅ Artifact Radar v6.0 run completed successfully.")
    except Exception as e:
        log.error(f"Fatal Error: {e}")
if __name__ == "__main__":
    main()
