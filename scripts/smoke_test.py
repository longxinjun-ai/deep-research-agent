#!/usr/bin/env python3
"""Offline sanity check: no network, no API keys required.

Run:  python scripts/smoke_test.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from deep_research_agent.scratchpad import Scratchpad, SECTIONS  # noqa: E402
from deep_research_agent.session import Session  # noqa: E402
from deep_research_agent.usage import TokenTracker  # noqa: E402
from deep_research_agent.tools import build_dispatcher  # noqa: E402
from deep_research_agent.tools.files import _safe_path  # noqa: E402
from deep_research_agent import wide  # noqa: E402

ok = 0


def check(name: str, cond: bool) -> None:
    global ok
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        sys.exit(1)
    ok += 1


with tempfile.TemporaryDirectory() as td:
    td = Path(td)

    # --- scratchpad ---------------------------------------------------------
    pad = Scratchpad(td / "scratchpad.md")
    pad.append("Background and Motivation", "Initial research query: test query", "Planner")
    pad.append("Next Steps and Action Items", "Search 3 keyword variants", "Planner")
    check("scratchpad creates 8 sections",
          all(s in pad.read() for s in SECTIONS))
    check("scratchpad append is attributed",
          "[Planner @" in pad.get_section("Background and Motivation"))
    pad.replace_section("Current Status / Progress Tracking", "| task | status |\n|---|---|\n| t1 | done |", "Executor")
    check("scratchpad replace preserves other sections",
          "test query" in pad.read() and "t1" in pad.get_section("Current Status / Progress Tracking"))
    pad.add_claims([("zero-config", "Tier 1", "github issues")])
    check("claim ledger gets table rows",
          "| zero-config | Tier 1 | github issues | pending |" in pad.get_section("Claim Ledger"))

    # --- session --------------------------------------------------------------
    s = Session(td / "runs", "Smoke Test: 深 度 调研!!")
    check("session slug is filesystem-safe",
          " " not in s.path.name and s.path.name.split("-", 3)[-1].isascii())
    s.write_manifest([{"id": "s01", "title": "t", "instruction": "i", "suggested_queries": ["q"]}])
    check("manifest round-trips", s.read_manifest()[0]["id"] == "s01")

    # --- usage tracker --------------------------------------------------------
    t = TokenTracker()
    t.record("planner", 1000, 200, 0, "gpt-4o", 1.5)
    t.record("worker-s01", 500, 100, 500, "deepseek-chat", 0.5)
    rep = t.report()
    check("usage report aggregates roles",
          "planner" in rep and "worker-s01" in rep and "TOTAL" in rep)

    # --- tool dispatcher (files only; web tools degrade to [] offline) --------
    d = build_dispatcher(s.path, auto_approve=True)
    r = d("create_file", {"filename": "reports/test.md", "content": "# hi"})
    check("create_file writes inside session", (s.path / "reports/test.md").exists())
    check("read_file returns content", "hi" in d("read_file", {"filename": "reports/test.md"}))
    try:
        _safe_path("../../etc/passwd", s.path)
        check("path traversal rejected", False)
    except ValueError:
        check("path traversal rejected", True)

    # --- wide aggregation (pure code, no LLM) ---------------------------------
    subtasks = [{"id": "s01", "title": "t1", "instruction": "i", "suggested_queries": []},
                {"id": "s02", "title": "t2", "instruction": "i", "suggested_queries": []}]
    s.write_manifest(subtasks)
    s.child_output("s01").write_text("## s01\nfinding with [src](https://a.b)\n", encoding="utf-8")
    out = wide.aggregate(s, "goal")
    text = out.read_text(encoding="utf-8")
    check("aggregation preserves citations verbatim", "[src](https://a.b)" in text)
    check("aggregation flags coverage gaps", "s02" in text and "Coverage Gaps" in text)

print(f"\nAll {ok} checks passed.")
