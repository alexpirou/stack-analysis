# Code: LLM shock across Stack Exchange sites

Requires Python 3.11+ with `pandas numpy statsmodels matplotlib requests`
(`pip install pandas numpy statsmodels matplotlib requests`).

Get a free API key at https://stackapps.com/apps/oauth/register and set it
as an environment variable. Don't put it in any file.

```bash
export SE_API_KEY=your_key_here        # PowerShell: $env:SE_API_KEY="your_key_here"
```

## Run order

| step | command | output |
|---|---|---|
| 1. pull counts (768 requests, ~4 min, resumable) | `python pull.py` | `raw_questions.csv` |
| 2. build tidy panel | `python build_panel.py` | `se_panel.csv` |
| 3. real + placebo analysis, figure | `python analyze.py` | `summary.csv`, `summary_with_placebo.csv`, `shortfall.png` |
| 4. robustness (onset rules, excess over placebo) | `python robustness.py` | `robustness.csv` |
| 5. validation checks | `python validation_checks.py all` | printed |

## Files

- `se_api.py` - API helper: UTC month bounds, backoff and quota handling, custom
  `filter` that returns only `total`/`quota_remaining`/`backoff`
- `pull.py` - 6 sites x 128 months, appends each result to disk so a crash or
  quota stop can resume
- `build_panel.py` - uses SEDE CSV exports (`<slug>_questions.csv`,
  `<slug>_answers.csv`) if present, otherwise the API pull; reports gaps and
  never fills them in
- `analyze.py` - per-site `log(q) ~ t + C(month)` on the pre-period, shortfall,
  onset, last-6-month magnitude, R2/SD/Durbin-Watson, placebo, power check
- `robustness.py` - onset under 2/3 SD x 3/6 month rules; real shortfall minus
  placebo shortfall
- `validation_checks.py` - additivity test, live-stream check, tag feasibility,
  enumeration cost, residual autocorrelation

Numbers change over time because these are live databases. The results in
`SUMMARY.md` come from a pull on 2026-09-09 (UTC).
Data: Stack Exchange, CC BY-SA.
