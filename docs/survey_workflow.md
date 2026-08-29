# Deep Research Survey SOP

The standard operating procedure the agents follow for a serious
third-party investigation. Human researchers can follow it directly too.

> Credit: condensed from grapeot/context-infrastructure
> `rules/skills/workflow_deep_research_survey.md`, cross-checked with
> Anthropic's multi-agent research lessons.

## Phase 0 — Frame the question

Before searching, decide:
- Why does the requester care? What decision does this inform?
- Reader mode: internal memo (shared context) or external argument
  (self-contained)? See `rules/source_tiers.md`.
- Effort class: fact-finding (1 worker, ≤10 tool calls) / comparison
  (2–4 dimensions) / open landscape (wide mode fan-out).

## Phase 1 — Scan & claim extraction

1. 2–3 searches covering: official story (Tier 1), market narrative
   (Tier 2), criticism & known issues (Tier 3–4).
2. Summarize 3–5 dimensions that deserve deep dives.
3. Extract claims from Tier 1–2 sources into the **Claim Ledger** with a
   verification channel for each (which Tier 3–4 source type could
   confirm/refute it?). Write verification tasks into Phase 2 prompts.

## Phase 1.5 — Prior work positioning (academic topics only)

If the object is a paper: read its Related Work skeptically — authors
position themselves favorably. Extract the cited lineage and decide whether
the contribution is a *new problem*, a *new measurement of a felt problem*,
or an *engineering improvement*; that classification decides whether your
report is a survey, a deep-dive, or a comparison. Skip for products/companies.

## Phase 2 — Parallel deep dives with overlapping coverage

One sub-agent per dimension, with deliberate overlap between neighbors so
disagreement exposes blind spots. Each brief contains: objective, output
format, tool/source guidance, boundaries — vague briefs duplicate work.
Verify ledger claims here, citing Tier 3–4 evidence; `contested` is a valid
outcome.

## Phase 3 — Cross-validation

Compare reports on overlapping ground. Discrepancies are findings, not
noise: chase them to primary sources. Update every ledger row to
verified / refuted / contested with evidence links.

## Phase 4 — Single deliverable

One main report (Executive Summary → Key Facts/Timeline → Thematic
Analysis → Risks & Next Steps), plus reusable artifacts (claim ledger,
source index) in the session directory. Every load-bearing claim carries an
inline citation; every contested claim is labeled. Write chapter by chapter.

## Phase 5 — Two-step QA

1. Was the report assembled via staged edits (not single-pass)?
2. Is the depth real? Thin sections trace to either thin children (rerun
   those) or compressive synthesis (expand the edit).

## Anti-patterns

- Trusting vendor benchmarks as evidence (they are Tier 1 claims).
- Summarizing from snippets without fetching full sources.
- Dropping "inconvenient" contested claims for narrative smoothness.
- Letting one long single-pass write mangle 50+ collected items — that is
  the exact failure wide mode exists to prevent.
