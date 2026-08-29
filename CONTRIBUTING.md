# Contributing

Read [AGENTS.md](AGENTS.md) first — it is the routing table and lists the
architectural invariants (scratchpad-only communication, code-only wide
aggregation, runtime-loaded rules files, session confinement, inline
citations).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_test.py        # offline sanity check
python -m compileall deep_research_agent
```

## Ground rules

- Python ≥3.10; stdlib-first. New dependencies need a justification in the PR.
- Behavior changes to agents belong in `rules/*.md` (runtime-loaded contracts)
  when possible — prompt-level changes should not require code changes.
- Every public module docstring states which upstream idea it implements and
  what it does differently.
- Keep runs reproducible: anything that changes session layout must keep old
  sessions readable or provide a migration note.
- PRs that weaken safety gates (command confirmation, blocklist, session
  confinement) will be rejected unless they add a scoped opt-in.

## Suggested first issues

- More search backends (SearXNG, Brave, Exa) behind `tools/web.py`.
- Playwright fallback in `fetch_web_content` for JS-heavy pages.
- Resume command for interrupted deep sessions (re-read scratchpad, continue).
- Cost-aware worker routing in wide mode (cheap model first pass, escalate on
  thin outputs).
- A `--reader-mode internal|external` flag that injects the corresponding
  writing contract from `rules/source_tiers.md`.
