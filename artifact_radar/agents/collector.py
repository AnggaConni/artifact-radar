from __future__ import annotations

import json
import logging
from typing import Any

from artifact_radar import gemini as gemini_mod
from artifact_radar.json_extract import extract_json_array

log = logging.getLogger("ArtifactRadar.Collector")

COLLECTOR_PROMPT = """You assist cultural-heritage monitoring and OSINT researchers (e.g. UNESCO-aligned illicit-trade awareness).
Use Google Search to find publicly indexed pages relevant to this monitoring query: "{keyword}".

Task: propose candidate records for documentation only. Include marketplace listings, auction catalogs, news, or forum threads that appear in search results.
Do not provide instructions to buy, sell, smuggle, or evade law. If results are sparse, return an empty array.

Already captured URLs to avoid duplicating (same listing): {exclude_urls}

Output STRICTLY a JSON array (no markdown fences) of up to {max_items} objects with this shape:
[
  {{
    "title": "page or listing title as shown",
    "url": "https://... full canonical URL if known",
    "platform_guess": "human-readable site or publisher name",
    "snippet_summary": "one factual sentence: what the page appears to be (listing, news, auction, etc.)",
    "source_context": "marketplace|auction|news|forum|social|other"
  }}
]
"""

REPAIR_COLLECTOR_PROMPT = """You assist cultural-heritage researchers documenting publicly visible web pages.
Use Google Search for: "{keyword}"

Extract only bibliographic-style facts for up to {max_items} distinct URLs that appear relevant to cultural property trade or heritage news.
Skip duplicates of: {exclude_urls}

Return STRICTLY a JSON array (no markdown) of objects:
[
  {{
    "title": "string",
    "url": "https://...",
    "platform_guess": "string",
    "snippet_summary": "neutral one-line description of page type and topic",
    "source_context": "marketplace|auction|news|forum|social|other"
  }}
]
If no suitable public pages are found, return [].
"""


def _parse_candidates(raw_text: str) -> list[dict[str, Any]]:
    data = extract_json_array(raw_text)
    if not data:
        return []
    out: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        if not url or not url.lower().startswith(("http://", "https://")):
            continue
        out.append(
            {
                "title": (item.get("title") or "Untitled")[:500],
                "url": url[:2048],
                "platform_guess": (item.get("platform_guess") or "Unknown")[:200],
                "snippet_summary": (item.get("snippet_summary") or "")[:1200],
                "source_context": (item.get("source_context") or "other")[:64],
            }
        )
    return out


def collect_candidates(
    api_key: str,
    keyword: str,
    exclude_urls: list[str],
    *,
    max_items: int = 8,
    repair: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Run collector agent. Returns (candidates, meta) where meta includes raw_ok, error, repair flag.
    """
    excl = json.dumps(exclude_urls[:20], ensure_ascii=False)
    template = REPAIR_COLLECTOR_PROMPT if repair else COLLECTOR_PROMPT
    prompt = template.format(keyword=keyword, exclude_urls=excl, max_items=max_items)

    meta: dict[str, Any] = {"repair": repair}
    res = gemini_mod.generate_content(
        api_key,
        prompt,
        use_google_search=True,
        temperature=0.25 if repair else 0.4,
    )
    meta["gemini_ok"] = res.get("ok")
    meta["http_status"] = res.get("http_status")
    meta["error"] = res.get("error")
    if not res.get("ok"):
        return [], meta

    candidates = _parse_candidates(res.get("text") or "")
    meta["raw_count"] = len(candidates)
    return candidates[:max_items], meta
