# Source Tiers: Incentive-Aware Verification

> Methodology credit: distilled from grapeot/context-infrastructure
> `rules/skills/workflow_deep_research_survey.md`.

Information value depends on the **incentive structure of its source**. Vendor
narratives are useful but cannot verify themselves. Every load-bearing claim
must be traced to evidence independent of the party that benefits from the
claim.

## Tier Table

| Tier | Type | Signal | How to use |
|------|------|--------|------------|
| 1 | Vendor docs, official blogs, case studies | How the product wants to be seen | Extract claims; never verification evidence |
| 2 | Press coverage, sponsored reviews | Market narrative, still incentive-skewed | Understand positioning; not independent evidence |
| 3 | Independent dev blogs, HN/Reddit, Stack Overflow | Stronger signal, biased sampling | Verification signal; mind community bias |
| 4 | GitHub issues, migration stories, production post-mortems, commit history | Behavioral evidence — migrating costs far more than posting praise | Highest credibility; verify claims, mark boundaries |

Evidence credibility, ascending: attitude expression ("works great") < usage
descriptions < comparative decision records < migration stories < production
post-mortems < code/commit-level evidence. Collect the second half.

## Claim Ledger

For research over products, tools, papers, or any contested claims, maintain
a claim ledger in the scratchpad:

```markdown
| Claim | Source (tier) | Verification channel | Status |
|-------|---------------|----------------------|--------|
| "zero-config, works out of the box" | Tier 1 docs | GitHub issues search "setup pain"; Reddit migration threads | pending |
| "2x faster than X" | Tier 1 blog | Independent benchmark repo; production post-mortem | pending |
```

Rules:
- One row per load-bearing claim; trivia can stay untracked.
- A claim moves to `verified` / `refuted` / `contested` **only** on Tier 3–4
  evidence. Tier 1–2 sources can only open or restate rows.
- `contested` (conflicting evidence) is a legitimate, reportable outcome —
  surface it in the final report rather than picking a side silently.

## Reader Modes

Choose a writing contract before drafting (by reader context, not channel):

- **Mode A — Internal memo** (reader shares your long-term context): skip
  shared common knowledge; expand what changes conclusions, likely objections,
  conflicts with prior beliefs. Lead with conclusion, evidence, open
  questions, recommended actions.
- **Mode B — External argument** (unknown reader): answer *why this matters*
  explicitly; put the most useful judgment in the first paragraphs; write
  definitions, comparison frames, and caveats on the page, not in the
  reader's head.

Three questions to pick: (1) does the reader share thick context? (2) is the
goal faster decisions or understanding-and-persuasion? (3) does the report
stand alone without private background? Shared context / fast judgment → A;
self-contained / persuasion → B.

Under Mode B, also answer whether the topic's relevance to the reader is
*now*, *future*, or *probably-not-now*. If the honest answer is the third,
the thesis must say so — do not imply near-term value by stacking flashy
examples.
