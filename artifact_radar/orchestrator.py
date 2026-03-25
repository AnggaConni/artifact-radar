from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Callable

from artifact_radar.agents.classifier import classify_candidate
from artifact_radar.agents.collector import collect_candidates
from artifact_radar.agents.reasoner import reason_over
from artifact_radar.config import DEFAULT_MAX_CANDIDATES_PER_KEYWORD, REQUEST_DELAY_SEC
from artifact_radar.step_log import StepLogger
from artifact_radar.url_utils import normalize_url

log = logging.getLogger("ArtifactRadar.Orchestrator")


def _merge_listing(
    *,
    keyword: str,
    candidate: dict[str, Any],
    classification: dict[str, Any],
    reasoning: dict[str, Any] | None,
    scraped_at: str,
    screenshot_url: str,
    repair_flags: dict[str, bool],
) -> dict[str, Any]:
    reason = ""
    uncertainty: list[str] = []
    evidence_gap = ""
    confidence = "low"

    if reasoning:
        reason = reasoning.get("reason") or classification.get("classification_notes", "")
        uncertainty = list(reasoning.get("uncertainty_flags") or [])
        evidence_gap = reasoning.get("evidence_that_would_change_assessment") or ""
        confidence = reasoning.get("confidence") or "medium"
    else:
        reason = classification.get("classification_notes", "") or (
            f"Automated classification: {classification.get('status')} (score {classification.get('risk_score')})."
        )
        uncertainty = ["reasoner_unavailable"]
        evidence_gap = "Analyst review or live page inspection recommended."
        confidence = "low"

    pipeline = {
        "version": "6.0",
        "uncertainty_flags": uncertainty,
        "evidence_that_would_change_assessment": evidence_gap,
        "confidence": confidence,
        "source_context": candidate.get("source_context"),
        "listing_kind": classification.get("listing_kind"),
        "collector_repair": repair_flags.get("collector_repair", False),
        "classifier_repair": repair_flags.get("classifier_repair", False),
    }

    return {
        "original_title": candidate.get("title") or "Unknown",
        "platform": candidate.get("platform_guess") or "Unknown",
        "url": candidate.get("url"),
        "price_usd": classification.get("price_usd", 0),
        "status": classification.get("status", "INFO ONLY"),
        "risk_score": classification.get("risk_score", 0),
        "origin_region": classification.get("origin_region", "Unknown"),
        "provenance_flag": classification.get("provenance_flag", False),
        "keyword_trigger": keyword,
        "reason": reason,
        "scraped_at": scraped_at,
        "screenshot_url": screenshot_url,
        "pipeline": pipeline,
    }


def run_pipeline_for_keyword(
    api_key: str,
    keyword: str,
    existing_norm_urls: set[str],
    *,
    get_screenshot_url: Callable[[str], str],
    step_logger: StepLogger | None = None,
    max_candidates: int = DEFAULT_MAX_CANDIDATES_PER_KEYWORD,
    delay_sec: float = REQUEST_DELAY_SEC,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Execute collect → classify → reason for one keyword.
    Returns (new_listings, run_stats).
    """
    stats: dict[str, Any] = {
        "keyword": keyword,
        "candidates_raw": 0,
        "listings_added": 0,
        "collector_repair_used": False,
        "classifier_repairs": 0,
    }
    repair_flags = {"collector_repair": False, "classifier_repair": False}
    exclude = list(existing_norm_urls)[:30]

    def slog(agent: str, step: str, **kw: Any) -> None:
        if step_logger:
            step_logger.log(agent=agent, step=step, keyword=keyword, extra=kw)

    slog("collector", "start", exclude_count=len(exclude))
    candidates, c_meta = collect_candidates(
        api_key, keyword, exclude, max_items=max_candidates + 2, repair=False
    )
    slog(
        "collector",
        "complete",
        gemini_ok=c_meta.get("gemini_ok"),
        error=c_meta.get("error"),
        count=len(candidates),
    )

    if not candidates:
        slog("collector", "repair_trigger", reason="empty_or_failed")
        repair_flags["collector_repair"] = True
        stats["collector_repair_used"] = True
        candidates, c_meta2 = collect_candidates(
            api_key, keyword, exclude, max_items=max_candidates + 2, repair=True
        )
        slog(
            "collector",
            "repair_complete",
            gemini_ok=c_meta2.get("gemini_ok"),
            error=c_meta2.get("error"),
            count=len(candidates),
        )

    stats["candidates_raw"] = len(candidates)
    if not candidates:
        log.warning("No candidates for keyword=%r after repair.", keyword)
        slog("orchestrator", "skip_keyword", reason="no_candidates")
        return [], stats

    new_listings: list[dict[str, Any]] = []
    time.sleep(delay_sec)

    for cand in candidates[:max_candidates]:
        url = cand.get("url")
        norm = normalize_url(url)
        if not norm or norm in existing_norm_urls:
            slog("orchestrator", "skip_duplicate", url=url)
            continue

        slog("classifier", "start", url=url)
        cls, cl_meta = classify_candidate(api_key, keyword, cand, repair=False)
        if cls is None:
            slog("classifier", "repair_trigger", error=cl_meta.get("error"))
            repair_flags["classifier_repair"] = True
            stats["classifier_repairs"] += 1
            time.sleep(delay_sec)
            cls, cl_meta = classify_candidate(api_key, keyword, cand, repair=True)

        slog(
            "classifier",
            "complete",
            gemini_ok=cl_meta.get("gemini_ok"),
            error=cl_meta.get("error"),
            parse_error=cl_meta.get("parse_error"),
        )

        if cls is None:
            log.warning("Classifier failed for url=%s", url)
            slog("orchestrator", "skip_candidate", reason="classifier_failed", url=url)
            time.sleep(delay_sec)
            continue

        time.sleep(delay_sec)
        slog("reasoner", "start", url=url)
        reasoning, r_meta = reason_over(api_key, keyword, cand, cls)
        slog(
            "reasoner",
            "complete",
            gemini_ok=r_meta.get("gemini_ok"),
            error=r_meta.get("error"),
            parse_error=r_meta.get("parse_error"),
        )

        scraped_at = datetime.now().isoformat() + "Z"
        shot = get_screenshot_url(url or "")
        listing = _merge_listing(
            keyword=keyword,
            candidate=cand,
            classification=cls,
            reasoning=reasoning,
            scraped_at=scraped_at,
            screenshot_url=shot,
            repair_flags=repair_flags,
        )
        new_listings.append(listing)
        existing_norm_urls.add(norm)
        stats["listings_added"] += 1

        time.sleep(delay_sec)

    return new_listings, stats


def run_multi_agent_crawl(
    api_key: str,
    keywords: list[str],
    existing_urls_raw: set[str],
    *,
    get_screenshot_url: Callable[[str], str],
    step_logger: StepLogger | None = None,
    max_candidates_per_keyword: int = DEFAULT_MAX_CANDIDATES_PER_KEYWORD,
    delay_sec: float = REQUEST_DELAY_SEC,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run pipeline for each keyword in sequence.
    Returns (all_new_listings, per_keyword_stats).
    """
    existing_norm: set[str] = set()
    for u in existing_urls_raw:
        nu = normalize_url(u)
        if nu:
            existing_norm.add(nu)

    all_new: list[dict[str, Any]] = []
    all_stats: list[dict[str, Any]] = []

    for kw in keywords:
        items, st = run_pipeline_for_keyword(
            api_key,
            kw,
            set(existing_norm),
            get_screenshot_url=get_screenshot_url,
            step_logger=step_logger,
            max_candidates=max_candidates_per_keyword,
            delay_sec=delay_sec,
        )
        all_stats.append(st)
        for it in items:
            all_new.append(it)
            nu = normalize_url(it.get("url"))
            if nu:
                existing_norm.add(nu)

    return all_new, all_stats
