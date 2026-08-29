"""Structured scratchpad: the shared, on-disk memory between agents.

The scratchpad is the single source of truth for a research session. The
planner writes plans and next steps into it; the executor writes findings,
status and blockers back into it. Both agents re-read it every round, which
keeps every decision traceable and survives context truncation — the same
"document-centric memory" idea as grapeot/deep_research_agent, extended with
per-section history and a claim ledger for incentive-aware verification.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

SECTIONS = [
    "Background and Motivation",
    "Key Challenges and Analysis",
    "Verifiable Success Criteria",
    "High-level Task Breakdown",
    "Claim Ledger",
    "Current Status / Progress Tracking",
    "Next Steps and Action Items",
    "Executor's Feedback or Assistance Requests",
]

TEMPLATE = "\n".join(
    f"### {name}\n(placeholder)\n" if i else f"### {name}\n(placeholder)\n"
    for i, name in enumerate(SECTIONS)
)


class Scratchpad:
    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            self.path.write_text(TEMPLATE, encoding="utf-8")
        self.content = self.path.read_text(encoding="utf-8")

    # ------------------------------------------------------------- read/write
    def read(self) -> str:
        self.content = self.path.read_text(encoding="utf-8")
        return self.content

    def get_section(self, name: str) -> str:
        m = re.search(rf"^### {re.escape(name)}\s*\n(.*?)(?=^### |\Z)",
                      self.read(), re.S | re.M)
        return m.group(1).strip() if m else ""

    def append(self, section: str, text: str, role: str) -> None:
        """Append a timestamped, role-attributed entry to a section."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n[{role} @ {now}]\n{text.strip()}\n"
        content = self.read()
        pattern = rf"(^### {re.escape(section)}\s*\n)"
        if re.search(pattern, content, re.M):
            content = re.sub(pattern, rf"\1{entry}", content, count=1, flags=re.M)
        else:  # section missing -> add at the end
            content += f"\n### {section}\n{entry}"
        self.path.write_text(content, encoding="utf-8")
        self.content = content

    def replace_section(self, section: str, text: str, role: str) -> None:
        """Replace a section body entirely (used for status tables)."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        body = f"\n[{role} @ {now}]\n{text.strip()}\n"
        content = self.read()
        pattern = rf"(^### {re.escape(section)}\s*\n).*?(?=^### |\Z)"
        if re.search(pattern, content, re.S | re.M):
            content = re.sub(pattern, rf"\1{body}", content, count=1, flags=re.S | re.M)
        else:
            content += f"\n### {section}\n{body}"
        self.path.write_text(content, encoding="utf-8")
        self.content = content

    # ------------------------------------------------------------- claim ledger
    def add_claims(self, rows: list[tuple[str, str, str]]) -> None:
        """Append rows to the Claim Ledger as a markdown table.

        rows: (claim, source_tier, verification_channel)
        """
        existing = self.get_section("Claim Ledger")
        first_line = existing.splitlines()[0] if existing else ""
        lines = []
        if "| Claim |" not in first_line:
            lines.append("| Claim | Source tier | Verification channel | Status |")
            lines.append("|---|---|---|---|")
        for claim, tier, channel in rows:
            claim = claim.replace("|", "\\|")
            lines.append(f"| {claim} | {tier} | {channel} | pending |")
        self.append("Claim Ledger", "\n".join(lines), "Planner")
