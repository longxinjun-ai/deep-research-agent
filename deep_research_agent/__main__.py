"""CLI entry point.

    python -m deep_research_agent "your research query"                 # deep mode
    python -m deep_research_agent "compare 20 RSS readers" --mode wide # wide mode
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import load_config
from .orchestrator import Orchestrator
from .session import Session
from .usage import TokenTracker
from . import wide


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deep-research-agent",
        description="Document-driven deep & wide research agent system.")
    parser.add_argument("query", help="The research query or task")
    parser.add_argument("--mode", choices=["deep", "wide"], default="deep",
                        help="deep: planner<->executor loop; wide: parallel fan-out "
                             "with programmatic aggregation (default: deep)")
    parser.add_argument("--workers", type=int, default=None,
                        help="wide mode worker concurrency (default 4)")
    parser.add_argument("--auto-approve", action="store_true",
                        help="skip interactive confirmation of shell commands")
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    cfg = load_config()
    cfg.auto_approve = cfg.auto_approve or args.auto_approve
    cfg.debug = cfg.debug or args.debug
    session = Session(Path("runs"), args.query)
    print(f"session: {session.path}")

    if args.mode == "wide":
        tracker = TokenTracker()
        print("[1/4] reconnaissance: building subtask manifest ...")
        subtasks = wide.plan_manifest(args.query, cfg, tracker, session)
        for s in subtasks:
            print(f"  - {s['id']}: {s['title']}")
        print(f"[2/4] fan-out: {len(subtasks)} workers "
              f"(concurrency {args.workers or cfg.wide_workers}) ...")
        results = wide.fan_out(subtasks, cfg, tracker, session, args.workers)
        for sid, status in sorted(results.items()):
            print(f"  {status}")
        print("[3/4] programmatic aggregation ...")
        wide.aggregate(session, args.query)
        print("[4/4] section-by-section synthesis ...")
        out = wide.synthesize(session, args.query, cfg, tracker)
        print("\n" + "=" * 62)
        print(tracker.report())
        print("=" * 62)
        print(f"final deliverable: {out}")
        return 0

    orch = Orchestrator(cfg)
    path = orch.run(args.query, session)
    print(f"\nsession directory: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
