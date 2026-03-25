import json
import os
import tempfile

from artifact_radar.step_log import StepLogger


def test_step_logger_writes_jsonl():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "steps.jsonl")
        log = StepLogger(path)
        log.log(agent="collector", step="start", keyword="k", extra={"n": 1})
        log.log(agent="classifier", step="complete", keyword="k", extra={"ok": True})
        with open(path, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        assert len(lines) == 2
        r0 = json.loads(lines[0])
        assert r0["agent"] == "collector"
        assert r0["keyword"] == "k"


def test_step_logger_disabled():
    log = StepLogger(None)
    log.log(agent="x", step="y")  # no crash
