"""Orchestrator: the planner<->executor control loop for deep mode.

Control flow (inherited from grapeot/deep_research_agent):

    user query
       |
       v
    Planner round --- update scratchpad.md (plan / next steps)
       |  INVOKE_EXECUTOR
       v
    Executor round --- search/fetch/analyze, write files, update scratchpad
       |  TASK_COMPLETED
       v
    Planner reviews scratchpad status ... loop
       |  TASK_COMPLETE
       v
    user feedback gate -> final wrap-up

All state lives in files (scratchpad + reports), so any round can be resumed
after a crash by simply re-reading the session directory.
"""
from __future__ import annotations

import logging
from pathlib import Path

from .agents.executor import ExecutorAgent
from .agents.planner import PlannerAgent
from .config import Config
from .scratchpad import Scratchpad
from .session import Session
from .usage import TokenTracker

logger = logging.getLogger(__name__)

MAX_ROUNDS = 30


class Orchestrator:
    def __init__(self, cfg: Config, rules_dir: Path | None = None):
        self.cfg = cfg
        self.tracker = TokenTracker()
        self.rules_dir = Path(rules_dir) if rules_dir else Path(__file__).parent.parent / "rules"
        if not self.rules_dir.exists():  # installed package fallback
            self.rules_dir = Path(__file__).parent / "rules"

    def run(self, query: str, session: Session) -> Path:
        scratchpad = Scratchpad(session.scratchpad_path)
        scratchpad.append("Background and Motivation", f"Initial research query: {query}",
                          "Planner")

        planner = PlannerAgent(self.cfg.planner, self.rules_dir / "planner.md", self.tracker)
        executor = ExecutorAgent(self.cfg.executor, self.rules_dir / "executor.md",
                                 self.tracker, session.path, self.cfg.auto_approve)

        current_query = query
        for round_no in range(1, MAX_ROUNDS + 1):
            files = self._workspace_files(session)
            marker = planner.plan(current_query, scratchpad.read(), files)
            logger.info("[round %d] planner -> %s", round_no, marker)

            if marker == "TASK_COMPLETE":
                feedback = input("\nTask complete. Additional feedback, Enter to accept, "
                                 "'q' to quit: ").strip()
                if feedback.lower() == "q" or not feedback:
                    scratchpad.append("Current Status / Progress Tracking",
                                      "Task completed and confirmed by user", "Planner")
                    break
                current_query = feedback
                continue
            if marker.startswith("ERROR"):
                scratchpad.append("Executor's Feedback or Assistance Requests",
                                  marker, "Planner")
                break

            files = self._workspace_files(session)
            status = executor.execute(scratchpad.read(), files)
            logger.info("[round %d] executor -> %s", round_no, status)
            if status.startswith("MAX_STEPS"):
                scratchpad.append("Executor's Feedback or Assistance Requests",
                                  status, "Executor")

        print("\n" + "=" * 62)
        print(self.tracker.report())
        print("=" * 62)
        print(session.summary())
        return session.path

    @staticmethod
    def _workspace_files(session: Session) -> dict[str, str]:
        files: dict[str, str] = {}
        for p in sorted(session.path.rglob("*.md")):
            rel = p.relative_to(session.path)
            if rel.parts[0] in ("raw", "logs"):
                continue
            files[str(rel)] = p.read_text(encoding="utf-8")[:30000]
        return files
