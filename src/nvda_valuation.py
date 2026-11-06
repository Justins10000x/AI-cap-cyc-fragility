"""
NVDA: bubble or boom?  Test log(price / trailing-12-month revenue), not log price.

Revenue comes from SEC XBRL (data/nvda_revenue.json). Each quarterly figure is
dated by its FIRST filing date, so the ratio only uses revenue the market could
have seen (look-ahead-free; enforced by tests/test_v3.py for log_valuation).
Q4 is not reported on its own: it is derived as the 10-K annual total minus the
three 10-Q quarters, and becomes available on the 10-K filing date.

Caveat: the ratio is split-adjusted price / total revenue, i.e. price-to-sales up
to the split-adjusted share count. NVDA's split-adjusted share count has drifted
by roughly 10% in total since 2009, far too slowly to create or hide an explosive
root. The v3 test machinery is used unchanged.
"""
import json, os
import numpy as np, pandas as pd
from fast_psy import bsadf_fast, _min_obs_from_r0
from fundamentals import log_valuation
from psy_v3 import (wild_null_bsadf, gsadf_pvalue, familywise_cv, date_episodes,
                    min_duration, episode_table)

DATA = os.environ.get("DATA_DIR", "data")

# The series starts in fiscal 2012. Before that, some NVDA quarters sit under this
# tag only as restated comparatives first filed a year or more late, which would
# misdate them (the filing-lag assertion below catches this).
FIRST_FISCAL_START = pd.Timestamp("2011-01-31")

# FY2019-FY2021 annual totals were originally filed under the ASC 606 tag; under
# us-gaap:Revenues they appear late (FY2019 not at all; FY2020/21 first in the 2022
# 10-K). Values and FIRST filing dates from SEC XBRL
# us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax, fetched 6 Nov 2026.
# Values agree with us-gaap:Revenues to the dollar wherever both exist.
SUPPLEMENT_ANNUALS = [
    dict(start="2018-01-29", end="2019-01-27", val=11_716_000_000, filed="2019-02-21", form="10-K"),
    dict(start="2019-01-28", end="2020-01-26", val=10_918_000_000, filed="2020-02-20", form="10-K"),
    dict(start="2020-01-27", end="2021-01-31", val=16_675_000_000, filed="2021-02-26", form="10-K"),
]


def _verify_supplement(asc606_path):
    """If the ASC 606 file has been downloaded (src/fetch_data.py), check every
    hard-coded value and first-filing date against it. Raises on any mismatch."""
    if not os.path.exists(asc606_path):
        return False
    df = pd.DataFrame(json.load(open(asc606_path))["units"]["USD"])
    for s in SUPPLEMENT_ANNUALS:
        hit = df[(df.start == s["start"]) & (df.end == s["end"])]
        assert len(hit), f"supplement period {s['start']}..{s['end']} not in {asc606_path}"
        assert (hit.val == s["val"]).all(), f"value mismatch for {s['end']}"
        assert hit.filed.min() == s["filed"], f"first-filed mismatch for {s['end']}"
    return True


def quarterly_revenue(path):
    _verify_supplement(os.path.join(os.path.dirname(path), "nvda_revenue_asc606.json"))
    j = json.load(open(path))
    df = pd.concat([pd.DataFrame(j["units"]["USD"]), pd.DataFrame(SUPPLEMENT_ANNUALS)],
                   ignore_index=True)
    for c in ("start", "end", "filed"):
        df[c] = pd.to_datetime(df[c])
    df = df[df.start >= FIRST_FISCAL_START]
    df["days"] = (df.end - df.start).dt.days
    first = lambda d: d.sort_values("filed").groupby(["start", "end"], as_index=False).first()
    q = first(df[df.days.between(80, 100)])
    a = first(df[df.days.between(350, 380)])
    annual_filed = dict(zip(a.end, a.filed))
    # A fiscal Q4 is knowable once the 10-K is out (annual minus Q1-Q3), even if the
    # standalone Q4 figure is only first tagged in a later filing.
    rows = [dict(period_end=r.end,
                 filed=min(r.filed, annual_filed.get(r.end, r.filed)),
                 value=float(r.val), derived=False)
            for r in q.itertuples()]
    have = set(q.end)
    for r in a.itertuples():                         # derive any missing fiscal Q4
        inside = q[(q.start >= r.start) & (q.end <= r.end)]
        if r.end in have or len(inside) != 3:
            continue
        rows.append(dict(period_end=r.end, filed=r.filed,
                         value=float(r.val - inside.val.sum()), derived=True))
    out = pd.DataFrame(rows).sort_values("period_end").reset_index(drop=True)
    lag = (out.filed - out.period_end).dt.days
    assert lag.between(0, 75).all(), f"late or impossible filing date:\n{out[~lag.between(0, 75)]}"
    gaps = out.period_end.diff().dt.days.dropna()
    assert gaps.between(80, 100).all(), f"quarter gap found:\n{out[out.period_end.diff().dt.days > 100]}"
    return out


def run(B=499, seed=101):
    rev = quarterly_revenue(os.path.join(DATA, "nvda_revenue.json"))
    px_d = (pd.read_csv(os.path.join(DATA, "nvda_us_d.csv"), parse_dates=["Date"])
              .set_index("Date").sort_index()["Close"])
    lv_d = log_valuation(px_d, rev)                  # daily, look-ahead-free
    lv = lv_d.resample("W-FRI").last().dropna()      # weekly, as in v3
    y = lv.values; T = len(y)
    bs = bsadf_fast(y, _min_obs_from_r0(T))
    w = wild_null_bsadf(y, B, seed=seed)
    cv = familywise_cv(w, 52)
    eps, flag = date_episodes(bs, cv, min_duration(T))
    ps = np.exp(lv)                                  # price / TTM revenue (up to share count)
    return dict(rev=rev, lv=lv, ps=ps, bsadf=bs, cv=cv, flag=flag, eps=eps,
                p=gsadf_pvalue(bs, w), T=T, table=episode_table(ps, eps))


def price_control(r, B=499, seed=101):
    """Same test on log PRICE over exactly the ratio's window: separates 'the ratio
    finds nothing' from 'the shorter window finds nothing'."""
    lv = r["lv"]
    px = (pd.read_csv(os.path.join(DATA, "nvda_us_d.csv"), parse_dates=["Date"])
            .set_index("Date").sort_index()["Close"].resample("W-FRI").last().dropna())
    px = px[(px.index >= lv.index[0]) & (px.index <= lv.index[-1])]
    assert (px.index == lv.index).all()
    y = np.log(px.values); T = len(y)
    bs = bsadf_fast(y, _min_obs_from_r0(T))
    w = wild_null_bsadf(y, B, seed=seed)
    eps, _ = date_episodes(bs, familywise_cv(w, 52), min_duration(T))
    return dict(p=gsadf_pvalue(bs, w), eps=[(px.index[o], px.index[l]) for o, l, _t in eps],
                px=px)


def decompose(r, px, episodes_csv="results/episodes_v3.csv"):
    """Split each v3 NVDA price episode (detection -> peak) into revenue growth and
    multiple change: log price = log(P/S) + log(TTM revenue)."""
    lv = r["lv"]; ep = pd.read_csv(episodes_csv); ep = ep[ep.series == "NVDA"]
    rows = []
    for e in ep.itertuples():
        a, b = pd.Timestamp(e.origination), pd.Timestamp(e.peak)
        lp = np.log(px.asof(b) / px.asof(a)); lm = lv.asof(b) - lv.asof(a)
        rows.append(dict(origination=e.origination, peak=e.peak, price=np.exp(lp) - 1,
                         revenue=np.exp(lp - lm) - 1, multiple=np.exp(lm) - 1,
                         rev_share=(lp - lm) / lp))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import pickle
    r = run()
    print(f"quarters: {len(r['rev'])} ({r['rev'].derived.sum()} derived Q4s), "
          f"{r['rev'].period_end.min().date()} -> {r['rev'].period_end.max().date()}")
    print(f"weekly P/S series: T={r['T']}, {r['lv'].index[0].date()} -> {r['lv'].index[-1].date()}")
    print(f"GSADF on log(P/TTM revenue): p = {r['p']:.3f}   episodes = {len(r['eps'])}   "
          f"live now = {bool(r['flag'][-1])}")
    if not r["table"].empty:
        print(r["table"][["origination", "peak", "termination", "weeks",
                          "gain_detect_to_peak"]].to_string(index=False))
    os.makedirs("results", exist_ok=True)
    pickle.dump(r, open("results/nvda_valuation.pkl", "wb"))

    c = price_control(r)
    print(f"\nControl, PRICE on the same window: p = {c['p']:.3f}, episodes = {len(c['eps'])}")
    for a, b in c["eps"]:
        print(f"   {a.date()} -> {b.date()}")
    pickle.dump(dict(p=c["p"], eps=c["eps"]), open("results/nvda_price_samewindow.pkl", "wb"))

    d = decompose(r, c["px"])
    d.to_csv("results/nvda_episode_decomposition.csv", index=False)
    print("\nv3 price episodes, detection -> peak:")
    print(d.to_string(index=False, float_format=lambda x: f"{x:+.0%}"))
    ps = r["lv"]
    print(f"\nMar 2012 -> latest: price x{np.exp(np.log(c['px'].iloc[-1]/c['px'].iloc[0])):.0f}, "
          f"multiple x{np.exp(ps.iloc[-1]-ps.iloc[0]):.2f}; P/S percentile now "
          f"{(ps < ps.iloc[-1]).mean():.0%}, Oct-2026 peak {(ps < ps['2026-10'].max()).mean():.0%}")
