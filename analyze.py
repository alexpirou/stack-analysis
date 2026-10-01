"""Step 3+4: per-site trend break analysis against each site's OWN pre-trend."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson

REAL_CUTOFF  = pd.Timestamp("2022-11-01")   # ChatGPT public release 2022-11-30
REAL_PRE_END = pd.Timestamp("2022-10-01")
PLA_CUTOFF   = pd.Timestamp("2019-11-01")
PLA_PRE_END  = pd.Timestamp("2019-10-01")

TECH = {"stackoverflow", "math", "physics", "cs", "unix", "datascience"}
ORDER = ["stackoverflow", "math", "physics", "cs", "unix", "datascience",
         "english", "cooking", "travel", "worldbuilding",
         "gaming", "movies", "history", "fitness", "workplace", "philosophy"]


def prep(path="se_panel.csv"):
    df = pd.read_csv(path, parse_dates=["mo"])
    df = df[df.questions.notna() & (df.questions > 0)].copy()
    df["t"] = (df.mo.dt.year - 2016) * 12 + df.mo.dt.month
    df["month"] = df.mo.dt.month
    df["logq"] = np.log(df.questions)
    return df


def analyse(df, cutoff, pre_end, eval_end=None, mag_end=None, label=""):
    """Fit log(q) ~ t + C(month) on pre-period, measure deviation from own trend.

    eval_end : last month in which an onset may be detected (placebo uses a
               window that stops before the real treatment date).
    mag_end  : magnitude = mean shortfall over the 6 months ending here.
    """
    rows, curves = [], {}
    for site, g in df.groupby("site"):
        g = g.sort_values("mo").copy()
        pre = g[g.mo <= pre_end]
        if len(pre) < 24:
            rows.append(dict(site=site, note="insufficient pre-period"))
            continue
        fit = smf.ols("logq ~ t + C(month)", data=pre).fit()
        g["pred"] = fit.predict(g)
        g["resid"] = g.logq - g.pred
        g["shortfall"] = np.exp(g.resid) - 1
        sd = fit.resid.std()

        win = g[g.mo >= cutoff]
        if eval_end is not None:
            win = win[win.mo <= eval_end]
        below = (win.resid < -2 * sd).to_numpy()
        dates = win.mo.to_numpy()
        onset = None
        for i in range(len(below) - 2):
            if below[i] and below[i + 1] and below[i + 2]:
                onset = pd.Timestamp(dates[i]); break

        magsrc = g if mag_end is None else g[g.mo <= mag_end]
        last6 = magsrc.tail(6)
        rows.append(dict(
            site=site,
            category="technical" if site in TECH else "non-technical",
            onset=onset.strftime("%Y-%m") if onset is not None else "no detected break",
            shortfall_last6mo=round(last6.shortfall.mean(), 3),
            mag_window=f"{last6.mo.min():%Y-%m}..{last6.mo.max():%Y-%m}",
            pre_r2=round(fit.rsquared, 3),
            resid_sd=round(sd, 4),
            durbin_watson=round(durbin_watson(fit.resid), 2),
            pre_n=len(pre),
        ))
        curves[site] = g
    out = pd.DataFrame(rows).sort_values("shortfall_last6mo")
    out.insert(0, "analysis", label)
    return out, curves


def figure(curves, path="shortfall.png"):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    colors = plt.cm.tab20.colors
    for i, site in enumerate([s for s in ORDER if s in curves]):
        g = curves[site]
        tech = site in TECH
        ax.plot(g.mo, g.shortfall * 100, "-" if tech else "--",
                lw=2.1 if tech else 1.7, color=colors[i],
                label=f"{site} ({'technical' if tech else 'non-technical'})")
    ax.axvline(REAL_CUTOFF, color="grey", ls=":", lw=1.4)
    ax.annotate("ChatGPT\n2022-11-30", xy=(REAL_CUTOFF, ax.get_ylim()[1]),
                xytext=(6, -34), textcoords="offset points", fontsize=9, color="grey")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Deviation from site's own pre-2022 trend (%)")
    ax.set_xlabel("Month")
    ax.set_title("Stack Exchange question volume vs. each site's own extrapolated pre-trend\n"
                 "solid = technical, dashed = non-technical", fontsize=11)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print("wrote", path)


def power_check(df):
    y = df[df.mo.dt.year == 2019].groupby("site").questions.mean().round(1)
    out = y.reset_index().rename(columns={"questions": "mean_monthly_q_2019"})
    out["underpowered_lt300"] = out.mean_monthly_q_2019 < 300
    return out.sort_values("mean_monthly_q_2019")


def unanswered_plot(df, path="unanswered_share.png"):
    if "unanswered" not in df or df.unanswered.notna().sum() == 0:
        print("SKIP unanswered plot: column empty (Path B data has no answer-side fields)")
        return False
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = plt.cm.tab10.colors
    for i, site in enumerate([s for s in ORDER if s in set(df.site)]):
        g = df[(df.site == site) & df.unanswered.notna()].sort_values("mo")
        if g.empty: continue
        ax.plot(g.mo, 100 * g.unanswered / g.questions, "-" if site in TECH else "--",
                lw=1.6, color=colors[i], label=site)
    ax.axvline(REAL_CUTOFF, color="grey", ls=":", lw=1.4)
    ax.axvline(pd.Timestamp("2023-06-01"), color="firebrick", ls="-.", lw=1.2)
    ax.annotate("SO mod strike\n2023-06", xy=(pd.Timestamp("2023-06-01"), ax.get_ylim()[1]),
                xytext=(5, -32), textcoords="offset points", fontsize=8, color="firebrick")
    ax.set_ylabel("Share of questions with zero answers (%)")
    ax.set_title("Deletion / moderation confound check: unanswered share over time", fontsize=11)
    ax.grid(alpha=0.25); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight")
    print("wrote", path)
    return True


if __name__ == "__main__":
    df = prep()
    print(f"panel: {len(df)} site-months, {df.mo.min():%Y-%m} .. {df.mo.max():%Y-%m}, "
          f"{df.site.nunique()} sites\n")

    real, curves = analyse(df, REAL_CUTOFF, REAL_PRE_END, label="real (cutoff 2022-11)")
    # Placebo: fit 2016-01..2019-10, detect only in the CLEAN window that ends
    # before the real treatment, and measure magnitude over 2022-05..2022-10.
    pla, _ = analyse(df, PLA_CUTOFF, PLA_PRE_END, eval_end=REAL_PRE_END,
                     mag_end=REAL_PRE_END, label="placebo (cutoff 2019-11)")

    print("=== REAL ===");    print(real.to_string(index=False))
    print("\n=== PLACEBO ==="); print(pla.to_string(index=False))
    print("\n=== POWER CHECK (2019 mean monthly questions) ===")
    print(power_check(df).to_string(index=False))

    real.to_csv("summary.csv", index=False)
    pd.concat([real, pla]).to_csv("summary_with_placebo.csv", index=False)
    figure(curves)
    unanswered_plot(df)
    print("\nwrote summary.csv, summary_with_placebo.csv")
