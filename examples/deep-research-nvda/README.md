# Example: Deep-mode NVDA stock analysis (abridged sample run)

Command:

```bash
python -m deep_research_agent \
  "Perform a detailed analysis on the recent trend of NVDA stock. How did the
   price change? What might have caused it? How about market sentiment?"
```

This directory shows the *shape* of a deep-mode session (illustrative
content, not a real run). Files produced under `runs/<stamp>-nvda-stock/`:

| File | Author | Purpose |
|---|---|---|
| `scratchpad.md` | planner + executor | shared memory: criteria, plan, claim ledger, status |
| `reports/search_nvda_price.md` | executor | cited search results (≥10 sources) |
| `reports/search_nvda_sentiment.md` | executor | sentiment coverage |
| `nvda_analysis.py` | executor | data fetch + chart script (runs after `[y/N]` gate) |
| `nvda_trend.png` | script | price trend chart |
| `nvda_analysis_report.md` | planner | final synthesis |

See `scratchpad.example.md` in this directory for the document structure.
