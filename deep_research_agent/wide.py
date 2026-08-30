"""Wide research: manifest-driven fan-out with programmatic aggregation.

Implements the wide-research playbook (Manus-style divide-and-conquer,
codified by grapeot/codex_wide_research) in a provider-agnostic way:

1. reconnaissance  — the orchestrator (or the user) produces a manifest of
   independent subtasks (one JSON row per item).
2. fan-out         — N researcher workers run in parallel, each with an
   isolated context: search, fetch, and write a self-contained markdown
   report to child_outputs/<id>.md. Failures return explanatory notes, never
   silent gaps.
3. aggregation     — a *script* (not an LLM) stitches child reports into
   final_report.md, preserving citations verbatim.
4. synthesis       — a separate polish pass (LLM) rewrites section by
   section, never single-pass, per the two-step QA rule.

The LLM never merges content wholesale — that is the whole point: code merges
are lossless and immune to the "slacking off on long outputs" failure mode.
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .config import Config
from .llm import chat
from .session import Session
from .tools import TOOL_DEFINITIONS, build_dispatcher
from .usage import TokenTracker

logger = logging.getLogger(__name__)

CHILD_SYSTEM = """You are a wide-research worker. You own ONE subtask with an isolated context.

Rules:
- Use web_search with varied keywords, then fetch_web_content for pages that matter.
- NEVER invent URLs, quotes, or facts. Every claim needs a [source](url) link inline.
- Keep total search+fetch iterations under 10. Stop when information is sufficient.
- Rank sources by incentive: vendor docs (Tier 1) state claims; issues/migration
  stories/post-mortems (Tier 4) verify them. Prefer Tier 3-4 evidence for anything
  load-bearing.
- Write your full findings to the required output file via create_file, structured as:
  ## <subtask title>
  ### Key Findings (bullets, each with inline citation)
  ### Evidence & Quotes (verbatim excerpts with URLs)
  ### Open Questions / To-Verify
- On failure after two attempts, write a section explaining the error and suggested
  follow-up instead of leaving the file empty.
- Output exactly TASK_COMPLETED when the report file is written."""

RECON_SYSTEM = """You are a research orchestrator. Given a goal, produce a JSON manifest of
independent subtasks for parallel workers. Requirements:
- 3-12 subtasks; each must be independently executable and cover a distinct slice.
- Use the reconnaissance rule: only propose items you can anchor to concrete
  dimensions (topic clusters, lists, time windows). If the goal needs live data
  you do not have, emit one subtask per dimension with explicit search guidance.
- Output STRICT JSON: {"subtasks": [{"id": "s01", "title": "...", "instruction":
  "...", "suggested_queries": ["..."]}]}
No prose outside the JSON."""


def plan_manifest(goal: str, cfg: Config, tracker: TokenTracker,
                  session: Session) -> list[dict]:
    """Ask the planner model for a subtask manifest (reconnaissance phase)."""
    content, _, _ = chat(cfg.planner,
                         [{"role": "system", "content": RECON_SYSTEM},
                          {"role": "user", "content": f"Research goal: {goal}"}],
                         role="planner", tracker=tracker)
    try:
        m = re.search(r"\{.*\}", content, re.S)
        data = json.loads(m.group(0) if m else content)
        subtasks = data["subtasks"]
        assert isinstance(subtasks, list) and subtasks
    except Exception as e:  # noqa: BLE001
        subtasks = [{"id": "s01", "title": goal[:60],
                     "instruction": goal, "suggested_queries": [goal]}]
        logger.warning("manifest parse failed (%s); falling back to single subtask", e)
    session.write_manifest(subtasks)
    return subtasks


def _run_child(subtask: dict, cfg: Config, tracker: TokenTracker,
               session: Session) -> str:
    sub_id = subtask["id"]
    out_file = f"child_outputs/{subtask['id']}.md"
    queries = "\n".join(f"- {q}" for q in subtask.get("suggested_queries", []))
    user_prompt = (f"Subtask {sub_id}: {subtask['title']}\n\n"
                   f"Instruction: {subtask['instruction']}\n"
                   f"Suggested queries:\n{queries}\n\n"
                   f"Write your report to child output file named exactly "
                   f"`{out_file}` via create_file.")
    dispatch = build_dispatcher(session.path, auto_approve=True)
    messages = [
        {"role": "system", "content": CHILD_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    status = "failed"
    for _ in range(3):  # whole-child retry
        done = False
        for _ in range(14):
            content, tool_calls, _ = chat(cfg.researcher, messages, TOOL_DEFINITIONS,
                                          role=f"worker-{sub_id}", tracker=tracker)
            if content and "TASK_COMPLETED" in content:
                done = True
                break
            if not tool_calls:
                messages.append({"role": "user", "content":
                                 "Continue with tools, or write the report and output "
                                 "TASK_COMPLETED."})
                continue
            for tc in tool_calls:
                args = tc["arguments"]
                try:
                    result = dispatch(tc["name"], args)
                except Exception as e:  # noqa: BLE001
                    result = f"[error: {e}]"
                messages.append({"role": "assistant", "content": None,
                                 "tool_calls": [{"id": tc["id"], "type": "function",
                                                 "function": {"name": tc["name"],
                                                              "arguments": json.dumps(args, ensure_ascii=False)}}]})
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": str(result)[:15000]})
        if done and session.child_output(sub_id).exists():
            status = "ok"
            break
        logger.warning("child %s attempt failed; retrying", sub_id)
    return f"{sub_id}: {status}"


def fan_out(subtasks: list[dict], cfg: Config, tracker: TokenTracker,
            session: Session, workers: int | None = None) -> dict[str, str]:
    """Run all subtasks in parallel with isolated contexts. Idempotent:
    subtasks whose child output already exists are skipped."""
    n = min(workers or cfg.wide_workers, max(1, len(subtasks)))
    results: dict[str, str] = {}
    todo = [s for s in subtasks if not session.child_output(s["id"]).exists()]
    logger.info("fan-out: %d subtasks, %d to run, %d workers (rest cached)",
                len(subtasks), len(todo), n)
    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = {pool.submit(_run_child, s, cfg, tracker, session): s["id"]
                   for s in todo}
        for fut in as_completed(futures):
            sid = futures[fut]
            try:
                results[sid] = fut.result()
            except Exception as e:  # noqa: BLE001
                results[sid] = f"{sid}: failed ({e})"
                logger.error("child %s crashed: %s", sid, e)
    return results


def aggregate(session: Session, goal: str) -> Path:
    """Programmatically stitch child reports into final_report.md.

    Pure code, no LLM: child wording and citations are preserved verbatim —
    the lossless merge that keeps wide research honest.
    """
    children = sorted(session.path.glob("child_outputs/*.md"))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [f"# Wide Research Aggregate\n\n*Goal:* {goal}\n\n"
             f"*Generated:* {stamp} · *Sources merged:* {len(children)}\n\n---\n"]
    missing = []
    manifest = session.read_manifest()
    done_ids = {p.stem for p in children}
    for st in manifest:
        if st["id"] not in done_ids:
            missing.append(st["id"])
    for p in children:
        parts.append(p.read_text(encoding="utf-8").strip() + "\n\n---\n")
    if missing:
        parts.append(f"\n## Coverage Gaps\n\nMissing child reports: {', '.join(missing)}\n")
    out = session.path / "final_report.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    logger.info("aggregated %d child reports -> %s", len(children), out)
    return out


def synthesize(session: Session, goal: str, cfg: Config,
               tracker: TokenTracker) -> Path:
    """Section-by-section polish of the aggregate into polished_report.md.

    Follows the two-step QA rule: never a single-pass rewrite. The LLM
    receives the aggregate in slices and edits chapter by chapter with
    citations intact.
    """
    aggregate_path = session.path / "final_report.md"
    text = aggregate_path.read_text(encoding="utf-8")
    # slice the aggregate on child boundaries; polish in batches of ~6k chars
    slices = [text[i:i + 6000] for i in range(0, len(text), 6000)] or [""]
    polished: list[str] = []
    outline_prompt = ("You are the synthesis editor for a wide-research aggregate. "
                      "Rewrite the following slice into a coherent report section. "
                      "Rules: keep every citation link verbatim; keep numbers exact; "
                      "de-duplicate; add one-line synthesis where patterns repeat; "
                      "never drop a source. Output markdown only.")
    for i, s in enumerate(slices):
        content, _, _ = chat(cfg.planner,
                             [{"role": "system", "content": outline_prompt},
                              {"role": "user", "content": s}],
                             role="synthesizer", tracker=tracker)
        polished.append(content or s)
        logger.info("synthesized slice %d/%d", i + 1, len(slices))
    header = (f"# {goal}\n\n*Synthesized from {len(slices)} aggregate slices · "
              f"{datetime.now().strftime('%Y-%m-%d')}*\n\n")
    out = session.path / "polished_report.md"
    out.write_text(header + "\n\n".join(polished), encoding="utf-8")
    return out
