# Deep Research Agent

A document-driven, provider-agnostic **deep & wide research agent system** —
an open synthesis of [grapeot/deep_research_agent](https://github.com/grapeot/deep_research_agent),
[grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research),
and [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure),
plus multi-agent research engineering lessons from
[Anthropic](https://www.anthropic.com/engineering/built-multi-agent-research-system)
and [Manus Wide Research](https://manus.im/blog/introducing-wide-research).

[中文文档](README.zh-CN.md)

## Why another research agent

Most "Deep Research" products are actually **wide research**: they close
*information asymmetry* but not *cognitive asymmetry*. And every LLM degrades
once output length climbs toward the context-window ceiling — items get
dropped, work gets paraphrased away. This repo attacks both problems with
architecture rather than prompt tricks:

1. **Documents are the memory.** A structured scratchpad is the single
   communication channel between agents, so nothing lives or dies inside a
   context window.
2. **Merge with code, not an LLM.** Wide mode fans out isolated workers and
   aggregates their reports programmatically — a lossless merge immune to
   long-output slacking.
3. **Incentive-aware verification.** A claim ledger tracks every
   load-bearing claim with its source tier and verification channel; vendor
   narratives never self-verify.
4. **User agency.** Shell commands pause for confirmation; every citation is
   inline; every run is an auditable directory.

## Two research modes

**Deep mode** — planner ⇄ executor loop (from `deep_research_agent`):

```
python -m deep_research_agent "Analyze the recent trend of NVDA stock: price action, causes, market sentiment"
```

The planner decomposes the question, writes verifiable success criteria and
next steps into `runs/<id>/scratchpad.md`, and hands off. The executor
searches (≥3 keyword variants, ≥10 sources), fetches full pages, writes
cited report files, optionally runs analysis scripts (with your `[y/N]`
confirmation), and updates status. The planner reviews, re-plans, and loops
until criteria are met — then a feedback gate hands control back to you.

**Wide mode** — divide-and-conquer fan-out (from `codex_wide_research` /
Manus):

```
python -m deep_research_agent "Survey 25 open-source RSS readers: maintenance status, features, community health" --mode wide --workers 6
```

Reconnaissance builds a subtask manifest → parallel workers with isolated
contexts write cited reports → a **script** stitches them verbatim → an
editor pass polishes chapter by chapter (never single-pass). This is how you
cover 50+ items without the model quietly dropping half of them.

## Quick start

```bash
git clone https://github.com/<you>/deep-research-agent && cd deep-research-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...        # or any provider below
python -m deep_research_agent "your research question"
```

### Any provider, per role

Planner, executor, and wide workers each route independently via env vars:

```bash
# e.g. reasoning planner on OpenAI, cheap workers on DeepSeek
export DRA_PLANNER_MODEL=o3                              # + OPENAI_API_KEY
export DRA_RESEARCHER_PROVIDER=openai_compatible
export DRA_RESEARCHER_MODEL=deepseek-chat                # + DEEPSEEK_API_KEY
export DRA_RESEARCHER_BASE_URL=https://api.deepseek.com/v1

# Anthropic executor
export DRA_EXECUTOR_PROVIDER=anthropic
export DRA_EXECUTOR_MODEL=claude-sonnet-4-20250514       # + ANTHROPIC_API_KEY
```

Works with OpenAI, Anthropic, DeepSeek, GLM, OpenRouter, Ollama, vLLM —
anything speaking the OpenAI protocol.

### Optional upgrades

```bash
export DRA_SEARCH_BACKEND=tavily TAVILY_API_KEY=tvly-...  # better search (paid)
export DRA_AUTO_APPROVE=1                                  # skip [y/N] gates (trust!)
```

## Repository layout

```
deep_research_agent/        the Python package
  orchestrator.py           deep-mode planner<->executor loop
  wide.py                   wide-mode recon -> fan-out -> merge -> synthesize
  scratchpad.py             structured shared memory (incl. claim ledger)
  llm.py                    provider-agnostic chat + tool calling
  agents/                   planner & executor with rules-file contracts
  tools/                    web search/fetch (cached), sandboxed files/commands
rules/                      behavior contracts & methodology (the real IP)
  planner.md · executor.md · wide_research_playbook.md · source_tiers.md
docs/                       DESIGN.md · survey_workflow.md · memory.md
scripts/run_wide_children.sh  CLI-based batch runner (codex et al.)
examples/                   sample runs (deep + wide)
```

## Methodology worth reading even if you never run the code

- [docs/yage-methodology-map.html](docs/yage-methodology-map.html) — **visual
  knowledge map** of the whole methodology (consensus ceiling, wide research,
  three-tier memory, source tiers → this repo's implementation)
- [docs/yage-methodology.md](docs/yage-methodology.md) — the same map as
  consolidated notes (Chinese)
- [docs/DESIGN.md](docs/DESIGN.md) — architecture and upstream lineage
- [deep_research_agent/rules/source_tiers.md](deep_research_agent/rules/source_tiers.md) — incentive-aware source
  tiers, claim ledger, reader modes
- [docs/survey_workflow.md](docs/survey_workflow.md) — the 5-phase survey SOP
- [docs/memory.md](docs/memory.md) — escaping the consensus ceiling with
  personal context (three-tier memory)

## Acknowledgments

This project stands on Yan Wang (鸭哥, [@grapeot](https://github.com/grapeot))'s
open work — [deep_research_agent](https://github.com/grapeot/deep_research_agent),
[codex_wide_research](https://github.com/grapeot/codex_wide_research),
[context-infrastructure](https://github.com/grapeot/context-infrastructure),
and his writing at [yage.ai](https://yage.ai/) — plus Anthropic's multi-agent
research system post, Manus's Wide Research, and Stanford's STORM. The
upstream projects are MIT-licensed; so is this synthesis.

## License

MIT — see [LICENSE](LICENSE).
