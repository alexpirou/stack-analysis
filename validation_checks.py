"""One-off checks run during the study (originally run inline).

Usage:  python validation_checks.py [additivity|live|tags|capacity|ar1|all]
Needs SE_API_KEY in the environment for the API checks.
"""
import datetime as dt
import sys

import numpy as np
import pandas as pd
import requests
import statsmodels.formula.api as smf

import se_api as A


def additivity():
    """12 monthly counts for 2019 must sum to the single full-year count.
    A mismatch would mean month windows overlap or leave gaps."""
    months = {m: A.month_count("stackoverflow", 2019, m)[0] for m in range(1, 13)}
    year, q = A.count("stackoverflow", A.epoch(2019, 1), A.epoch(2020, 1) - 1)
    total = sum(months.values())
    print("monthly:", months)
    print(f"sum of months {total:,}  single call {year:,}  diff {total - year}  quota {q}")


def live():
    """Implied monthly rate from the time span of the 100 newest questions.
    Independent check that recent panel values aren't a query artifact.
    (Don't use /info questions_per_minute: it's a lifetime average.)"""
    for site in ["stackoverflow", "math", "english"]:
        p = dict(site=site, sort="creation", order="desc", pagesize=100)
        if A.KEY:
            p["key"] = A.KEY
        items = requests.get(A.ENDPOINT, params=p, timeout=30).json()["items"]
        ds = sorted(dt.datetime.fromtimestamp(i["creation_date"], dt.timezone.utc)
                    for i in items)
        hours = (ds[-1] - ds[0]).total_seconds() / 3600
        print(f"{site:14s} {ds[0]:%Y-%m-%d %H:%M} -> {ds[-1]:%Y-%m-%d %H:%M} "
              f"= {hours:7.2f}h -> ~{100 / hours * 24 * 30.4:,.0f} q/month")


def tags():
    """Feasibility of a tag-level design (old vs post-cutoff technologies)."""
    def tagcount(tag, y, m):
        frm, to = A.month_bounds(y, m)
        p = dict(site="stackoverflow", tagged=tag, fromdate=frm, todate=to,
                 sort="creation", order="desc", filter=A.FILTER)
        if A.KEY:
            p["key"] = A.KEY
        return requests.get(A.ENDPOINT, params=p, timeout=30).json().get("total")

    periods = [(2019, 6), (2022, 6), (2024, 6), (2026, 6)]
    print(f"{'tag':12s}" + "".join(f"{y}-{m:02d}".rjust(10) for y, m in periods))
    for t in ["pandas", "numpy", "django", "reactjs",
              "langchain", "polars", "bun", "ollama"]:
        print(f"{t:12s}" + "".join(f"{tagcount(t, y, m):>10,}" for y, m in periods))


def capacity():
    """API requests needed to enumerate every question (pagesize=100)."""
    t = pd.read_csv("se_panel.csv").groupby("site").questions.sum().sort_values()
    for s, v in t.items():
        pages = v / 100
        verdict = "feasible in a day" if pages < 9000 else "NOT feasible via API"
        print(f"{s:15s} {v:>12,.0f} questions -> {pages:>9,.0f} requests  {verdict}")


def ar1():
    """Residual autocorrelation: why the nominal 2-SD rule is too loose."""
    from analyze import ORDER, REAL_PRE_END, prep
    df = prep()
    for s in ORDER:
        g = df[df.site == s].sort_values("mo")
        r = smf.ols("logq ~ t + C(month)", data=g[g.mo <= REAL_PRE_END]).fit().resid.to_numpy()
        rho = np.corrcoef(r[:-1], r[1:])[0, 1]
        infl = (1 + rho) / (1 - rho)
        print(f"{s:15s} rho={rho:.3f}  SE inflation {np.sqrt(infl):.1f}x  "
              f"nominal 2SD = {2 / np.sqrt(infl):.2f} true SD")


CHECKS = dict(additivity=additivity, live=live, tags=tags, capacity=capacity, ar1=ar1)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in CHECKS.items():
        if which in (name, "all"):
            print(f"\n=== {name} ===")
            fn()
