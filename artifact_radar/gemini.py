from __future__ import annotations

import logging
from typing import Any

import requests

from artifact_radar.config import GENERATE_URL

log = logging.getLogger("ArtifactRadar.Gemini")

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


def generate_content(
    api_key: str,
    prompt: str,
    *,
    use_google_search: bool = True,
    temperature: float = 0.35,
    max_output_tokens: int = 8192,
    timeout_sec: int = 120,
) -> dict[str, Any]:
    """
    Call Gemini generateContent. Returns:
      ok, text (str), http_status, error (optional), raw_block_reason (optional)
    """
    url = f"{GENERATE_URL}?key={api_key}"
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
        "safetySettings": SAFETY_SETTINGS,
    }
    if use_google_search:
        payload["tools"] = [{"google_search": {}}]

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_sec,
        )
    except requests.RequestException as e:
        return {"ok": False, "text": "", "http_status": 0, "error": str(e)}

    try:
        data = resp.json()
    except Exception:
        return {
            "ok": False,
            "text": "",
            "http_status": resp.status_code,
            "error": resp.text[:500],
        }

    if resp.status_code != 200:
        err = data.get("error", {}).get("message") or resp.text[:500]
        log.error("Gemini HTTP %s: %s", resp.status_code, err)
        return {
            "ok": False,
            "text": "",
            "http_status": resp.status_code,
            "error": err,
        }

    block = data.get("promptFeedback", {}).get("blockReason")
    candidates = data.get("candidates") or []
    if not candidates:
        return {
            "ok": False,
            "text": "",
            "http_status": resp.status_code,
            "error": "empty_candidates",
            "raw_block_reason": block,
        }

    try:
        parts = candidates[0].get("content", {}).get("parts") or []
        text = parts[0].get("text") or ""
    except (IndexError, KeyError, TypeError):
        text = ""

    if not text.strip():
        return {
            "ok": False,
            "text": "",
            "http_status": resp.status_code,
            "error": "no_text_in_response",
            "raw_block_reason": candidates[0].get("finishReason"),
        }

    return {"ok": True, "text": text, "http_status": resp.status_code}
