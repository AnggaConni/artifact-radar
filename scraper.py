"""
=======================================================================
  ARTIFACT RADAR v6.0 — Multi-agent intelligence pipeline
  Collect → Classify → Reason (Gemini 2.5 Flash + Google Search)
  Legacy schedule, data.json format, and screenshot backfill preserved.
=======================================================================
"""

import os
import json
import hashlib
import logging
import random
import time
from datetime import datetime

import requests

from artifact_radar.orchestrator import run_multi_agent_crawl
from artifact_radar.step_log import StepLogger
from artifact_radar.url_utils import normalize_url

# ── Logging Configuration ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("ArtifactRadar")

# ── File Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE = os.path.abspath(__file__)
DEFAULT_PIPELINE_LOG = os.path.join(BASE_DIR, "pipeline.jsonl")

# ======================================================================
# GLOBAL KEYWORD DATABASE (Full English)
# ======================================================================
KEYWORDS = [
    # ══════════════════════════════════════════════════════
    # SOUTHEAST ASIA
    # ══════════════════════════════════════════════════════
    "majapahit artifact for sale",
    "khmer ancient statue sale",
    "srivijaya gold artifact",
    "angkor wat style antiquity",
    "ayutthaya bronze buddha sale",
    "champa stone carving authentic",
    "dong son bronze drum auction",
    "ban chiang pottery for sale",
    "prehistoric indonesian artifact",
    "borobudur temple stone fragment",
    "prambanan relief fragment sale",
    "khmer temple sculpture fragment",
    # — new —
    "khmer sandstone deity sale",
    "thai bronze deity authentic",
    "lao buddha image antique",
    "burmese lacquerware antique auction",
    "vietnamese cham artifact sale",
    "ancient cambodia sculpture buy",
    "java hindu statue authentic",
    "bali ceremonial artifact sale",
    "philippine gold artifact precolonial",
    "brunei sultanate artifact",
    "sulawesi ancient artifact",
    "borneo tribal artifact auction",
    "pyu kingdom artifact myanmar",
    "dvaravati buddha sale",
    "funan period artifact",
    "sukhothai buddha image sale",
    "lopburi artifact auction",
    "mon kingdom bronze sale",
    # ══════════════════════════════════════════════════════
    # EAST ASIA
    # ══════════════════════════════════════════════════════
    "han dynasty artifact sale",
    "tang dynasty ceramic authentic",
    "song dynasty porcelain auction",
    "ming dynasty porcelain antique",
    "qing dynasty jade carving",
    "ancient chinese bronze vessel",
    "jomon pottery authentic",
    "yayoi bronze bell dotaku",
    "kofun haniwa figure",
    "ancient chinese burial figurine",
    "tang sancai pottery authentic",
    "song celadon bowl sale",
    # — new —
    "shang dynasty oracle bone sale",
    "zhou dynasty bronze ritual vessel",
    "warring states jade belt hook",
    "han jade burial suit fragment",
    "tang dynasty horse ceramic",
    "yuan dynasty blue white porcelain",
    "ancient chinese silk fragment",
    "chinese neolithic pottery sale",
    "liangzhu jade cong authentic",
    "sanxingdui bronze mask sale",
    "goryeo celadon korea auction",
    "silla gold crown artifact",
    "baekje bronze mirror sale",
    "joseon dynasty artifact",
    "goguryeo tomb artifact",
    "ancient korean bronze dagger",
    "ryukyu kingdom artifact sale",
    "ainu artifact authentic japan",
    "nanban lacquerware antique",
    "edo period sword tsuba auction",
    # ══════════════════════════════════════════════════════
    # MIDDLE EAST & EGYPT
    # ══════════════════════════════════════════════════════
    "ancient egyptian ushabti for sale",
    "pharaonic sarcophagus fragment",
    "egyptian faience amulet authentic",
    "sumerian cuneiform tablet private sale",
    "babylonian cylinder seal authentic",
    "akkadian bronze artifact",
    "luristan bronze antiquity",
    "ancient persian rhyton",
    "mesopotamian clay tablet cuneiform",
    "palmyra relief fragment sale",
    # — new —
    "ancient egyptian canopic jar sale",
    "egyptian shabtis collection auction",
    "cartouche stele fragment",
    "ptolemaic egyptian artifact",
    "coptic textile fragment sale",
    "meroitic nubian artifact",
    "ancient nubian gold jewelry",
    "phoenician glass vessel sale",
    "canaanite bronze figurine",
    "ugarit ivory carving sale",
    "assyrian lamassu fragment",
    "neo-babylonian amulet sale",
    "achaemenid persian seal authentic",
    "sassanid silver plate sale",
    "parthian coin hoard",
    "nabataean artifact sale",
    "south arabian bronze artifact",
    "yemeni pre-islamic artifact",
    "minean sabaean inscription fragment",
    "syrian mosaic fragment sale",
    "levantine bronze age artifact",
    "dead sea scroll fragment private",
    "ancient hebrew inscription stone",
    # ══════════════════════════════════════════════════════
    # MEDITERRANEAN (GRECO-ROMAN)
    # ══════════════════════════════════════════════════════
    "ancient greek amphora sale",
    "roman marble bust fragment authentic",
    "etruscan bronze antiquity",
    "attic red figure pottery",
    "roman legionary gladius authentic",
    "byzantine icon antique",
    "mycenaean artifact for sale",
    "minoan pottery fragment",
    "roman bronze figurine authentic",
    "ancient greek kylix pottery",
    # — new —
    "greek geometric period pottery sale",
    "corinthian helmet authentic",
    "spartan bronze artifact",
    "hellenistic gold jewelry sale",
    "roman gold aureus coin",
    "roman mosaic tesserae fragment",
    "pompeii artifact for sale",
    "roman glass unguentarium sale",
    "etruscan bucchero pottery",
    "villanovan bronze artifact",
    "magna graecia pottery authentic",
    "sicilian greek coin auction",
    "roman oil lamp collection sale",
    "ancient greek terracotta figurine",
    "cycladic idol authentic",
    "thracian gold treasure sale",
    "illyrian helmet authentic",
    "celtic torque authentic auction",
    "dacian gold bracelet sale",
    "scythian gold pectoral fragment",
    # ══════════════════════════════════════════════════════
    # THE AMERICAS (PRE-COLUMBIAN)
    # ══════════════════════════════════════════════════════
    "mayan jade artifact sale",
    "aztec stone sculpture authentic",
    "inca gold antiquity",
    "moche ceramic vessel",
    "nazca textile fragment",
    "pre-columbian pottery authentic",
    "chavin stone carving",
    "tairona gold ornament sale",
    "olmec jade mask authentic",
    "pre columbian artifact auction",
    # — new —
    "mayan stela fragment sale",
    "mayan codex page authentic",
    "zapotec funerary urn sale",
    "mixtec gold pendant auction",
    "teotihuacan mask sale",
    "veracruz hacha artifact",
    "totonac smiling figurine sale",
    "huastec stone sculpture",
    "west mexico shaft tomb figure",
    "colima dog figurine authentic",
    "chimu silver vessel sale",
    "wari textile fragment",
    "tiwanaku puma figure sale",
    "paracas embroidered textile",
    "sipan gold artifact lord",
    "mississippian gorget artifact sale",
    "hopewell burial artifact",
    "anasazi pottery authentic",
    "cahokia copper artifact sale",
    "pueblo pottery ancient authentic",
    "northwest coast totem fragment",
    "caribbean taino artifact sale",
    "florida archaic artifact",
    "amazonian burial urn ancient",
    # ══════════════════════════════════════════════════════
    # SOUTH ASIA & SILK ROAD
    # ══════════════════════════════════════════════════════
    "indus valley seal authentic",
    "gandhara buddha sculpture sale",
    "chola bronze statue",
    "pala empire sculpture",
    "scythian gold ornament",
    "bactrian camel artifact authentic",
    "sogdian silver vessel sale",
    "kushan coin hoard",
    "ancient silk road artifact",
    "central asian burial artifact",
    # — new —
    "mathura red sandstone sculpture sale",
    "amaravati relief fragment",
    "hoysala temple sculpture sale",
    "vijayanagara bronze artifact",
    "kerala temple bronze antique",
    "odisha temple sculpture fragment",
    "mughal jade artifact sale",
    "rajput artifact authentic",
    "ancient indian coin hoard sale",
    "harappan terracotta figurine",
    "mauryan artifact authentic",
    "gupta period gold coin",
    "nepali gilt bronze buddha",
    "tibetan thangka antique authentic",
    "tibetan ritual object sale",
    "himalayan bronze artifact",
    "bactrian gold hoard private",
    "parthian artifact sale",
    "oxus treasure type artifact",
    "kushan buddha fragment sale",
    "bukhara artifact authentic",
    "samarkand artifact antique",
    "khwarezm artifact sale",
    "ancient afghanistan artifact",
    # ══════════════════════════════════════════════════════
    # AFRICA (SUB-SAHARAN)
    # ══════════════════════════════════════════════════════
    "benin bronze head sale",
    "ife bronze figure authentic",
    "nok terracotta figure sale",
    "yoruba artifact auction",
    "akan goldweight collection",
    "ashanti gold artifact sale",
    "dogon mask artifact authentic",
    "mali empire artifact sale",
    "african tribal artifact auction",
    "kongo kingdom artifact",
    "zulu ceremonial artifact sale",
    "ethiopian artifact antique",
    "aksumite coin hoard",
    "great zimbabwe artifact",
    "ancient mali gold artifact",
    "sao civilization terracotta",
    "west african brass casting sale",
    "igbo ukwu bronze authentic",
    # ══════════════════════════════════════════════════════
    # EUROPE (PREHISTORIC & EARLY MEDIEVAL)
    # ══════════════════════════════════════════════════════
    "viking artifact sale authentic",
    "anglo-saxon brooch auction",
    "roman britain artifact sale",
    "iron age celtic artifact",
    "bronze age hoard fragment sale",
    "neolithic stone tool authentic",
    "merovingian gold fibula sale",
    "visigoth artifact auction",
    "carolingian artifact sale",
    "medieval pilgrim badge authentic",
    "illuminated manuscript page sale",
    "viking sword authentic",
    "migration period artifact sale",
    "hunnic artifact authentic",
    "avar gold artifact sale",
    "slavic ancient artifact",
    "prehistoric cave bear tooth sale",
    "mesolithic flint tool",
    # ══════════════════════════════════════════════════════
    # OCEANIA & PACIFIC
    # ══════════════════════════════════════════════════════
    "aboriginal artifact for sale",
    "maori taonga artifact",
    "papua new guinea tribal artifact",
    "polynesian artifact authentic auction",
    "melanesian artifact sale",
    "easter island artifact",
    "hawaiian feather artifact",
    "fijian artifact authentic",
    "micronesian artifact sale",
    "torres strait islander artifact",
    # ══════════════════════════════════════════════════════
    # PLATFORM-SPECIFIC SEARCH PATTERNS
    # ══════════════════════════════════════════════════════
    "ancient artifact ebay listing",
    "etsy ancient artifact seller",
    "craigslist ancient relic sale",
    "facebook marketplace antiquity",
    "catawiki antiquity lot auction",
    "liveauctioneers antiquity no provenance",
    "invaluable ancient artifact listing",
    "bonhams ancient art sale",
    "christies antiquities private sale",
    "sothebys antiquity auction lot",
    "worthpoint ancient artifact value",
    "ruby lane ancient artifact",
    "1stdibs antiquity listing",
    "chairish ancient artifact",
    "ancient artifact alibaba seller",
    "taobao antique artifact sale",
    "mercari ancient artifact sale",
    "vinted antique artifact listing",
    # Forums / communities
    "ancient artifact reddit found",
    "treasure net forum ancient find sale",
    "metal detecting forum ancient find",
    "artifact hunters forum sale",
    "antiquities collectors forum",
    "ancient coins forum sale",
    "numismatic ancient coin forum",
    "artifact identification forum sell",
    "history forum artifact found sale",
    "collectors weekly ancient artifact",
    # Social media patterns
    "ancient artifact instagram sale",
    "telegram antiquities channel",
    "whatsapp artifact dealer group",
    "tiktok ancient artifact found",
    "youtube artifact found unearthed",
    "pinterest ancient artifact collection",
    "discord antiquity server",
    "artifact dealer facebook group",
    # Dark/encrypted market signals
    "antiquity tor market sale",
    "artifact escrow payment anonymous",
    "antiquity bitcoin payment accepted",
    "crypto payment ancient artifact",
    "artifact shipped discreetly",
    "no questions asked ancient object",
    # ══════════════════════════════════════════════════════
    # LOOTING & TRAFFICKING INTELLIGENCE
    # ══════════════════════════════════════════════════════
    "illegal antiquities trafficking news",
    "artifact smuggling investigation report",
    "stolen archaeological artifact alert",
    "looted antiquity returned to museum",
    "artifact found metal detector sale",
    "ancient relic no provenance sale",
    "repatriation of stolen cultural heritage",
    "black market antiquities discussion",
    # — new —
    "INTERPOL stolen artifact database",
    "UNESCO cultural property theft",
    "art loss register antiquity match",
    "carabinieri TPC artifact seizure",
    "homeland security artifact trafficking",
    "ICE HSI cultural property seizure",
    "FBI art crime team artifact",
    "customs seized antiquity auction",
    "looted artifact repatriated news",
    "archaeological site looted report",
    "conflict antiquity ISIS daesh sale",
    "war zone artifact smuggling route",
    "conflict zone cultural heritage looting",
    "mali timbuktu manuscript theft",
    "afghan artifact looted kabul",
    "iraq museum stolen artifact",
    "libyan artifact smuggling route",
    "syrian artifact trafficking network",
    "yemen artifact stolen sale",
    "haiti artifact looted earthquake",
    "ukraine cultural property looted",
    "occupied territory artifact removal",
    # ══════════════════════════════════════════════════════
    # SELLER CAMOUFLAGE & OBFUSCATION TERMS
    # ══════════════════════════════════════════════════════
    "ancient object found in field",
    "metal detector ancient find sale",
    "old stone statue unknown origin",
    "burial artifact excavation find",
    "ancient relic estate sale",
    "unknown ancient artifact identification",
    # — new —
    "inherited ancient artifact sell",
    "grandmother collection ancient object",
    "estate lot ancient artifacts",
    "antique curiosity cabinet contents",
    "old object attic find identification",
    "flea market ancient find",
    "barn find ancient artifact",
    "car boot ancient object sale",
    "garage sale ancient object",
    "auction house unknown ancient object",
    "no papers ancient artifact",
    "document missing provenance artifact",
    "export certificate needed artifact",
    "old find possibly ancient",
    "pre-1970 artifact collection sale",
    "pre-1973 UNESCO cutoff artifact",
    "family heirloom ancient relic sell",
    "deaccessioned museum artifact sale",
    "legitimate provenance ancient object buy",
    "old collection cleanup sale",
    "private collector downsizing antiquity",
    "bulk lot ancient artifacts",
    "mixed ancient artifact lot auction",
    "ancient object fragment sale cheap",
    "genuine ancient artifact no reserve",
    # ══════════════════════════════════════════════════════
    # PROVENANCE-EVASION & LEGAL GREY-ZONE LANGUAGE
    # ══════════════════════════════════════════════════════
    "pre-ban ivory artifact sale",
    "antique ivory carving authentic",
    "ancient artifact export permit included",
    "artifact COA certificate authenticity",
    "thermoluminescence tested artifact sale",
    "TL test certificate ancient pottery",
    "Oxford authentication artifact sale",
    "ancient artifact customs cleared",
    "art loss register checked artifact",
    "no stolen property artifact guarantee",
    "artifact legally imported collection",
    "swiss collection artifact provenance",
    "london trade artifact authentic",
    "old european collection antiquity",
    "japanese private collection artifact",
    "belgium collection ancient artifact",
    "ancient artifact sold as is",
    "mineral specimen artifact disguised",
    "ethnographic object not antiquity listed",
]

# ======================================================================
# DATA PERSISTENCE & MIGRATION
# ======================================================================


def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
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
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    except OSError:
        return "none"


def check_schedule():
    """Run automatically every 8 days, or immediately if FORCE_CRAWL is true."""
    if os.environ.get("FORCE_CRAWL") == "true":
        log.info("FORCE_CRAWL is active. Bypassing schedule.")
        return True

    if not os.path.exists(HISTORY_FILE):
        return True
    try:
        with open(HISTORY_FILE) as f:
            h = json.load(f)
        last = datetime.fromisoformat(h.get("last_crawl_date"))

        days_passed = (datetime.now() - last).days
        if days_passed >= 8:
            log.info(f"{days_passed} days have passed. Executing scheduled crawl.")
            return True
        log.info(
            f"Only {days_passed} days passed since last crawl. Waiting for 8-day mark."
        )
        return False
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return True


def calculate_summary(listings):
    high_risk = [x for x in listings if x.get("risk_score", 0) >= 8]
    medium_risk = [x for x in listings if 4 <= x.get("risk_score", 0) <= 7]

    platforms = {}
    for item in listings:
        plat = item.get("platform", "Unknown")
        platforms[plat] = platforms.get(plat, 0) + 1

    top_high_risk = sorted(
        high_risk, key=lambda x: x.get("risk_score", 0), reverse=True
    )[:5]

    return {
        "generated_at": datetime.now().isoformat() + "Z",
        "total_listings": len(listings),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "alerts_by_platform": platforms,
        "top_high_risk": top_high_risk,
        "pipeline_version": "6.0",
    }


def get_screenshot_url(url):
    """Generates a dynamic screenshot URL using a free API service."""
    if not url or url.lower() == "n/a":
        return "N/A"
    encoded_url = requests.utils.quote(url)
    return f"https://api.microlink.io/?url={encoded_url}&screenshot=true&meta=false&embed=screenshot.url"


def main():
    if not check_schedule():
        return

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        log.error("GEMINI_API_KEY not found or empty!")
        return

    if "ARTIFACT_PIPELINE_LOG" in os.environ and os.environ["ARTIFACT_PIPELINE_LOG"].strip() == "":
        step_logger = StepLogger(None)
    else:
        log_path = os.environ.get("ARTIFACT_PIPELINE_LOG", DEFAULT_PIPELINE_LOG)
        step_logger = StepLogger(log_path)

    try:
        db = load_db()
        listings = db.get("listings", [])

        backfill_count = 0
        for item in listings:
            if not item.get("screenshot_url") or item.get("screenshot_url") == "":
                u = item.get("url")
                if u and u.lower() != "n/a":
                    item["screenshot_url"] = get_screenshot_url(u)
                else:
                    item["screenshot_url"] = "N/A"
                backfill_count += 1
        if backfill_count > 0:
            log.info(f"Successfully backfilled screenshots for {backfill_count} old records.")

        existing_urls = {i.get("url") for i in listings if i.get("url")}
        existing_norm_urls = set()
        for u in existing_urls:
            nu = normalize_url(u)
            if nu:
                existing_norm_urls.add(nu)

        targets = random.sample(KEYWORDS, min(len(KEYWORDS), 3))
        log.info("Multi-agent pipeline: keywords=%s", targets)

        max_cand = int(os.environ.get("ARTIFACT_MAX_CANDIDATES_PER_KEYWORD", "5"))

        new_items, run_stats = run_multi_agent_crawl(
            api_key,
            targets,
            existing_urls,
            get_screenshot_url=get_screenshot_url,
            step_logger=step_logger,
            max_candidates_per_keyword=max(1, min(max_cand, 15)),
        )
        for st in run_stats:
            log.info(
                "Pipeline stats kw=%r added=%s collector_repair=%s classifier_repairs=%s",
                st.get("keyword"),
                st.get("listings_added"),
                st.get("collector_repair_used"),
                st.get("classifier_repairs"),
            )

        count = 0
        for item in new_items:
            link = item.get("url")
            nu = normalize_url(link)
            if not link or not nu:
                continue
            if nu in existing_norm_urls:
                continue
            listings.append(item)
            existing_urls.add(link)
            existing_norm_urls.add(nu)
            count += 1

        db["listings"] = listings
        db["summary"] = calculate_summary(listings)

        if count > 0 or backfill_count > 0 or not db["summary"].get("generated_at"):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)

        with open(HISTORY_FILE, "w") as f:
            json.dump(
                {
                    "last_crawl_date": datetime.now().isoformat(),
                    "script_hash": get_hash(SCRIPT_FILE),
                    "pipeline_version": "6.0",
                },
                f,
                indent=2,
            )

        log.info(
            f"✅ Run Complete. Added {count} new items. Total Database: {len(listings)} items."
        )

    except Exception as e:
        log.error(f"Fatal Error during main execution: {e}")


if __name__ == "__main__":
    main()
