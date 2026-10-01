"""Step 2: merge into tidy long panel se_panel.csv."""
import glob, os
import pandas as pd

COLS = ["site","category","mo","questions","askers","accepted",
        "unanswered","answers","answerers"]
CAT = {"stackoverflow":"technical","math":"technical","english":"non-technical",
       "cooking":"non-technical","travel":"non-technical","worldbuilding":"non-technical",
       "physics":"technical","cs":"technical","unix":"technical","datascience":"technical",
       "gaming":"non-technical","movies":"non-technical","history":"non-technical",
       "fitness":"non-technical","workplace":"professional","philosophy":"non-technical"}
FULL = pd.date_range("2016-01-01", "2026-08-01", freq="MS")


def from_sede():
    """Path A: <slug>_questions.csv + <slug>_answers.csv if a human exported them."""
    frames = []
    for qf in sorted(glob.glob("*_questions.csv")):
        slug = os.path.basename(qf).replace("_questions.csv", "")
        if slug not in CAT: continue
        q = pd.read_csv(qf); q.columns = [c.lower() for c in q.columns]
        q = q.rename(columns={"mo":"mo"}); q["mo"] = pd.to_datetime(q["mo"])
        af = f"{slug}_answers.csv"
        if os.path.exists(af):
            a = pd.read_csv(af); a.columns = [c.lower() for c in a.columns]
            a["mo"] = pd.to_datetime(a["mo"])
            q = q.merge(a, on="mo", how="outer")
        q["site"] = slug
        frames.append(q)
    return pd.concat(frames, ignore_index=True) if frames else None


def from_api():
    if not os.path.exists("raw_questions.csv"): return None
    d = pd.read_csv("raw_questions.csv")
    d["mo"] = pd.to_datetime(d["mo"])
    return d.drop_duplicates(subset=["site","mo"])


def main():
    src = from_sede()
    origin = "SEDE (Path A)"
    if src is None or src.empty:
        src = from_api(); origin = "Stack Exchange API (Path B)"
    if src is None or src.empty:
        raise SystemExit("No input data found (need SEDE CSVs or raw_questions.csv).")

    src["category"] = src.site.map(CAT)
    for c in COLS:
        if c not in src.columns: src[c] = pd.NA
    panel = src[COLS].sort_values(["site","mo"]).reset_index(drop=True)

    # completeness report - never interpolate, just report gaps
    print(f"source: {origin}")
    for s, g in panel.groupby("site"):
        missing = sorted(set(FULL) - set(g.mo))
        print(f"  {s:15s} {len(g):3d} months  "
              f"{g.mo.min():%Y-%m}..{g.mo.max():%Y-%m}  missing={len(missing)}"
              + (f" -> {[f'{m:%Y-%m}' for m in missing[:6]]}" if missing else ""))
    panel.to_csv("se_panel.csv", index=False)
    print(f"\nwrote se_panel.csv  ({len(panel)} rows)")
    filled = [c for c in COLS[3:] if panel[c].notna().any()]
    print("populated measure columns:", filled)
    print("empty measure columns   :", [c for c in COLS[3:] if c not in filled])


if __name__ == "__main__":
    main()
