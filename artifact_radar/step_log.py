from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


class StepLogger:
    """Append-only JSONL log for multi-agent pipeline steps."""

    def __init__(self, path: str | None) -> None:
        self.path = path
        self.enabled = bool(path)

    def log(
        self,
        *,
        agent: str,
        step: str,
        keyword: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled or not self.path:
            return
        row: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "step": step,
        }
        if keyword is not None:
            row["keyword"] = keyword
        if extra:
            row.update(extra)
        line = json.dumps(row, ensure_ascii=False)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
