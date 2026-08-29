"""Executor agent: tool-using field researcher.

Design (from grapeot/deep_research_agent, hardened):
- Reads its behavior contract from rules/executor.md at startup.
- Agentic tool loop: search -> fetch -> create_file -> (confirm-gated)
  commands, up to MAX_STEPS actions per invocation.
- MUST write findings to files (search reports with URLs) and update the
  scratchpad's status/feedback sections before returning — undocumented
  effort is wasted effort.
- Incentive-aware source tiers and anti-hallucination rules (never invent
  URLs; cite everything) are baked into rules/executor.md.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from ..config import ModelSpec
from ..llm import chat
from ..tools import TOOL_DEFINITIONS, build_dispatcher
from ..usage import TokenTracker

logger = logging.getLogger(__name__)

MAX_STEPS = 60  # tool calls per executor invocation


class ExecutorAgent:
    def __init__(self, spec: ModelSpec, rules_path: Path, tracker: TokenTracker,
                 session_dir: Path, auto_approve: bool = False):
        self.spec = spec
        self.tracker = tracker
        self.rules = Path(rules_path).read_text(encoding="utf-8")
        self.dispatch = build_dispatcher(session_dir, auto_approve)
        self.session_dir = session_dir

    def execute(self, scratchpad_content: str, files: dict[str, str]) -> str:
        """One execution round. Returns a short status string for the logs."""
        today = datetime.now().strftime("%Y-%m-%d")
        system = (f"{self.rules}\n\nToday's date is {today}.")
        files_text = "\n".join(f"--- {name} ---\n{content}\n"
                               for name, content in files.items())
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content":
                f"Scratchpad (working doc):\n{scratchpad_content}\n\n"
                f"Other workspace files:\n{files_text}\n\n"
                "Read the 'Next Steps and Action Items' section and carry out the "
                "immediate task now. Write results to files and update the scratchpad "
                "status/feedback sections. Output TASK_COMPLETED when done."},
        ]

        for step in range(MAX_STEPS):
            content, tool_calls, _ = chat(self.spec, messages, TOOL_DEFINITIONS,
                                          role="executor", tracker=self.tracker)
            if content and "TASK_COMPLETED" in content:
                return "TASK_COMPLETED"

            if not tool_calls:
                messages.append({"role": "user", "content":
                    "Continue using tools to finish the task, or output TASK_COMPLETED. "
                    "Remember: findings must be saved to files, not chat."})
                continue

            for tc in tool_calls:
                name, args = tc["name"], tc["arguments"]
                logger.info("[executor step %d] %s %s", step + 1, name,
                            json.dumps(args, ensure_ascii=False)[:120])
                try:
                    result = self.dispatch(name, args)
                except Exception as e:  # noqa: BLE001
                    result = f"[error: {e}]"
                messages.append({"role": "assistant", "content": None,
                                 "tool_calls": [{"id": tc["id"], "type": "function",
                                                 "function": {"name": name,
                                                              "arguments": json.dumps(args, ensure_ascii=False)}}]})
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": str(result)[:15000]})

        return ("MAX_STEPS_REACHED: executor hit the tool-call ceiling; "
                "check scratchpad feedback for state")
