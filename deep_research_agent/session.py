"""Run-directory management: every research session is isolated and idempotent.

Layout (borrowed from the wide-research playbook):

    runs/20260829-143000-my-topic/
        scratchpad.md          shared agent memory
        manifest.json          wide-research subtask manifest
        child_outputs/         one markdown report per wide worker
        raw/                   cached search/scrape payloads
        logs/                  per-worker logs + prompt dumps (debug)
        final_report.md        programmatic aggregation output
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path


def _slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text or "session")[:max_len].rstrip("-")


class Session:
    def __init__(self, root: str | Path = "runs", topic: str = "session"):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.path = Path(root) / f"{stamp}-{_slugify(topic)}"
        self.path.mkdir(parents=True, exist_ok=True)
        for sub in ("child_outputs", "raw", "logs"):
            (self.path / sub).mkdir(exist_ok=True)

    # convenience accessors -------------------------------------------------
    @property
    def scratchpad_path(self) -> Path:
        return self.path / "scratchpad.md"

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    def child_output(self, subtask_id: str) -> Path:
        return self.path / "child_outputs" / f"{subtask_id}.md"

    def raw_path(self, key: str) -> Path:
        return self.path / "raw" / f"{key}.json"

    def log_path(self, name: str) -> Path:
        return self.path / "logs" / f"{name}.log"

    def write_manifest(self, subtasks: list[dict]) -> Path:
        self.manifest_path.write_text(
            json.dumps({"subtasks": subtasks}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        return self.manifest_path

    def read_manifest(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))["subtasks"]

    def summary(self) -> str:
        children = list((self.path / "child_outputs").glob("*.md"))
        return (f"session dir : {self.path}\n"
                f"child reports: {len(children)}\n"
                f"final report: {(self.path / 'final_report.md').exists()}")
