# Example: Wide research over 53 course blogs

Reproduces the flagship use case of
[grapeot/codex_wide_research](https://github.com/grapeot/codex_wide_research):
summarize 53 student blog posts, build a label taxonomy, label every article,
count labels, and assemble one cited report — the task where serial "deep
research" quietly dropped most students and only wide research covered all 53.

```bash
python -m deep_research_agent \
  "Read https://example.edu/index (53 student blogs about software engineering
   questions). (1) Extract every name+URL. (2) Summarize each student's
   questions. (3) Design a label taxonomy. (4) Assign 5 labels per article.
   (5) Count the most frequent labels. (6) Deliver one cited Chinese report." \
  --mode wide --workers 6
```

Files in this directory are illustrative samples of the pipeline artifacts:

- `manifest.example.json` — the recon-phase subtask manifest
- `child_outputs/s01.md` — one worker report (structure, citations, documented gap)
- `final_report.example.md` — the programmatic merge (verbatim child content)
- `polished_report.example.md` — the chapter-by-chapter synthesis

The pipeline order matters: recon → fan-out → **code merge** → staged polish.
See `rules/wide_research_playbook.md` for the protocol.
