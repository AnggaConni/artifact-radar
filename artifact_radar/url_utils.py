from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PARAMS = frozenset(
    p.lower()
    for p in (
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
    )
)


def normalize_url(url: str | None) -> str | None:
    """Normalize URL for deduplication (best-effort)."""
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u or u.lower() == "n/a":
        return None
    try:
        parts = urlsplit(u)
        if not parts.scheme or not parts.netloc:
            return u.lower()
        netloc = parts.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parts.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        q = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in _TRACKING_PARAMS
        ]
        query = urlencode(q)
        return urlunsplit((parts.scheme.lower(), netloc, path, query, ""))
    except Exception:
        return u.lower()
