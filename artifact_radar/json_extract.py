from __future__ import annotations

import json
import re


def _strip_fences(text: str) -> str:
    t = text.replace("```json", "").replace("```JSON", "").replace("```", "")
    return re.sub(r"\[\d+\]", "", t)


def extract_json_array(text: str) -> list | None:
    """Extract the first top-level JSON array from model output."""
    if not text:
        return None
    clean = _strip_fences(text)
    start = clean.find("[")
    end = clean.rfind("]")
    if start == -1 or end == -1 or start >= end:
        return None
    chunk = clean[start : end + 1]
    try:
        data = json.loads(chunk)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None


def extract_json_object(text: str) -> dict | None:
    """Extract the first top-level JSON object from model output."""
    if not text:
        return None
    clean = _strip_fences(text)
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    chunk = clean[start : end + 1]
    try:
        data = json.loads(chunk)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
