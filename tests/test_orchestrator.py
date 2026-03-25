from unittest.mock import patch

from artifact_radar.orchestrator import run_pipeline_for_keyword, run_multi_agent_crawl
from artifact_radar.step_log import StepLogger


def _fake_screenshot(u: str) -> str:
    return f"https://screenshot.test/?u={u}"


def test_run_pipeline_full_flow(monkeypatch):
    calls = {"n": 0}

    def fake_generate(api_key, prompt, **kwargs):
        calls["n"] += 1
        use_search = kwargs.get("use_google_search", True)
        if use_search and "monitoring query" in prompt and "Repair" not in prompt:
            return {
                "ok": True,
                "text": '[{"title": "T1", "url": "https://listing.example/item", "platform_guess": "eBay", "snippet_summary": "Sale listing.", "source_context": "marketplace"}]',
            }
        if use_search:
            return {"ok": True, "text": "[]"}
        if "synthesize" in prompt.lower() or "dashboard" in prompt.lower():
            return {
                "ok": True,
                "text": '{"reason": "Observed a public listing without provenance language.", "uncertainty_flags": ["single_source"], "evidence_that_would_change_assessment": "Export paperwork.", "confidence": "medium"}',
            }
        return {
            "ok": True,
            "text": '{"status": "MEDIUM RISK", "risk_score": 5, "origin_region": "Unknown", "provenance_flag": false, "price_usd": 100, "listing_kind": "sale_listing", "classification_notes": "Vague provenance."}',
        }

    with patch("artifact_radar.gemini.generate_content", side_effect=fake_generate):
        items, stats = run_pipeline_for_keyword(
            "k",
            "roman coin sale",
            set(),
            get_screenshot_url=_fake_screenshot,
            step_logger=StepLogger(None),
            max_candidates=2,
            delay_sec=0,
        )

    assert stats["listings_added"] == 1
    assert len(items) == 1
    assert items[0]["url"] == "https://listing.example/item"
    assert items[0]["risk_score"] == 5
    assert items[0]["pipeline"]["confidence"] == "medium"
    assert "uncertainty_flags" in items[0]["pipeline"]


def test_collector_repair_triggers(monkeypatch):
    seq = iter(
        [
            {"ok": False, "text": "", "http_status": 500, "error": "boom"},
            {
                "ok": True,
                "text": '[{"title": "N", "url": "https://news.example/a", "platform_guess": "News", "snippet_summary": "Article.", "source_context": "news"}]',
            },
            {
                "ok": True,
                "text": '{"status": "INFO ONLY", "risk_score": 0, "origin_region": "EU", "provenance_flag": false, "price_usd": 0, "listing_kind": "news", "classification_notes": "News only."}',
            },
            {
                "ok": True,
                "text": '{"reason": "News article.", "uncertainty_flags": [], "evidence_that_would_change_assessment": "N/A", "confidence": "high"}',
            },
        ]
    )

    def fake_generate(api_key, prompt, **kwargs):
        return next(seq)

    with patch("artifact_radar.gemini.generate_content", side_effect=fake_generate):
        items, stats = run_pipeline_for_keyword(
            "k",
            "test keyword",
            set(),
            get_screenshot_url=_fake_screenshot,
            step_logger=StepLogger(None),
            max_candidates=2,
            delay_sec=0,
        )

    assert stats["collector_repair_used"] is True
    assert len(items) == 1
    assert items[0]["platform"] == "News"


def test_classifier_repair(monkeypatch):
    def fake_generate(api_key, prompt, **kwargs):
        use_search = kwargs.get("use_google_search", True)
        if use_search:
            return {
                "ok": True,
                "text": '[{"title": "X", "url": "https://x.example/1", "platform_guess": "X", "snippet_summary": "S", "source_context": "marketplace"}]',
            }
        if "compact JSON" in prompt or kwargs.get("temperature") == 0.1:
            return {
                "ok": True,
                "text": '{"status": "LOW RISK", "risk_score": 2, "origin_region": "Unknown", "provenance_flag": false, "price_usd": 0, "listing_kind": "other", "classification_notes": "repair"}',
            }
        if "heritage-monitoring analyst" in prompt:
            return {"ok": False, "text": "", "error": "fail"}
        return {
            "ok": True,
            "text": '{"reason": "R", "uncertainty_flags": [], "evidence_that_would_change_assessment": "", "confidence": "low"}',
        }

    with patch("artifact_radar.gemini.generate_content", side_effect=fake_generate):
        items, stats = run_pipeline_for_keyword(
            "k",
            "kw",
            set(),
            get_screenshot_url=_fake_screenshot,
            step_logger=StepLogger(None),
            max_candidates=1,
            delay_sec=0,
        )

    assert stats["classifier_repairs"] >= 1
    assert items[0]["risk_score"] == 2


def test_multi_keyword_dedup_normalized(monkeypatch):
    def fake_generate(api_key, prompt, **kwargs):
        use_search = kwargs.get("use_google_search", True)
        if not use_search and "synthesize" in prompt.lower():
            return {
                "ok": True,
                "text": '{"reason": "R", "uncertainty_flags": [], "evidence_that_would_change_assessment": "", "confidence": "high"}',
            }
        if not use_search:
            return {
                "ok": True,
                "text": '{"status": "INFO ONLY", "risk_score": 0, "origin_region": "U", "provenance_flag": false, "price_usd": 0, "listing_kind": "other", "classification_notes": "n"}',
            }
        return {
            "ok": True,
            "text": '[{"title": "Same", "url": "https://EXAMPLE.com/a?utm_source=1", "platform_guess": "P", "snippet_summary": "S", "source_context": "other"}]',
        }

    with patch("artifact_radar.gemini.generate_content", side_effect=fake_generate):
        new, _ = run_multi_agent_crawl(
            "k",
            ["kw1", "kw2"],
            set(),
            get_screenshot_url=_fake_screenshot,
            step_logger=StepLogger(None),
            max_candidates_per_keyword=1,
            delay_sec=0,
        )

    assert len(new) == 1
