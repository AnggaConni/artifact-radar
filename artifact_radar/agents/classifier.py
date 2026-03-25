from __future__ import annotations

import json
import logging
from typing import Any

from artifact_radar import gemini as gemini_mod
from artifact_radar.json_extract import extract_json_object

log = logging.getLogger("ArtifactRadar.Classifier")

CLASSIFIER_PROMPT = """You are a heritage-monitoring analyst scoring publicly visible pages for documentation (ICOM / due-diligence style).
You receive one candidate record (from open web search). Do not assist trafficking; assess documented signals only.

Monitoring query keyword: "{keyword}"

Candidate JSON:
{candidate_json}

Apply this rubric for risk_score (integer 0–10):
- 8–10 (HIGH): clear signals of unprovenanced cultural objects offered for sale, looting/theft news, explicit "no provenance", conflict-zone heritage risk, or smuggling reports.
- 4–7 (MEDIUM): vague provenance, mixed signals, auction without clear chain of title, or needs expert review.
- 1–3 (LOW): benign collector discussion, museum/repatriation news with no sale, or weak relevance.
- 0 (INFO): informational only.

Map risk_score to status:
- 8–10 → "HIGH RISK"
- 4–7 → "MEDIUM RISK"
- 1–3 → "LOW RISK"
- 0 → "INFO ONLY"

provenance_flag = true only if the text explicitly indicates documented provenance or legal export/collection history; else false.

Output STRICTLY one JSON object (no markdown):
{{
  "status": "HIGH RISK|MEDIUM RISK|LOW RISK|INFO ONLY",
  "risk_score": 0,
  "origin_region": "best-effort geographic/cultural attribution or Unknown",
  "provenance_flag": false,
  "price_usd": 0,
  "listing_kind": "sale_listing|auction|news|forum|social|other",
  "classification_notes": "max 2 sentences, internal-style"
}}
If the URL/title are unusable, return risk_score 0, status "INFO ONLY", and explain in classification_notes.
"""

REPAIR_CLASSIFIER_PROMPT = """Heritage monitoring: output ONLY a JSON object (no markdown) scoring this single web candidate.
Keyword: "{keyword}"
Candidate:
{candidate_json}

Return compact JSON:
{{
  "status": "HIGH RISK|MEDIUM RISK|LOW RISK|INFO ONLY",
  "risk_score": 0,
  "origin_region": "string",
  "provenance_flag": false,
  "price_usd": 0,
  "listing_kind": "other",
  "classification_notes": "one sentence"
}}
Use the same 0–10 rubric as institutional due-diligence (higher = more concern for illicit trade signals). If unsure, use MEDIUM RISK and score 4–5.
"""


def _normalize_classification(obj: dict[str, Any]) -> dict[str, Any] | None:
    if not obj:
        return None
    try:
        score = int(obj.get("risk_score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(10, score))

    status = str(obj.get("status") or "INFO ONLY")
    allowed = {"HIGH RISK", "MEDIUM RISK", "LOW RISK", "INFO ONLY"}
    if status not in allowed:
        status = "INFO ONLY"

    price = obj.get("price_usd", 0)
    try:
        price_f = float(price)
    except (TypeError, ValueError):
        price_f = 0.0

    return {
        "status": status,
        "risk_score": score,
        "origin_region": str(obj.get("origin_region") or "Unknown")[:500],
        "provenance_flag": bool(obj.get("provenance_flag")),
        "price_usd": int(price_f) if price_f == int(price_f) else round(price_f, 2),
        "listing_kind": str(obj.get("listing_kind") or "other")[:64],
        "classification_notes": str(obj.get("classification_notes") or "")[:800],
    }


def classify_candidate(
    api_key: str,
    keyword: str,
    candidate: dict[str, Any],
    *,
    repair: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Returns (classification dict or None, meta)."""
    meta: dict[str, Any] = {"repair": repair}
    body = json.dumps(candidate, ensure_ascii=False, indent=2)
    template = REPAIR_CLASSIFIER_PROMPT if repair else CLASSIFIER_PROMPT
    prompt = template.format(keyword=keyword, candidate_json=body)

    res = gemini_mod.generate_content(
        api_key,
        prompt,
        use_google_search=False,
        temperature=0.1 if repair else 0.15,
        max_output_tokens=2048,
    )
    meta["gemini_ok"] = res.get("ok")
    meta["http_status"] = res.get("http_status")
    meta["error"] = res.get("error")
    if not res.get("ok"):
        return None, meta

    obj = extract_json_object(res.get("text") or "")
    if not obj:
        meta["parse_error"] = True
        return None, meta

    out = _normalize_classification(obj)
    return out, meta
