# AGENTS.md — Routing Table for AI Coding Tools

> Convention from grapeot/context-infrastructure: this file is the entry
> point for any AI assistant (Claude Code, Codex, Cursor, OpenCode...)
> working in this repo. Read it before touching anything.

## Project map

| You want to... | Go to |
|---|---|
| Understand the architecture & lineage | `docs/DESIGN.md` |
| Change the deep planner/executor loop | `deep_research_agent/orchestrator.py`, `agents/` |
| Change wide-research fan-out/aggregation | `deep_research_agent/wide.py` |
| Add/change a tool (search, fetch, files, commands) | `deep_research_agent/tools/`, register in `tools/__init__.py` |
| Add an LLM provider quirk | `deep_research_agent/llm.py` |
| Tune agent behavior contracts | `deep_research_agent/rules/planner.md`, `deep_research_agent/rules/executor.md` (agents read these at runtime) |
| Adjust pricing for cost tracking | `deep_research_agent/usage.py` (`PRICES`) |
| Review the methodology | `deep_research_agent/rules/*.md`, `docs/survey_workflow.md` |

## Invariants — do not break these

1. **Scratchpad is the only inter-agent channel.** Deep mode agents never
   exchange instructions through model output.
2. **Wide-mode aggregation is pure code.** `wide.aggregate` must never call
   an LLM; only `synthesize` does, chapter by chapter.
3. **Rules files are runtime-loaded.** `deep_research_agent/rules/planner.md` and
   `deep_research_agent/rules/executor.md` are read by the agents at startup — edit them like
   code, not comments.
4. **Session confinement.** Executor file writes stay inside the run
   directory; destructive commands pass the blocklist + confirmation gate.
5. **Citations inline.** Any change to report prompts must preserve the
   inline-citation requirement (`[source](url)` next to each claim).

## Conventions

- Python ≥3.10, stdlib-first; new deps require a justification in the PR.
- Every public module has a docstring explaining *which upstream idea it
  implements* and *what it does differently*.
- Verify with `python -m compileall deep_research_agent` and
  `python scripts/smoke_test.py` before committing (no network needed).

## Safety

- Do not exfiltrate keys or `runs/` content. Ever.
- Do not weaken the confirmation gates to make demos smoother.
