# Wide Research Playbook

> Methodology credit: adapted from grapeot/codex_wide_research
> `wide_research_prompt_en.md` (itself inspired by Manus Wide Research), made
> provider-agnostic in this repo's `wide.py`.

## Why Wide Research Exists

All LLMs degrade when output length approaches a large fraction of the
context window — the model starts skipping, paraphrasing instead of doing
the work, and quietly dropping items. Serial "deep research" hits this wall
around a few dozen items. The fix is architectural, not promptual:

**Divide and conquer.** Break the problem into independent subtasks, give
each worker an isolated context, keep every output short, and merge with
**code, not an LLM**. The merge is lossless and immune to slacking.

## Protocol

0. **Reconnaissance (never delegate).** Before any fan-out, the orchestrator
   does a discovery pass itself: clarify intent, identify the fan-out
   dimensions (topic clusters, item lists, time windows), and secure at
   least one real sample per dimension. Produce a manifest with estimated
   scale and known gaps. No samples, no fan-out.
1. **Manifest.** One JSON row per subtask: unique id, title, instruction,
   suggested queries. If a source yields fewer items than expected, record
   the gap; the orchestrator handles the missing slice directly.
2. **Fan-out.** Run workers in parallel (default concurrency 4–8; hardware
   and quota permitting). Each worker: isolated context, ≤10 search/fetch
   iterations, mandatory markdown report with inline citations, failures
   documented (never silent). Dry-run 1–2 workers before scaling.
3. **Programmatic aggregation.** A script stitches `child_outputs/*.md` into
   `final_report.md` in manifest order, preserving wording and citations
   verbatim. Coverage check flags missing/empty children before shipping.
4. **Section-by-section synthesis.** A separate editor pass rewrites the
   aggregate into the polished report **chapter by chapter** — never
   single-pass — validating citations after each section.

## Two-Step QA (before release)

1. Verify the final report was assembled via staged, chapter-by-chapter
   edits; if it was single-pass, roll back and rebuild iteratively.
2. Gauge narrative depth. Thin? Either child outputs are under-detailed
   (rerun/augment those children) or synthesis compressed them (expand the
   edit). Fix the right layer.

## Operational Rules

- **Idempotent runs**: every execution uses a fresh run directory; retries
  skip children whose validated output already exists.
- **Cache first**: persist raw search/scrape payloads under `raw/` and reuse.
- **Read fully before summarizing**: no fixed-length truncation of sources.
- **Isolate failures, retry surgically**: keep a failed-ids list; rerun only
  those units; surface them in the final report.
- **Effort scaling**: don't spawn 50 workers for a trivial question.
  Fact-finding: 1 worker. Comparison: 2–4. Open-ended landscape: more.
- **Cite inline** right after each bullet (`[source](url)`), not in a
  trailing dump — make fact-checking immediate.

## Delivery Standard

The deliverable is a polished, insight-dense document structured as
*Executive Summary → Timeline/Key Facts → Thematic Analysis → Risks & Next
Steps*, delivered as a file path plus a concise synopsis. Raw child outputs
stay archived for auditing. Keep child findings intact in the appendix —
compressing away the evidence is how wide research lies.
