from __future__ import annotations

import json
import logging
from typing import Any

from artifact_radar import gemini as gemini_mod
from artifact_radar.json_extract import extract_json_object

log = logging.getLogger("ArtifactRadar.Reasoner")

REASONER_PROMPT = """You synthesize a short analyst note for cultural-heritage monitoring dashboards.
Inputs are a search keyword, a web candidate, and a structured risk classification. Stay factual; flag uncertainty explicitly.

Keyword: "{keyword}"

Candidate:
{candidate_json}

Classification:
{class_json}

Output STRICTLY one JSON object (no markdown):
{{
  "reason": "2–4 sentences for dashboard display: what was observed and why the score applies",
  "uncertainty_flags": ["optional short bullet strings, e.g. single_source, price_unknown"],
  "evidence_that_would_change_assessment": "what additional documentation or signals would raise or lower confidence",
  "confidence": "low|medium|high"
}}
"""


def reason_over(
    api_key: str,
    keyword: str,
    candidate: dict[str, Any],
    classification: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    meta: dict[str, Any] = {}
    prompt = REASONER_PROMPT.format(
        keyword=keyword,
        candidate_json=json.dumps(candidate, ensure_ascii=False, indent=2),
        class_json=json.dumps(classification, ensure_ascii=False, indent=2),
    )
    res = gemini_mod.generate_content(
        api_key,
        prompt,
        use_google_search=False,
        temperature=0.35,
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

    flags = obj.get("uncertainty_flags") or []
    if not isinstance(flags, list):
        flags = [str(flags)]
    flags = [str(x)[:200] for x in flags][:20]

    conf = str(obj.get("confidence") or "medium").lower()
    if conf not in ("low", "medium", "high"):
        conf = "medium"

    out = {
        "reason": str(obj.get("reason") or classification.get("classification_notes") or "")[
            :2000
        ],
        "uncertainty_flags": flags,
        "evidence_that_would_change_assessment": str(
            obj.get("evidence_that_would_change_assessment") or ""
        )[:1200],
        "confidence": conf,
    }
    return out, meta
