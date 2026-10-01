"""Stack Exchange API helper: monthly question counts via filter=total equivalent."""
import calendar, datetime as dt, json, os, time
import requests

ENDPOINT = "https://api.stackexchange.com/2.3/questions"
FILTER = "!9n30IGbb1J()"          # base=none -> {.total, .quota_remaining, .backoff}
KEY = os.environ.get("SE_API_KEY") or None

_session = requests.Session()
_session.headers["User-Agent"] = "se-llm-shock-study/1.0 (monthly aggregate counts)"


class QuotaExhausted(RuntimeError):
    pass


def epoch(y, m, d=1, h=0, mi=0, s=0):
    """UTC epoch seconds. SE API and SEDE CreationDate are both UTC."""
    return calendar.timegm(dt.datetime(y, m, d, h, mi, s).timetuple())


def month_bounds(y, m):
    """[first second of month, last second of month] inclusive-inclusive."""
    nxt_y, nxt_m = (y + 1, 1) if m == 12 else (y, m + 1)
    return epoch(y, m), epoch(nxt_y, nxt_m) - 1


def count(site, frm, to, min_quota=15):
    """Question count with creation_date in [frm, to]. Raises on API error."""
    p = dict(site=site, fromdate=frm, todate=to,
             sort="creation", order="desc", filter=FILTER)
    if KEY:
        p["key"] = KEY
    r = _session.get(ENDPOINT, params=p, timeout=45)
    d = r.json()
    if "error_id" in d:
        raise RuntimeError(f"API error for {site} [{frm},{to}]: {d}")
    q = d.get("quota_remaining")
    if d.get("backoff"):
        time.sleep(d["backoff"] + 0.5)
    time.sleep(0.11)
    if q is not None and q < min_quota:
        raise QuotaExhausted(f"quota_remaining={q}; stopping cleanly")
    return d["total"], q


def month_count(site, y, m, **kw):
    frm, to = month_bounds(y, m)
    return count(site, frm, to, **kw)
