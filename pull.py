"""Path B pull: monthly question counts, 16 sites x 128 months, resumable."""
import csv, os, sys, datetime as dt
import se_api as A

SITES = [("stackoverflow","technical"), ("math","technical"),
         ("english","non-technical"), ("cooking","non-technical"),
         ("travel","non-technical"), ("worldbuilding","non-technical"),
         ("physics","technical"), ("cs","technical"),
         ("unix","technical"), ("datascience","technical"),
         ("gaming","non-technical"), ("movies","non-technical"),
         ("history","non-technical"), ("fitness","non-technical"),
         ("workplace","professional"), ("philosophy","non-technical")]
START = (2016, 1)
END   = (2026, 8)          # last COMPLETE month; today is 2026-09-16
RAW   = "raw_questions.csv"


def months(start, end):
    y, m = start
    while (y, m) <= end:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def load_done():
    done = {}
    if os.path.exists(RAW):
        with open(RAW, newline="") as f:
            for r in csv.DictReader(f):
                done[(r["site"], r["mo"])] = int(r["questions"])
    return done


def main():
    if not A.KEY:
        sys.exit("ERROR: SE_API_KEY not set in environment. Refusing to run "
                 "without a key (anonymous quota is 300/day, need 768).")
    done = load_done()
    todo = [(s, c, y, m) for s, c in SITES for y, m in months(START, END)
            if (s, f"{y:04d}-{m:02d}-01") not in done]
    print(f"already have {len(done)} cells; {len(todo)} to fetch", flush=True)

    new = not os.path.exists(RAW)
    f = open(RAW, "a", newline="")
    w = csv.writer(f)
    if new:
        w.writerow(["site", "category", "mo", "questions"]); f.flush()

    q = None
    try:
        for i, (site, cat, y, m) in enumerate(todo, 1):
            total, q = A.month_count(site, y, m)
            w.writerow([site, cat, f"{y:04d}-{m:02d}-01", total]); f.flush()
            if i % 50 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}  last={site} {y}-{m:02d}={total}  quota={q}",
                      flush=True)
    except A.QuotaExhausted as e:
        print(f"STOPPED CLEANLY: {e}", flush=True)
    except Exception as e:
        print(f"STOPPED ON ERROR: {type(e).__name__}: {e}", flush=True)
    finally:
        f.close()

    have = load_done()
    print(f"DONE. {len(have)} / {6*128} cells on disk. quota_remaining={q}", flush=True)
    print(f"PULL_DATE_UTC={dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M:%S}", flush=True)


if __name__ == "__main__":
    main()
