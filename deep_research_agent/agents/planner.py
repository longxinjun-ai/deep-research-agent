"""Planner agent: decomposition, success criteria, next-step assignment.

Design (from grapeot/deep_research_agent, hardened):
- Reads its behavior contract from rules/planner.md at startup.
- Every round it re-reads the scratchpad (all context lives in files).
- Its ONLY tool is create_file; it never talks to the executor through
  chat output — the scratchpad is the single communication channel.
- Emits control markers: INVOKE_EXECUTOR (after updating scratchpad.md)
  and TASK_COMPLETE.
- A guard rejects INVOKE_EXECUTOR when scratchpad.md was not touched this
  round, which prevents "phone it in" loops with stale instructions.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from ..config import ModelSpec
from ..llm import chat
from ..usage import TokenTracker

logger = logging.getLogger(__name__)

CREATE_FILE_TOOL = [{
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Create or update a file with the given content",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["filename", "content"],
        },
    },
}]

MAX_STEPS = 40  # planner tool-call steps per round


class PlannerAgent:
    def __init__(self, spec: ModelSpec, rules_path: Path, tracker: TokenTracker):
        self.spec = spec
        self.tracker = tracker
        self.rules = Path(rules_path).read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        self.system_prompt = (f"{self.rules}\n\nToday's date is {today}. Factor this "
                              "into planning and progress analysis.")

    def plan(self, user_input: str, scratchpad_content: str,
             files: dict[str, str]) -> str:
        """One planning round. Returns 'INVOKE_EXECUTOR' | 'TASK_COMPLETE' | 'ERROR: ...'"""
        files_text = "\n".join(f"--- {name} ---\n{content}\n"
                               for name, content in files.items())
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content":
                f"User request:\n{user_input}\n\nCurrent workspace files:\n{files_text}"},
        ]
        touched_scratchpad = False

        for _ in range(MAX_STEPS):
            content, tool_calls, _ = chat(self.spec, messages, CREATE_FILE_TOOL,
                                          role="planner", tracker=self.tracker)

            if content and content.strip() in ("TASK_COMPLETE", "INVOKE_EXECUTOR"):
                marker = content.strip()
                if marker == "INVOKE_EXECUTOR" and not touched_scratchpad:
                    messages.append({"role": "user", "content":
                        "Warning: you invoked the executor without updating scratchpad.md "
                        "this round. The executor would receive stale instructions. Update "
                        "scratchpad.md (especially 'Next Steps and Action Items') first."})
                    continue
                return marker

            if not tool_calls:
                messages.append({"role": "user", "content":
                    "Warning: respond only via the create_file tool, or output exactly "
                    "INVOKE_EXECUTOR / TASK_COMPLETE."})
                continue

            for tc in tool_calls:
                args = tc["arguments"]
                filename, body = args.get("filename", ""), args.get("content", "")
                try:
                    from ..tools import files as file_tools
                    result = file_tools.create_file(filename, body)
                except Exception as e:  # noqa: BLE001
                    result = f"[error creating file: {e}]"
                if "scratchpad" in filename:
                    touched_scratchpad = True
                messages.append({"role": "assistant", "content": None,
                                 "tool_calls": [{"id": tc["id"], "type": "function",
                                                 "function": {"name": tc["name"],
                                                              "arguments": json.dumps(args)}}]})
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

        return "ERROR: planner exceeded max steps without a control marker"
