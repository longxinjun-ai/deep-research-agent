# Personal Context: Escaping the Consensus Ceiling

> Credit: the framework and arguments come from Yan Wang (鸭哥)'s
> [Why AI Only Gives You Correct Nonsense](https://yage.ai/context-infrastructure-en.html)
> and the [context-infrastructure](https://github.com/grapeot/context-infrastructure)
> reference implementation. This page is the operator's manual for using
> that idea alongside this repo.

## The diagnosis

LLM output regresses to consensus: next-token prediction prefers what most
people would say, and RLHF further rewards balanced non-commitment. The
result is "correct nonsense" — accurate, generic, useless to an expert.
Deep Research products are mostly **wide research**: they close *information
asymmetry* (knowing more facts) but not *cognitive asymmetry* (knowing how
to interpret them). Swapping in smarter models or better prompts just buys
"a different source of consensus", because both optimize the same dimension:
model intelligence.

The escape is injecting your own accumulated judgment — and that must be
collected systematically, because experts cannot articulate most of what
makes them expert.

## The three-tier memory system

1. **Accumulate at scale** — collect *behavioral data*, not introspection:
   meeting notes, chat exports, every AI conversation and correction, kept
   as local files in one place.
2. **Layered distillation** (criterion: *stability* — judgments that recur
   across situations and time are your actual cognitive structure):
   - **L1 Observer** (daily): scan file changes, extract observations.
   - **L2 Reflector** (weekly): merge duplicates, prune stale entries, find
     cross-project patterns.
   - **L3 Axioms** (occasional): distill stable patterns into decision
     principles you can cite.
   Unlike fact-collectors (Mem0-style), this reaches judgment principles:
     *facts tell an AI who you are; judgment principles tell it how you think.*
3. **On-demand loading** — never dump everything into context. Load like a
   memory hierarchy: L1 cache = the routing file, L2 = skill index, L3 =
   individual skill/axiom files, each loaded only when a task needs it.

## How this repo consumes personal context

- `rules/planner.md` §stopping-conditions asks *why the user asked this* —
  answer it with your own judgment context, not the model's guess.
- The **success criteria** and **claim ledger** sections of the scratchpad
  are where your taste becomes executable: what counts as "good", which
  claims are load-bearing for *you*, which reader mode applies.
- Keep your own axioms next to this repo (the upstream reference keeps them
  under `rules/axioms/`); reference them in success criteria when they
  should shape the report.

## Feedback loop

Knowledge products (research reports, briefings) both consume and regenerate
context: every run's claim ledgers, source indexes, and post-mortems are
raw material for your L1 observer. Treat the `runs/` directory as part of
your behavioral data. Deliberately injecting your cultivated bias is the
point — cultivated bias is the source of depth.
