# Design Notes

This repo is a synthesis, not a fork. It distills three upstream projects by
Yan Wang (鸭哥/grapeot) plus public multi-agent research engineering, into one
provider-agnostic, runnable system.

## Upstream lineage

| Idea | Source | Where it lives here |
|---|---|---|
| Planner–Executor split; scratchpad as the only inter-agent channel; human confirmation gates; token/cost accounting | [grapeot/deep_research_agent](https://github.com/grapeot/deep_research_agent) | `orchestrator.py`, `agents/`, `scratchpad.py`, `deep_research_agent/rules/planner.md`, `deep_research_agent/rules/executor.md` |
| Wide research: divide-and-conquer fan-out, isolated worker contexts, **merge with code not LLM**, staged chapter-by-chapter synthesis, two-step QA, idempotent runs, cache-first | [grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research) (inspired by [Manus Wide Research](https://manus.im/blog/introducing-wide-research)) | `wide.py`, `deep_research_agent/rules/wide_research_playbook.md`, `scripts/run_wide_children.sh` |
| Incentive-aware source tiers, claim ledger verification, reader modes (internal memo vs external argument), document-centric rules routing | [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure) | `deep_research_agent/rules/source_tiers.md`, scratchpad *Claim Ledger* section, `AGENTS.md` |
| Effort scaling to query complexity, parallel tool calls, subagent brief hygiene | [Anthropic, "How we built our multi-agent research system"](https://www.anthropic.com/engineering/built-multi-agent-research-system) | `deep_research_agent/rules/planner.md` §Workflow, `wide.py` worker prompts |
| Perspective-guided inquiry (ask what a source would ask) | Stanford [STORM](https://arxiv.org/abs/2402.14207) / Co-STORM | suggested per-dimension queries in the manifest |

## What is deliberately different from upstream

1. **Provider-agnostic LLM layer.** The original pinned an OpenAI planner and
   a Claude executor. `llm.py` speaks OpenAI-compatible *and* Anthropic
   protocols behind one interface with normalized tool-calls and usage, so
   planner/executor/researcher roles can each route to any vendor (OpenAI,
   DeepSeek, GLM, OpenRouter, Ollama...) via env vars.
2. **Wide research without a CLI dependency.** `codex_wide_research` drives
   the Codex CLI as its worker runtime. `wide.py` implements the same
   protocol as plain Python workers with bounded concurrency, surgical
   retries, and programmatic aggregation — any API key works.
3. **Claim ledger as a first-class artifact.** The scratchpad ships a Claim
   Ledger section with tier-tagged verification channels, making the
   incentive-aware methodology executable rather than advisory.
4. **Session isolation & resumability.** Every run gets
   `runs/<stamp>-<slug>/` with `child_outputs/ raw/ logs/` and manifest, so
   crashed runs resume without redoing cached children.
5. **Session-scoped file sandbox.** Executor file writes are confined to the
   session directory (path traversal rejected); commands pass a blocklist and
   an interactive gate unless explicitly auto-approved.

## Architecture

```
                          ┌────────────────────────┐
        user query ──────►│      orchestrator      │
                          └───────┬────────┬───────┘
                    deep mode     │        │     wide mode
              ┌───────────────────┘        └───────────────────┐
              ▼                                                ▼
      ┌───────────────   scratchpad.md   ───────────┐   plan_manifest (recon)
      │   sections: background · challenges ·       │          │
      │   success criteria · breakdown · claims ·   │          ▼
      │   status · next steps · feedback            │   subtask manifest.json
      └───────▲───────────────────────▲─────────────┘          │
              │ read/write            │ read/write             ▼
      ┌───────┴───────┐       ┌───────┴───────┐    fan_out (ThreadPool, N workers,
      │    PLANNER    │       │   EXECUTOR    │    isolated contexts, ≤10 iters,
      │ decompose,    │──────►│ search, fetch,│    inline citations, failure notes)
      │ criteria,     │ INVOKE│ analyze, write│           │
      │ next steps    │_EXEC. │ files, status │           ▼
      └───────────────┘       └───────────────┘   aggregate (pure code merge,
              ▲                                       verbatim citations)
              │ TASK_COMPLETE            ▲                │
              │                          │                ▼
        user feedback gate         report files     synthesize (chapter-by-
                                               chapter polish, two-step QA)
```

Deep mode is a loop: the planner plans into the scratchpad and hands off;
the executor researches, writes files, and updates status; the planner
reviews and iterates; a feedback gate keeps the user in control. Wide mode
is a pipeline: recon → manifest → parallel workers → code merge → staged
synthesis.

## Design principles

- **Documents are the memory.** Context windows are the scarce resource;
  files are the durable one. Anything important is written down, attributed,
  and re-readable (`docs are long-term memory` axiom).
- **Merge with code, write with care.** Aggregation is deterministic; only
  synthesis touches an LLM, and only section by section.
- **User agency.** Destructive actions pause for confirmation; the final
  report is a file you can audit, with inline citations throughout.
- **Escape the consensus ceiling.** Model intelligence is depreciating and
  universal; your accumulated judgment context is not. Feed the agent your
  criteria (success criteria, claim ledgers, reader modes) and it stops
  producing correct nonsense. See `docs/memory.md` for the long game.
