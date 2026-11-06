"""
Out-of-sample, real-time replay of FROZEN v3 (no parameter or code changes).

Pre-registered prediction (stated in chat, 6 Nov 2026, before this ran):
  "v3 dated nothing in October" for NVDA -- the Sep->Oct run-up was not
  super-exponential, so the price detector should stay silent through the drop.

For every weekly date d from 2026-09-18 to the last available week, the weekly
series is truncated at d and v3 is run exactly as it would have been on that day:
GSADF on log price, order-preserving wild bootstrap (B=499, seed 101, as run_v3.py),
52-week family-wise critical values, ceil(log T) minimum duration.
Records: whole-sample p, whether the last week is flagged, whether an episode is live.
RSP is an addition (the clean control v2 lacked); it was not part of the prediction.
"""
import os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
from fast_psy import bsadf_fast, _min_obs_from_r0
from psy_v3 import wild_null_bsadf, gsadf_pvalue, familywise_cv, date_episodes, min_duration

DATA = os.environ.get("DATA_DIR", "data")
SERIES = ["NVDA", "SMH", "SPY", "CRWV", "RSP"]
START = pd.Timestamp("2026-09-18")
B, SEED, WINDOW = 499, 101, 52
# v3 (Sep 2026) ran on Stooq histories with these first dates. Yahoo goes back further
# (NVDA to its 1999 IPO); the frozen test must use v3's samples, so truncate to match.
# RSP was not in v3; it gets SPY's start for comparability.
SAMPLE_START = {"NVDA": "2009-01-22", "SMH": "2010-02-25", "SPY": "2005-02-25",
                "CRWV": "2025-03-28", "RSP": "2005-02-25"}
FULL = os.environ.get("FULL_HISTORY") == "1"     # set to reproduce the full-history run


def weekly(t):
    d = pd.read_csv(os.path.join(DATA, f"{t.lower()}_us_d.csv"), parse_dates=["Date"])
    d = d.set_index("Date").sort_index()["Close"]
    if not FULL:
        d = d[d.index >= SAMPLE_START[t]]
    return d.resample("W-FRI").last().dropna()


def one(job):
    t, d = job
    px = weekly(t)
    px = px[px.index <= d]
    y = np.log(px.values); T = len(y)
    bs = bsadf_fast(y, _min_obs_from_r0(T))
    w = wild_null_bsadf(y, B, seed=SEED)
    cv = familywise_cv(w, WINDOW)
    eps, flag = date_episodes(bs, cv, min_duration(T))
    live = [e for e in eps if e[2] is None]
    return dict(series=t, as_of=d.date(), T=T, close=float(px.iloc[-1]),
                gsadf_p=gsadf_pvalue(bs, w),
                bsadf_last=float(bs[-1]), cv_last=float(cv[-1]),
                flag_last_week=bool(flag[-1]),
                live_episode=bool(live),
                live_since=(px.index[live[0][0]].date() if live else None),
                n_episodes=len(eps))


if __name__ == "__main__":
    jobs = []
    for t in SERIES:
        dates = weekly(t).index
        jobs += [(t, d) for d in dates[dates >= START]]
    t0 = time.time()
    with Pool(2) as p:
        rows = p.map(one, jobs, chunksize=1)
    df = pd.DataFrame(rows)
    out = os.path.join(os.path.dirname(__file__), "..", "results",
                       "oos_realtime_fullhistory.csv" if FULL else "oos_realtime.csv")
    df.to_csv(out, index=False)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    print(f"\n{len(jobs)} runs in {time.time()-t0:.0f}s")
