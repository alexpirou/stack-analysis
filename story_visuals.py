"""Data story visuals for 'AI replacing Stack Overflow' narrative."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches

CHATGPT  = pd.Timestamp("2022-11-30")
CUT      = pd.Timestamp("2022-11-01")
TECH     = {"stackoverflow", "math", "physics", "cs", "unix", "datascience"}
PROF     = {"workplace"}
COLORS   = {"stackoverflow": "#F48024",
             "math":          "#4B8BBE",
             "physics":       "#2E86AB",
             "cs":            "#6C91C2",
             "unix":          "#1B5299",
             "datascience":   "#A23B72",
             "english":       "#6BAE75",
             "cooking":       "#E07B54",
             "travel":        "#9B79C4",
             "worldbuilding": "#C0776A",
             "gaming":        "#5BA08A",
             "movies":        "#D4A847",
             "history":       "#8B6B42",
             "fitness":       "#7BAD6E",
             "workplace":     "#888888",
             "philosophy":    "#B56FAE"}
TECH_COL   = "#4B8BBE"
NONTECH_COL = "#6BAE75"
PROF_COL   = "#888888"

df = pd.read_csv("se_panel.csv", parse_dates=["mo"])
df = df[df.questions.notna() & (df.questions > 0)].copy()

# ── Visual 1: The Drop ────────────────────────────────────────────────────────
so = df[df.site == "stackoverflow"].sort_values("mo")

fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")

ax.fill_between(so.mo, so.questions / 1000, alpha=0.15, color="#F48024")
ax.plot(so.mo, so.questions / 1000, color="#F48024", lw=2.2)

# Shade post-ChatGPT region
ax.axvspan(CUT, so.mo.max(), alpha=0.07, color="#cc0000", lw=0)

# ChatGPT line
ax.axvline(CUT, color="#cc0000", ls="--", lw=1.6)
ax.annotate("ChatGPT\nlaunches\nNov 2022",
            xy=(CUT, ax.get_ylim()[1] * 0.92),
            xytext=(18, 0), textcoords="offset points",
            fontsize=9.5, color="#cc0000", va="top",
            arrowprops=dict(arrowstyle="-", color="#cc0000", lw=1))

# Peak annotation
peak = so.loc[so.questions.idxmax()]
ax.annotate(f"Peak: {int(peak.questions/1000)}k\n({peak.mo:%b %Y})",
            xy=(peak.mo, peak.questions / 1000),
            xytext=(-60, -28), textcoords="offset points",
            fontsize=8.5, color="#555",
            arrowprops=dict(arrowstyle="->", color="#aaa", lw=1))

# Latest annotation
last = so.iloc[-1]
ax.annotate(f"Today: {int(last.questions/1000)}k\n({last.mo:%b %Y})",
            xy=(last.mo, last.questions / 1000),
            xytext=(-90, 20), textcoords="offset points",
            fontsize=8.5, color="#cc0000",
            arrowprops=dict(arrowstyle="->", color="#cc0000", lw=1))

ax.set_title("Questions on Stack Overflow have collapsed since ChatGPT",
             fontsize=13, fontweight="bold", pad=14, loc="left")
ax.set_ylabel("Questions posted per month (thousands)", fontsize=10)
ax.set_xlabel("")
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:.0f}k"))
ax.grid(axis="y", alpha=0.3, lw=0.8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(labelsize=9)

fig.tight_layout()
fig.savefig("story_v1_the_drop.png", dpi=150, bbox_inches="tight")
print("wrote story_v1_the_drop.png")
plt.close()


# ── Visual 2: Technical vs Non-Technical (indexed) ───────────────────────────
# Index each site to its Oct 2022 level, then average by category post-cutoff
BASE_MO = pd.Timestamp("2022-10-01")
post = df[df.mo >= pd.Timestamp("2021-01-01")].copy()

def index_to_base(g):
    base = g.loc[g.mo == BASE_MO, "questions"]
    if base.empty or base.iloc[0] == 0:
        return None
    g = g.copy()
    g["indexed"] = g.questions / base.iloc[0] * 100
    return g

frames = []
for site, g in post.groupby("site"):
    g = g.sort_values("mo")
    result = index_to_base(g)
    if result is not None:
        frames.append(result)
indexed = pd.concat(frames)
indexed["category"] = indexed.site.apply(
    lambda s: "Technical" if s in TECH else "Non-Technical")

cat_mean = (indexed.groupby(["mo", "category"])["indexed"]
            .mean().reset_index())

fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")


for cat, color, ls in [("Technical", TECH_COL, "-"),
                        ("Non-Technical", NONTECH_COL, "--")]:
    d = cat_mean[cat_mean.category == cat]
    ax.plot(d.mo, d.indexed, color=color, lw=2.4, ls=ls, label=cat)
    # individual site traces (faint)
    for site in (TECH if cat == "Technical" else
                 set(df.site) - TECH):
        sd = indexed[indexed.site == site]
        ax.plot(sd.mo, sd.indexed, color=color, lw=0.8, alpha=0.25)

ax.axvline(CUT, color="#cc0000", ls="--", lw=1.5)
ax.axhline(100, color="#aaa", lw=0.8, ls=":")
ax.axvspan(CUT, cat_mean.mo.max(), alpha=0.06, color="#cc0000", lw=0)

ax.annotate("ChatGPT\nlaunches",
            xy=(CUT, 108),
            xytext=(12, 0), textcoords="offset points",
            fontsize=9, color="#cc0000")

ax.set_title("Technical communities fell fastest",
             fontsize=13, fontweight="bold", pad=14, loc="left")
ax.set_ylabel("Question volume\n(Oct 2022 = 100)", fontsize=10)
ax.legend(fontsize=10, framealpha=0, loc="upper right")
ax.grid(axis="y", alpha=0.3, lw=0.8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(labelsize=9)
ax.set_ylim(bottom=0)

fig.tight_layout()
fig.savefig("story_v2_tech_vs_nontech.png", dpi=150, bbox_inches="tight")
print("wrote story_v2_tech_vs_nontech.png")
plt.close()


# ── Visual 3: Before / After bar chart ───────────────────────────────────────
PRE_START  = pd.Timestamp("2020-11-01")
PRE_END    = pd.Timestamp("2022-10-01")
POST_START = pd.Timestamp("2024-09-01")
POST_END   = pd.Timestamp("2026-08-01")

DISPLAY = {
    "stackoverflow": "Stack Overflow", "math": "Mathematics",
    "physics": "Physics", "cs": "Computer Science",
    "unix": "Unix & Linux", "datascience": "Data Science",
    "english": "English Language", "cooking": "Cooking",
    "travel": "Travel", "worldbuilding": "Worldbuilding",
    "gaming": "Gaming", "movies": "Movies",
    "history": "History", "fitness": "Fitness",
    "workplace": "Workplace", "philosophy": "Philosophy",
}

summary = []
for site, g in df.groupby("site"):
    pre   = g[(g.mo >= PRE_START) & (g.mo <= PRE_END)].questions.mean()
    post_q = g[(g.mo >= POST_START) & (g.mo <= POST_END)].questions.mean()
    summary.append(dict(site=DISPLAY.get(site, site.capitalize()),
                        pre=pre, post=post_q,
                        cat="Technical" if site in TECH else "Non-Technical",
                        pct_change=(post_q - pre) / pre * 100))

sumdf = pd.DataFrame(summary).sort_values("pct_change")

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="#FAFAFA")
ax.set_facecolor("#FAFAFA")

bar_colors = [TECH_COL if r["cat"] == "Technical" else NONTECH_COL
               for _, r in sumdf.iterrows()]
bars = ax.barh(sumdf["site"].tolist(), sumdf["pct_change"].tolist(),
               color=bar_colors, height=0.55, zorder=3)

for bar, (_, row) in zip(bars, sumdf.iterrows()):
    ax.text(bar.get_width() - 1.5, bar.get_y() + bar.get_height() / 2,
            f"{row['pct_change']:.0f}%",
            va="center", ha="right", fontsize=10,
            color="white", fontweight="bold")

ax.axvline(0, color="#888", lw=0.8)
ax.set_title("Every community is down\nTechnical sites hit hardest",
             fontsize=12, fontweight="bold", pad=14, loc="left")
ax.set_xlabel("Change in avg. monthly questions\n(2 yrs before vs. 2 yrs after ChatGPT launch)", fontsize=9.5)

tech_patch    = mpatches.Patch(color=TECH_COL,    label="Technical")
nontech_patch = mpatches.Patch(color=NONTECH_COL, label="Non-Technical")
ax.legend(handles=[tech_patch, nontech_patch], fontsize=10,
          framealpha=0, loc="upper left", bbox_to_anchor=(1.01, 1))

ax.grid(axis="x", alpha=0.3, lw=0.8, zorder=0)
ax.spines[["top", "right", "bottom"]].set_visible(False)
ax.tick_params(labelsize=10)

fig.tight_layout()
fig.savefig("story_v3_before_after.png", dpi=150, bbox_inches="tight")
print("wrote story_v3_before_after.png")
plt.close()
