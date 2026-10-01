"""Robustness: onset sensitivity + how much of the real result survives the placebo."""
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from analyze import prep, REAL_CUTOFF, REAL_PRE_END, PLA_CUTOFF, PLA_PRE_END, TECH, ORDER

def fit_site(g, pre_end):
    pre = g[g.mo <= pre_end]
    fit = smf.ols("logq ~ t + C(month)", data=pre).fit()
    g = g.copy()
    g["pred"] = fit.predict(g)
    g["resid"] = g.logq - g.pred
    return g, fit.resid.std()

def onset(g, sd, cutoff, k, nsd, eval_end=None):
    w = g[g.mo >= cutoff]
    if eval_end is not None: w = w[w.mo <= eval_end]
    b = (w.resid < -nsd * sd).to_numpy(); d = w.mo.to_numpy()
    for i in range(len(b) - k + 1):
        if b[i:i + k].all(): return pd.Timestamp(d[i]).strftime("%Y-%m")
    return "none"

df = prep()
rows = []
for site in ORDER:
    g0 = df[df.site == site].sort_values("mo")
    gr, sdr = fit_site(g0, REAL_PRE_END)      # real fit
    gp, sdp = fit_site(g0, PLA_PRE_END)       # placebo fit
    real_gap = gr[gr.mo >= "2026-03-01"].resid.mean()          # log gap, last 6 mo
    pla_gap  = gp[(gp.mo >= "2022-05-01") & (gp.mo <= "2022-10-01")].resid.mean()
    rows.append(dict(
        site=site,
        category="technical" if site in TECH else "non-technical",
        onset_2sd_3mo=onset(gr, sdr, REAL_CUTOFF, 3, 2),      # as specified
        onset_2sd_6mo=onset(gr, sdr, REAL_CUTOFF, 6, 2),
        onset_3sd_3mo=onset(gr, sdr, REAL_CUTOFF, 3, 3),
        onset_3sd_6mo=onset(gr, sdr, REAL_CUTOFF, 6, 3),
        real_shortfall=round(np.exp(real_gap) - 1, 3),
        placebo_shortfall=round(np.exp(pla_gap) - 1, 3),
        excess_over_placebo=round(np.exp(real_gap - pla_gap) - 1, 3),
        placebo_onset=onset(gp, sdp, PLA_CUTOFF, 3, 2, eval_end=REAL_PRE_END),
    ))
out = pd.DataFrame(rows).sort_values("excess_over_placebo")
out.to_csv("robustness.csv", index=False)
print(out.to_string(index=False))
print("""
excess_over_placebo = how far the real shortfall exceeds what the SAME method
produces at a fake 2019-11 cutfoff where no treatment occurred. Caveat: the real
horizon (41-46 months post-fit) is longer than the clean placebo horizon
(31-36 months), so placebo drift is somewhat understated and this column is
therefore an OPTIMISTIC (upper) bound on the true LLM-attributable gap.""")
