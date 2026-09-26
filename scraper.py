"""
=======================================================================
  ARTIFACT RADAR v7.0 — Evidence Snapshot Intelligence Engine
  AI Engine : Google Gemini 2.5 Flash (Google Search Grounding)
  Mode      : Full English, Global Scope, 4-Day Interval
  Feature   : Source Monitoring + Structured Evidence Snapshots
=======================================================================
"""

import os
import json
import hashlib
import logging
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import re
import time
from html import unescape
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

# ── Runtime Controls ──
TARGETS_PER_RUN = max(1, min(int(os.environ.get("TARGETS_PER_RUN", "3")), 6))
QUERY_HISTORY_LIMIT = 12
QUERY_STRIDE = 97
     
SOURCE_CHECK_WORKERS = max(2, min(int(os.environ.get("SOURCE_CHECK_WORKERS", "8")), 12))
SOURCE_CHECK_TIMEOUT = max(5, min(int(os.environ.get("SOURCE_CHECK_TIMEOUT", "12")), 30))
HISTORY_EVENT_LIMIT = 12
SNAPSHOT_LIMIT = 12
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")

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
# SOURCE MONITORING / CHANGE DETECTION
# ======================================================================

def canonical_source_url(item):
    return normalize_url(
        item.get("canonical_source_url") or
        item.get("source_url") or
        item.get("url")
    )


def is_grounding_redirect(url):
    if not url:
        return False
    u = url.lower()
    return "vertexaisearch.cloud.google.com" in u or "grounding-api-redirect" in u


def source_signature(response):
    """Create a conservative content signature for change detection."""
    content_type = (response.headers.get("content-type") or "").lower()
    raw = response.content[:524288]

    if "text/html" in content_type or "application/xhtml" in content_type:
        try:
            text = raw.decode(response.encoding or "utf-8", errors="ignore")
            text = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", text)
            text = re.sub(r"(?s)<!--.*?-->", " ", text)
            text = re.sub(r"\\s+", " ", text).strip().lower()
            raw = text[:200000].encode("utf-8")
        except Exception:
            pass

    return hashlib.sha256(raw).hexdigest()


def _clean_html_text(raw):
    text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", raw or "")
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\\s+", " ", text).strip()


def _first_meta(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text or "", re.I)
        if m:
            value = unescape(m.group(1)).strip()
            if value:
                return value
    return ""


def extract_page_metadata(body, content_type=""):
    """Extract lightweight structured page metadata for change detection."""
    if not body or "html" not in (content_type or "").lower():
        return {}
    try:
        raw = body.decode("utf-8", errors="replace")

        title = _first_meta(raw, [
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r'<title[^>]*>(.*?)</title>'
        ])

        description = _first_meta(raw, [
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)'
        ])

        images = []
        image_patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)'
        ]
        for pattern in image_patterns:
            for match in re.finditer(pattern, raw, re.I):
                value = unescape(match.group(1)).strip()
                if value and value not in images:
                    images.append(value)
                if len(images) >= 8:
                    break
            if len(images) >= 8:
                break

        for match in re.finditer(r'["\']image["\']\s*:\s*["\']([^"\']+)', raw, re.I):
            value = unescape(match.group(1)).strip()
            if value and value not in images:
                images.append(value)
            if len(images) >= 8:
                break

        price_text = _first_meta(raw, [
            r'["\']price["\']\s*:\s*["\']([^"\']+)',
            r'itemprop=["\']price["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+property=["\']product:price:amount["\'][^>]+content=["\']([^"\']+)'
        ])

        currency = _first_meta(raw, [
            r'["\']priceCurrency["\']\s*:\s*["\']([^"\']+)',
            r'itemprop=["\']priceCurrency["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+property=["\']product:price:currency["\'][^>]+content=["\']([^"\']+)'
        ])

        plain = _clean_html_text(raw)
        provenance_excerpt = ""
        lowered = plain.lower()
        for term in ("provenance", "collection", "ownership", "acquired", "provenienza"):
            idx = lowered.find(term)
            if idx >= 0:
                start_idx = max(0, idx - 120)
                provenance_excerpt = plain[start_idx:start_idx + 360]
                break

        return {
            "page_title": title[:500],
            "page_description": description[:1200],
            "image_urls": images[:8],
            "page_price_text": price_text[:120],
            "page_price_currency": currency[:20],
            "provenance_excerpt": provenance_excerpt[:500]
        }
    except Exception:
        return {}


def snapshot_file_path(fingerprint):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    return os.path.join(SNAPSHOT_DIR, f"{fingerprint}.json")


def load_snapshot_history(fingerprint):
    path = snapshot_file_path(fingerprint)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"_meta": {"version": "1.0", "description": "Structured observation snapshots for Artifact Radar. Snapshots record observed page metadata and do not establish intent or wrongdoing."}, "fingerprint": fingerprint, "observations": []}


def snapshot_value_signature(snapshot):
    payload = {
        "page_title": snapshot.get("page_title", ""),
        "page_description": snapshot.get("page_description", ""),
        "image_urls": sorted(snapshot.get("image_urls", [])),
        "page_price_text": snapshot.get("page_price_text", ""),
        "page_price_currency": snapshot.get("page_price_currency", ""),
        "provenance_excerpt": snapshot.get("provenance_excerpt", ""),
        "price_usd": snapshot.get("price_usd"),
        "provenance_flag": snapshot.get("provenance_flag"),
        "risk_score": snapshot.get("risk_score"),
        "ai_risk_score": snapshot.get("ai_risk_score"),
        "final_url": snapshot.get("final_url", ""),
        "source_status": snapshot.get("source_status", "")
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def make_snapshot(item, state):
    page = state.get("page_metadata", {}) or {}
    snapshot = {
        "observed_at": state.get("checked_at") or datetime.now().isoformat() + "Z",
        "title": item.get("original_title", ""),
        "page_title": page.get("page_title", ""),
        "page_description": page.get("page_description", ""),
        "image_urls": page.get("image_urls", []),
        "page_price_text": page.get("page_price_text", ""),
        "page_price_currency": page.get("page_price_currency", ""),
        "provenance_excerpt": page.get("provenance_excerpt", ""),
        "price_usd": item.get("price_usd"),
        "provenance_flag": item.get("provenance_flag"),
        "risk_score": item.get("risk_score"),
        "ai_risk_score": item.get("ai_risk_score"),
        "origin_region": item.get("origin_region", ""),
        "source_url": item.get("canonical_source_url") or canonical_source_url(item),
        "final_url": state.get("final_url", ""),
        "source_status": state.get("status", "UNKNOWN"),
        "http_status": state.get("http_status"),
        "content_hash": state.get("content_hash", ""),
        "etag": state.get("etag", ""),
        "last_modified": state.get("last_modified", "")
    }
    snapshot["snapshot_signature"] = snapshot_value_signature(snapshot)
    return snapshot


def diff_snapshots(previous, current):
    if not previous:
        return [{"field": "snapshot", "change": "INITIAL_SNAPSHOT", "before": None, "after": current.get("observed_at")}]

    diffs = []
    def add(field, change, before, after):
        if before != after:
            diffs.append({
                "field": field,
                "change": change,
                "before": before,
                "after": after
            })

    add("title", "TITLE_CHANGED", previous.get("page_title") or previous.get("title", ""), current.get("page_title") or current.get("title", ""))
    add("description", "DESCRIPTION_CHANGED", previous.get("page_description", ""), current.get("page_description", ""))
    add("price", "PRICE_CHANGED", previous.get("price_usd"), current.get("price_usd"))
    add("page_price", "PAGE_PRICE_CHANGED", previous.get("page_price_text", ""), current.get("page_price_text", ""))
    add("provenance", "PROVENANCE_CHANGED", previous.get("provenance_flag"), current.get("provenance_flag"))
    add("provenance_text", "PROVENANCE_TEXT_CHANGED", previous.get("provenance_excerpt", ""), current.get("provenance_excerpt", ""))
    add("images", "IMAGE_CHANGED", sorted(previous.get("image_urls", [])), sorted(current.get("image_urls", [])))
    add("risk_score", "RISK_SCORE_CHANGED", previous.get("risk_score"), current.get("risk_score"))
    add("ai_risk_score", "AI_RISK_SCORE_CHANGED", previous.get("ai_risk_score"), current.get("ai_risk_score"))
    add("final_url", "FINAL_URL_CHANGED", previous.get("final_url", ""), current.get("final_url", ""))
    return diffs


def persist_snapshot(fingerprint, snapshot):
    store = load_snapshot_history(fingerprint)
    observations = store.get("observations", []) if isinstance(store.get("observations"), list) else []
    previous = observations[-1] if observations else None
    diffs = diff_snapshots(previous, snapshot)

    if previous and previous.get("snapshot_signature") == snapshot.get("snapshot_signature"):
        previous["last_observed_at"] = snapshot.get("observed_at")
        previous["observations_seen"] = int(previous.get("observations_seen", 1) or 1) + 1
        current = previous
    else:
        snapshot["first_observed_at"] = snapshot.get("observed_at")
        snapshot["last_observed_at"] = snapshot.get("observed_at")
        snapshot["observations_seen"] = 1
        observations.append(snapshot)
        observations = observations[-SNAPSHOT_LIMIT:]
        current = snapshot

    store.update({
        "fingerprint": fingerprint,
        "updated_at": snapshot.get("observed_at"),
        "snapshot_count": len(observations),
        "observations": observations
    })
    with open(snapshot_file_path(fingerprint), "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)

    return previous, current, diffs, len(observations)


def fetch_source_state(item):
    """
    Check a source without interpreting intent.
    404/410 = source no longer returned.
    403/429/5xx/timeout = unavailable/blocked, not proof of deletion.
    Content hash changes = technical change signal, not proof of a material edit.
    """
    url = canonical_source_url(item)
    if not url:
        return {
            "status": "UNKNOWN",
            "reason": "No canonical source URL",
            "checked_at": datetime.now().isoformat() + "Z"
        }

    if is_grounding_redirect(url):
        return {
            "status": "UNKNOWN",
            "reason": "Grounding redirect URL; source cannot be reliably monitored",
            "checked_at": datetime.now().isoformat() + "Z",
            "checked_url": url
        }

    checked_at = datetime.now().isoformat() + "Z"
    headers = {
        "User-Agent": "ArtifactRadar/7.0 (+https://github.com/AnggaConni/artifact-radar)"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=SOURCE_CHECK_TIMEOUT,
            allow_redirects=True,
            stream=True
        )

        body = b""
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                body += chunk
                if len(body) >= 524288:
                    break

        # requests.Response.content is not guaranteed after partial streaming,
        # so temporarily replace it for signature generation.
        original_content = response._content
        response._content = body

        content_hash = source_signature(response) if response.status_code == 200 else ""
        content_type = response.headers.get("content-type", "")
        page_metadata = extract_page_metadata(body, content_type) if response.status_code == 200 else {}
        response._content = original_content

        final_url = normalize_url(response.url)

        if response.status_code in (404, 410):
            status = "REMOVED"
        elif 200 <= response.status_code < 300:
            status = "ACTIVE"
        elif response.status_code in (301, 302, 303, 307, 308):
            status = "REDIRECTED"
        elif response.status_code in (401, 403, 405, 406, 429):
            status = "UNAVAILABLE"
        elif 500 <= response.status_code < 600:
            status = "UNAVAILABLE"
        else:
            status = "UNKNOWN"

        return {
            "status": status,
            "http_status": response.status_code,
            "reason": response.reason or "",
            "checked_at": checked_at,
            "checked_url": url,
            "final_url": final_url,
            "content_hash": content_hash,
            "etag": response.headers.get("etag", ""),
            "last_modified": response.headers.get("last-modified", ""),
            "page_metadata": page_metadata
        }

    except requests.exceptions.Timeout:
        return {
            "status": "UNAVAILABLE",
            "reason": "Request timeout",
            "checked_at": checked_at,
            "checked_url": url
        }
    except requests.exceptions.RequestException as exc:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Request error: {type(exc).__name__}",
            "checked_at": checked_at,
            "checked_url": url
        }
    except Exception as exc:
        return {
            "status": "UNKNOWN",
            "reason": f"Monitor error: {type(exc).__name__}",
            "checked_at": checked_at,
            "checked_url": url
        }


def update_source_history(listings, source_history):
    """
    Update current source state and append a compact event history per record.
    Returns summary counters for the current crawl.
    """
    counters = {
        "active": 0,
        "removed": 0,
        "unavailable": 0,
        "changed": 0,
        "recovered": 0,
        "redirected": 0,
        "removed_events": 0,
        "unavailable_events": 0,
        "content_change_events": 0,
        "snapshot_field_change_events": 0,
        "title_change_events": 0,
        "description_change_events": 0,
        "price_change_events": 0,
        "image_change_events": 0,
        "provenance_change_events": 0,
        "risk_change_events": 0
    }

    monitor_targets = []
    for item in listings:
        fp = item.get("record_fingerprint") or record_fingerprint(item)
        url = canonical_source_url(item)
        item["record_fingerprint"] = fp

        if not fp or not url:
            item["source_status"] = "UNKNOWN"
            item["source_status_reason"] = "No monitorable canonical source URL"
            continue

        monitor_targets.append((fp, item))

    def check(pair):
        fp, item = pair
        return fp, fetch_source_state(item)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=SOURCE_CHECK_WORKERS) as executor:
        futures = [executor.submit(check, pair) for pair in monitor_targets]
        results = [future.result() for future in as_completed(futures)]

    for fp, state in results:
        item = next((x for x in listings if x.get("record_fingerprint") == fp), None)
        if item is None:
            continue

        entry = source_history.get(fp, {})
        events = entry.get("events", [])
        previous_status = entry.get("last_status", "")
        previous_hash = entry.get("last_content_hash", "")

        current_status = state.get("status", "UNKNOWN")
        current_hash = state.get("content_hash", "")

        snapshot = make_snapshot(item, state)
        previous_snapshot, current_snapshot, snapshot_diffs, snapshot_count = persist_snapshot(fp, snapshot)
        snapshot_changes = [d.get("change") for d in snapshot_diffs if d.get("change")]
        snapshot_changed = bool(previous_snapshot and snapshot_changes and snapshot_changes != ["INITIAL_SNAPSHOT"])

        if snapshot_changed:
            counters["snapshot_field_change_events"] += 1
            for code in snapshot_changes:
                if code in ("TITLE_CHANGED",): counters["title_change_events"] += 1
                if code in ("DESCRIPTION_CHANGED",): counters["description_change_events"] += 1
                if code in ("PRICE_CHANGED", "PAGE_PRICE_CHANGED"): counters["price_change_events"] += 1
                if code in ("IMAGE_CHANGED",): counters["image_change_events"] += 1
                if code in ("PROVENANCE_CHANGED", "PROVENANCE_TEXT_CHANGED"): counters["provenance_change_events"] += 1
                if code in ("RISK_SCORE_CHANGED", "AI_RISK_SCORE_CHANGED"): counters["risk_change_events"] += 1

        change_type = "UNCHANGED"
        if not events:
            change_type = "INITIAL_CHECK"
        elif current_status == "REMOVED" and previous_status not in ("REMOVED", "UNKNOWN"):
            change_type = "SOURCE_DISAPPEARED"
        elif current_status == "ACTIVE" and previous_status in ("REMOVED", "UNAVAILABLE"):
            change_type = "SOURCE_RECOVERED"
        elif current_status == "ACTIVE" and previous_hash and current_hash and previous_hash != current_hash:
            change_type = "POSSIBLE_CONTENT_CHANGE"
        elif current_status == "REDIRECTED" and previous_status != "REDIRECTED":
            change_type = "SOURCE_REDIRECTED"
        elif current_status == "UNAVAILABLE" and previous_status == "ACTIVE":
            change_type = "SOURCE_UNAVAILABLE"

        if current_status == "ACTIVE":
            counters["active"] += 1
        elif current_status == "REMOVED":
            counters["removed"] += 1
        elif current_status == "UNAVAILABLE":
            counters["unavailable"] += 1
        elif current_status == "REDIRECTED":
            counters["redirected"] += 1

        if change_type == "POSSIBLE_CONTENT_CHANGE":
            counters["changed"] += 1
            counters["content_change_events"] += 1
        elif change_type == "RISK_SCORE_CHANGED":
            counters["changed"] += 1
            counters["content_change_events"] += 1
        elif change_type == "PROVENANCE_STATUS_CHANGED":
            counters["changed"] += 1
            counters["content_change_events"] += 1
        elif change_type == "PRICE_CHANGED":
            counters["changed"] += 1
            counters["content_change_events"] += 1
        elif change_type == "SOURCE_RECOVERED":
            counters["recovered"] += 1
        elif change_type == "SOURCE_DISAPPEARED":
            counters["removed_events"] += 1
        elif change_type == "SOURCE_UNAVAILABLE":
            counters["unavailable_events"] += 1

        event = {
            "checked_at": state.get("checked_at"),
            "status": current_status,
            "change_type": change_type,
            "http_status": state.get("http_status"),
            "final_url": state.get("final_url"),
            "content_hash": current_hash,
            "reason": state.get("reason", ""),
            "etag": state.get("etag", ""),
            "last_modified": state.get("last_modified", ""),
            "title": item.get("original_title", ""),
            "risk_score": item.get("risk_score"),
            "ai_risk_score": item.get("ai_risk_score"),
            "provenance_flag": item.get("provenance_flag"),
            "price_usd": item.get("price_usd"),
            "source_type": item.get("source_type", ""),
            "platform": item.get("platform", ""),
            "snapshot_count": snapshot_count,
            "snapshot_changes": snapshot_changes,
            "snapshot_diffs": snapshot_diffs,
            "snapshot_file": f"snapshots/{fp}.json"
        }

        events.append(event)
        events = events[-HISTORY_EVENT_LIMIT:]

        observations = entry.get("observations", [])
        observations.append({
            "observed_at": state.get("checked_at"),
            "title": item.get("original_title", ""),
            "risk_score": item.get("risk_score"),
            "ai_risk_score": item.get("ai_risk_score"),
            "provenance_flag": item.get("provenance_flag"),
            "price_usd": item.get("price_usd"),
            "source_status": current_status,
            "http_status": state.get("http_status"),
            "change_type": change_type,
            "source_type": item.get("source_type", ""),
            "platform": item.get("platform", ""),
            "snapshot_count": snapshot_count,
            "snapshot_changes": snapshot_changes,
            "snapshot_diffs": snapshot_diffs
        })
        observations = observations[-HISTORY_EVENT_LIMIT:]

        entry.update({
            "first_seen": entry.get("first_seen") or item.get("first_seen") or item.get("scraped_at"),
            "last_checked": state.get("checked_at"),
            "last_status": current_status,
            "last_content_hash": current_hash,
            "last_final_url": state.get("final_url", ""),
            "last_risk_score": item.get("risk_score"),
            "last_ai_risk_score": item.get("ai_risk_score"),
            "last_price_usd": item.get("price_usd"),
            "last_provenance_flag": item.get("provenance_flag"),
            "last_snapshot_signature": current_snapshot.get("snapshot_signature"),
            "last_snapshot_observed_at": current_snapshot.get("observed_at"),
            "snapshot_changed": snapshot_changed,
            "events": events,
            "observations": observations
        })
        source_history[fp] = entry

        item["source_status"] = current_status
        item["source_status_reason"] = state.get("reason", "")
        item["source_http_status"] = state.get("http_status")
        item["source_checked_at"] = state.get("checked_at")
        item["source_final_url"] = state.get("final_url", "")
        item["source_content_hash"] = current_hash
        item["source_change_type"] = change_type
        item["snapshot_changed"] = snapshot_changed
        item["snapshot_changes"] = snapshot_changes
        item["snapshot_last_observed_at"] = current_snapshot.get("observed_at")
        item["snapshot_count"] = snapshot_count
        item["snapshot_file"] = f"snapshots/{fp}.json"
        item["source_change_detected"] = change_type in {
            "SOURCE_DISAPPEARED", "SOURCE_RECOVERED",
            "POSSIBLE_CONTENT_CHANGE", "SOURCE_REDIRECTED"
        } or snapshot_changed
        item["source_history_count"] = len(events)
        if change_type == "POSSIBLE_CONTENT_CHANGE":
            item["last_content_change_at"] = state.get("checked_at")

    return counters


# ======================================================================
# QUERY ROTATION / URL NORMALISATION / EVIDENCE SCORING
# ======================================================================

def normalize_url(raw_url):
    """Return a stable URL representation for duplicate detection and storage."""
    if not raw_url:
        return ""
    raw_url = str(raw_url).strip()
    if not raw_url or raw_url.lower() in {"n/a", "none", "null"}:
        return ""
    try:
        p = urlsplit(raw_url)
        scheme = p.scheme.lower() or "https"
        netloc = p.netloc.lower()
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        if netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        blocked = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "source"
        }
        qs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
              if k.lower() not in blocked]
        qs.sort()

        return urlunsplit((
            scheme,
            netloc,
            p.path.rstrip("/") or "/",
            urlencode(qs, doseq=True),
            ""
        ))
    except Exception:
        return raw_url.rstrip("/")


def choose_query_targets(history):
    """Rotate through the keyword bank deterministically instead of random sampling."""
    cursor = int(history.get("query_cursor", 0) or 0)
    n = len(KEYWORDS)
    if not n:
        return [], cursor

    step = max(1, min(QUERY_STRIDE, n - 1))
    recent = {str(x).strip().lower() for x in history.get("recent_queries", [])[-QUERY_HISTORY_LIMIT:]}
    targets = []
    checked = 0
    offset = 0

    while len(targets) < TARGETS_PER_RUN and checked < n * 2:
        idx = (cursor + offset * step) % n
        candidate = KEYWORDS[idx]
        if candidate.lower() not in recent and candidate not in targets:
            targets.append(candidate)
        offset += 1
        checked += 1

    while len(targets) < min(TARGETS_PER_RUN, n):
        idx = (cursor + offset * step) % n
        candidate = KEYWORDS[idx]
        if candidate not in targets:
            targets.append(candidate)
        offset += 1

    next_cursor = (cursor + 1) % n
    return targets, next_cursor



def record_fingerprint(item):
    """Create a conservative fallback identity key for duplicate listings."""
    title = re.sub(r"[^a-z0-9]+", " ", str(item.get("original_title", "")).lower()).strip()
    platform = re.sub(r"[^a-z0-9]+", " ", str(item.get("platform", "")).lower()).strip()
    if not title or not platform:
        return ""
    return hashlib.sha1(f"{platform}|{title}".encode("utf-8")).hexdigest()


def derive_evidence(item, target):
    """Create explicit, auditable evidence flags from returned fields."""
    text = " ".join([
        str(item.get("original_title", "")),
        str(item.get("reason", "")),
        str(item.get("platform", "")),
        str(item.get("origin_region", "")),
        str(item.get("source_type", "")),
        str(target or "")
    ]).lower()

    def has_any(words):
        return any(w in text for w in words)

    evidence = {
        "sale_or_market_signal": has_any([
            "for sale", "sale", "auction", "listing", "marketplace", "dealer",
            "seller", "buy", "bidding", "price", "lot"
        ]),
        "provenance_missing_signal": (
            item.get("provenance_flag") is False and has_any([
                "no provenance", "without provenance", "no papers", "no documentation",
                "undocumented", "unknown provenance", "unclear provenance",
                "missing provenance", "no ownership history", "unknown origin"
            ])
        ),
        "trafficking_or_looting_signal": has_any([
            "trafficking", "smuggling", "looted", "loot", "stolen", "illicit",
            "black market", "seized", "seizure", "repatriat", "illegal export",
            "illegal import", "conflict zone", "war zone"
        ]),
        "export_or_legal_risk_signal": has_any([
            "export ban", "export restriction", "export permit", "customs",
            "cultural property law", "restricted", "prohibited", "permit required",
            "import restriction", "legal grey", "legal gray", "no papers"
        ]),
        "seller_opacity_signal": has_any([
            "anonymous seller", "anonymous", "unknown seller", "private seller",
            "discreet", "no questions asked", "anonymous payment", "crypto payment"
        ]),
        "authenticity_claim_signal": has_any([
            "authentic", "genuine", "ancient", "original", "authenticity"
        ]),
        "documented_provenance_signal": bool(item.get("provenance_flag")) or has_any([
            "provenance", "private collection", "public collection", "museum collection",
            "published collection", "acquired in", "formerly collection"
        ]),
        "news_or_institutional_context": has_any([
            "news", "museum", "university", "government", "police", "interpol",
            "unesco", "customs", "research", "academic"
        ])
    }

    return evidence


def calculate_evidence_risk(item, evidence):
    """Deterministic score based on observed signals; AI score is retained separately."""
    score = 0
    factors = []

    weights = [
        ("trafficking_or_looting_signal", 3, "Trafficking / looting signal"),
        ("provenance_missing_signal", 3, "Missing / unclear provenance"),
        ("export_or_legal_risk_signal", 2, "Export / legal-risk signal"),
        ("seller_opacity_signal", 1, "Seller / transaction opacity"),
        ("sale_or_market_signal", 1, "Active market / sale signal"),
    ]

    for key, points, label in weights:
        if evidence.get(key):
            score += points
            factors.append(label)

    if evidence.get("authenticity_claim_signal") and evidence.get("sale_or_market_signal"):
        score += 1
        factors.append("Authenticity claim attached to a market signal")

    if evidence.get("documented_provenance_signal") and not evidence.get("provenance_missing_signal"):
        score -= 3
        factors.append("Documented provenance signal")

    score = max(0, min(10, score))

    if score >= 8:
        status = "HIGH RISK"
    elif score >= 4:
        status = "MEDIUM RISK"
    else:
        status = "INFO ONLY"

    return score, status, factors


def enrich_item(item, target):
    """Normalise a model result and attach auditable evidence fields."""
    if not isinstance(item, dict):
        return None

    direct_url = item.get("canonical_source_url") or item.get("source_url") or item.get("url")
    canonical = normalize_url(direct_url)
    if not canonical:
        return None

    item["url"] = canonical
    item["keyword_trigger"] = target
    item["scraped_at"] = datetime.now().isoformat() + "Z"
    item.setdefault("first_seen", item["scraped_at"])
    item["last_seen"] = item["scraped_at"]
    item["seen_count"] = int(item.get("seen_count", 0) or 0) + 1
    item["new_in_last_crawl"] = True

    ai_score = item.get("risk_score")
    try:
        ai_score = int(round(float(ai_score)))
    except (TypeError, ValueError):
        ai_score = 0
    item["ai_risk_score"] = max(0, min(10, ai_score))

    evidence = derive_evidence(item, target)
    evidence_score, status, factors = calculate_evidence_risk(item, evidence)

    item["evidence"] = evidence
    item["risk_factors"] = factors
    item["risk_score"] = evidence_score
    item["status"] = status
    item["risk_method"] = "evidence_v6"

    item["record_fingerprint"] = record_fingerprint(item)

    if not item.get("screenshot_url"):
        item["screenshot_url"] = get_screenshot_url(canonical)

    return item


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
    """Run automatically every 4 days, or immediately if FORCE_CRAWL is true."""
    if os.environ.get("FORCE_CRAWL") == "true": 
        log.info("FORCE_CRAWL is active. Bypassing schedule.")
        return True
        
    if not os.path.exists(HISTORY_FILE): return True
    try:
        with open(HISTORY_FILE) as f:
            h = json.load(f)
        last = datetime.fromisoformat(h.get("last_crawl_date"))
        
        # 4-DAY INTERVAL CHECK
        days_passed = (datetime.now() - last).days
        if days_passed >= 4:
            log.info(f"{days_passed} days have passed. Executing scheduled crawl.")
            return True
        else:
            log.info(f"Only {days_passed} days passed since last crawl. Waiting for 4-day mark.")
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

def get_screenshot_url(url):
    """Generates a dynamic screenshot URL using a free API service."""
    if not url or url.lower() == "n/a":
        return "N/A"
    encoded_url = requests.utils.quote(url)
    return f"https://api.microlink.io/?url={encoded_url}&screenshot=true&meta=false&embed=screenshot.url"

# ======================================================================
# CORE: DIRECT REST API AI ANALYZER
# ======================================================================


def run_ai_search(api_key, existing_url_keys, target):
    log.info(f"Targeting keyword: {target}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    prompt = f"""
    Use Google Search grounding to find real, publicly accessible web sources relevant to:
    "{target}"

    Focus on actual artifact / antiquities listings, auction records, trafficking or looting reports,
    provenance issues, or credible institutional / news reporting. Prefer the original source page
    over a secondary article that merely mentions it.

    Return ONLY a JSON array. Each object must describe ONE distinct source/item.

    Important URL rule:
    - "canonical_source_url" must be the direct source URL you found.
    - NEVER return a vertexaisearch.cloud.google.com grounding redirect URL when a direct source URL is available.
    - Do not invent URLs.
    - If a direct source URL cannot be determined, return the grounded URL in "url" and set "canonical_source_url" to "".

    Required fields:
    [
      {{
        "original_title": "Original source/listing title",
        "platform": "Source/platform name",
        "source_type": "MARKETPLACE | AUCTION | NEWS | FORUM | SOCIAL | MUSEUM | ACADEMIC | GOVERNMENT | OTHER",
        "canonical_source_url": "Direct source URL or empty string",
        "url": "Source URL",
        "price_usd": 0,
        "origin_region": "Best-supported artifact origin region; use Unknown when not supported",
        "provenance_flag": false,
        "reason": "Concise evidence-based explanation of what was observed and why it matters",
        "risk_score": 0
      }}
    ]

    Risk score is ONLY an AI assessment and will be kept separately as ai_risk_score.
    Do not inflate risk merely because something is old, expensive, or sold by an auction house.

    Ignore already-known URLs (normalised comparison):
    {list(existing_url_keys)[:60]}
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}],
        "generationConfig": {
            "temperature": 0.2,
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
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if response.status_code != 200:
            log.error(f"Google API Error ({response.status_code}): {response.text}")
            return {"items": [], "grounding": {}}

        response_data = response.json()

        try:
            candidate = response_data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            log.error("Empty or rejected API response.")
            return {"items": [], "grounding": {}}

        grounding = candidate.get("groundingMetadata", {}) or {}
        log.info(f"Raw AI Output: {text[:180]}...")

        fence = chr(96) * 3
        clean_text = text.replace(fence + "json", "").replace(fence, "")
        clean_text = re.sub(r"\[\d+\]", "", clean_text)

        start_idx = clean_text.find("[")
        end_idx = clean_text.rfind("]")

        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            log.warning("AI did not provide a valid JSON Array.")
            return {"items": [], "grounding": grounding}

        try:
            items = json.loads(clean_text[start_idx:end_idx + 1])
        except json.JSONDecodeError as e:
            log.error(f"JSON Parse Error: {e}")
            return {"items": [], "grounding": grounding}

        if not isinstance(items, list):
            return {"items": [], "grounding": grounding}

        return {"items": items, "grounding": grounding}

    except Exception as e:
        log.error(f"AI Search Failed for '{target}': {e}")
        return {"items": [], "grounding": {}}


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

        history = {}
        source_history = {}
        source_history_file = os.path.join(BASE_DIR, "source_history.json")
        if os.path.exists(source_history_file):
            try:
                with open(source_history_file, encoding="utf-8") as f:
                    source_history = json.load(f)
            except Exception:
                source_history = {}
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = {}

        crawl_now = datetime.now().isoformat() + "Z"
        for item in listings:
            item.setdefault("first_seen", item.get("scraped_at") or crawl_now)
            item["last_seen"] = crawl_now
            item["seen_count"] = int(item.get("seen_count", 0) or 0) + 1
            item["new_in_last_crawl"] = False

        backfill_count = 0
        for item in listings:
            if not item.get("screenshot_url"):
                url_value = item.get("url")
                if url_value:
                    item["screenshot_url"] = get_screenshot_url(url_value)
                else:
                    item["screenshot_url"] = "N/A"
                backfill_count += 1

        existing_url_keys = set()
        existing_fingerprints = set()
        for item in listings:
            key = normalize_url(
                item.get("canonical_source_url") or
                item.get("source_url") or
                item.get("url")
            )
            if key:
                existing_url_keys.add(key)
            fp = item.get("record_fingerprint") or record_fingerprint(item)
            if fp:
                existing_fingerprints.add(fp)

        targets, next_cursor = choose_query_targets(history)
        log.info(f"Selected {len(targets)} targets: {targets}")

        count = 0
        duplicate_count = 0
        grounding_source_count = 0

        recent_queries = list(history.get("recent_queries", []))

        for target in targets:
            result = run_ai_search(api_key, existing_url_keys, target)
            new_items = result.get("items", []) if isinstance(result, dict) else []

            grounding = result.get("grounding", {}) if isinstance(result, dict) else {}
            grounding_chunks = grounding.get("groundingChunks", []) or []
            grounding_source_count += len([
                c for c in grounding_chunks
                if isinstance(c, dict)
                and isinstance(c.get("web"), dict)
                and c["web"].get("uri")
            ])

            for raw_item in new_items:
                item = enrich_item(raw_item, target)
                if not item:
                    continue

                link_key = normalize_url(
                    item.get("canonical_source_url") or item.get("url")
                )
                if not link_key:
                    continue

                fingerprint = item.get("record_fingerprint") or record_fingerprint(item)
                if link_key in existing_url_keys or (fingerprint and fingerprint in existing_fingerprints):
                    duplicate_count += 1
                    continue

                listings.append(item)
                existing_url_keys.add(link_key)
                if fingerprint:
                    existing_fingerprints.add(fingerprint)
                count += 1

            recent_queries.append(target)
            time.sleep(3)

        source_monitor = update_source_history(listings, source_history)

        db["listings"] = listings
        db["summary"] = calculate_summary(listings)
        db["summary"]["source_active_count"] = source_monitor["active"]
        db["summary"]["source_current_removed_count"] = source_monitor["removed"]
        db["summary"]["source_current_unavailable_count"] = source_monitor["unavailable"]
        db["summary"]["source_redirected_count"] = source_monitor["redirected"]
        db["summary"]["source_changed_count"] = source_monitor["content_change_events"]
        db["summary"]["source_removed_count"] = source_monitor["removed_events"]
        db["summary"]["source_unavailable_count"] = source_monitor["unavailable_events"]
        db["summary"]["source_recovered_count"] = source_monitor["recovered"]
        db["summary"]["snapshot_field_change_events"] = source_monitor["snapshot_field_change_events"]
        db["summary"]["snapshot_title_change_events"] = source_monitor["title_change_events"]
        db["summary"]["snapshot_description_change_events"] = source_monitor["description_change_events"]
        db["summary"]["snapshot_price_change_events"] = source_monitor["price_change_events"]
        db["summary"]["snapshot_image_change_events"] = source_monitor["image_change_events"]
        db["summary"]["snapshot_provenance_change_events"] = source_monitor["provenance_change_events"]
        db["summary"]["snapshot_risk_change_events"] = source_monitor["risk_change_events"]
        db["summary"]["provenanced_count"] = sum(
            1 for x in listings if x.get("provenance_flag")
        )
        db["summary"]["no_provenance_count"] = sum(
            1 for x in listings
            if x.get("evidence", {}).get("provenance_missing_signal")
        )
        db["summary"]["trafficking_signal_count"] = sum(
            1 for x in listings
            if x.get("evidence", {}).get("trafficking_or_looting_signal")
        )

        if (count > 0 or backfill_count > 0 or source_monitor["removed_events"] > 0 or
                source_monitor["content_change_events"] > 0 or source_monitor["recovered"] > 0 or
                source_monitor["unavailable_events"] > 0 or not db["summary"].get("generated_at")):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)

        with open(source_history_file, "w", encoding="utf-8") as f:
            json.dump(source_history, f, indent=2, ensure_ascii=False)

        recent_queries = recent_queries[-QUERY_HISTORY_LIMIT:]
        history_out = {
            "last_crawl_date": datetime.now().isoformat(),
            "script_hash": get_hash(SCRIPT_FILE),
            "query_cursor": next_cursor,
            "recent_queries": recent_queries,
            "targets_per_run": TARGETS_PER_RUN,
            "crawl_version": "v7.0",
            "source_monitor": source_monitor
        }

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_out, f, indent=2, ensure_ascii=False)

        log.info(
            f"✅ Run Complete. Added {count} new items, skipped {duplicate_count} duplicates, "
            f"grounding sources seen {grounding_source_count}. Total Database: {len(listings)} items."
        )

    except Exception as e:
        log.error(f"Fatal Error during main execution: {e}")

if __name__ == "__main__":
    main()
