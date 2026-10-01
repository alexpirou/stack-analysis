"""
Generate a synthetic se_panel.csv that mimics the real LLM-shock dataset.

Each site gets:
- A realistic baseline level of questions per month
- A slow upward or flat pre-trend (2016-01 to 2022-10)
- Monthly seasonality noise
- A sharp post-ChatGPT decline (2022-11 onward) for technical sites,
  no meaningful decline for non-technical sites
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# (site, category, baseline_monthly_q, monthly_trend_pct, post_shock_pct)
# post_shock_pct: approximate mean % shortfall after 2022-11
SITES = [
    ("stackoverflow",  "technical",     20_000, +0.25, -0.45),
    ("math",           "technical",        800, +0.20, -0.30),
    ("english",        "non-technical",    900, +0.10, -0.05),
    ("cooking",        "non-technical",    500, +0.05, -0.02),
    ("travel",         "non-technical",    400, -0.10, +0.04),
    ("worldbuilding",  "non-technical",    300, +0.08, +0.01),
]

months = pd.date_range("2016-01-01", "2026-08-01", freq="MS")

rows = []
for site, cat, base, trend_pct, shock_pct in SITES:
    for i, mo in enumerate(months):
        # linear trend
        level = base * (1 + trend_pct / 100) ** i
        # mild seasonal cycle
        seasonal = 1 + 0.07 * np.cos(2 * np.pi * (mo.month - 3) / 12)
        # post-shock ramp (gradual settling)
        post_months = max(0, (mo.year - 2022) * 12 + mo.month - 11)
        shock = 1.0
        if post_months > 0:
            shock = 1 + shock_pct * min(post_months / 6, 1.0)
        # noise
        noise = rng.normal(1, 0.03)
        q = max(1, int(level * seasonal * shock * noise))
        rows.append({
            "site": site,
            "category": cat,
            "mo": mo,
            "questions": q,
            "askers": pd.NA,
            "accepted": pd.NA,
            "unanswered": pd.NA,
            "answers": pd.NA,
            "answerers": pd.NA,
        })

panel = pd.DataFrame(rows)
panel.to_csv("se_panel.csv", index=False)
print(f"Wrote se_panel.csv  ({len(panel)} rows, {panel.site.nunique()} sites, "
      f"{panel.mo.min():%Y-%m}..{panel.mo.max():%Y-%m})")
