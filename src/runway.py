"""
runway.py -- how long can each hyperscaler fund its spending gap from cash on hand?

  liquid   = cash + short-term investments at the latest quarter-end
  gap      = capex + buybacks + dividends - operating cash flow, averaged over the
             latest two quarters (operating cash flow is seasonal)
  runway   = liquid / gap, in quarters, if the gap is positive

A simple what-if, not a forecast: it holds spending, payouts and cash flow at their
recent level. In practice companies borrow, cut buybacks or slow capex long before
cash runs out. Payouts not tagged in a quarter count as zero in the gap, so the gap
is a lower bound there (flagged in `payouts_complete`).
"""
from __future__ import annotations
import os
import pandas as pd
import circular_funding as cf
from hyperscalers import NAMES, CAPEX_TAG, OCF_TAG, calendar_quarter

DATA = os.environ.get("DATA_DIR", "data")
ST_INV = {"msft": "ShortTermInvestments", "googl": "MarketableSecuritiesCurrent",
          "amzn": "MarketableSecuritiesCurrent", "meta": "MarketableSecuritiesCurrent",
          "orcl": "AvailableForSaleSecuritiesDebtSecuritiesCurrent"}
DIV = {"msft": ["PaymentsOfDividendsCommonStock"], "googl": ["PaymentsOfDividends", "PaymentsOfOrdinaryDividends"],
       "amzn": [], "meta": ["PaymentsOfDividends"], "orcl": ["PaymentsOfDividendsCommonStock"]}
BUYBACK = "PaymentsForRepurchaseOfCommonStock"


def company(co: str, start="2024-06-01") -> pd.DataFrame:
    f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
    p = pd.DataFrame({"capex": cf.quarterly(f, CAPEX_TAG[co]), "ocf": cf.quarterly(f, OCF_TAG)}).dropna()
    p["buybacks"] = cf.quarterly(f, BUYBACK)
    # a company may switch dividend tags mid-year (Alphabet did in 2026); pool the raw
    # facts first so year-to-date figures chain across the switch
    pooled = [x for t in DIV[co] if t in f for x in f[t]["units"]["USD"]]
    div = cf.quarterly({"_div": {"units": {"USD": pooled}}}, "_div") if pooled else pd.Series(dtype=float)
    p["dividends"] = div if len(div) else float("nan")
    p["liquid"] = cf.instant(f, "CashAndCashEquivalentsAtCarryingValue") + cf.instant(f, ST_INV[co])
    p = p[p.index >= start]
    pays_dividend = bool(DIV[co])
    p["payouts_complete"] = p.buybacks.notna() & (p.dividends.notna() | (not pays_dividend))
    p["gap"] = p.capex + p.buybacks.fillna(0) + p.dividends.fillna(0) - p.ocf
    p["quarter"] = calendar_quarter(p.index)
    p["company"] = NAMES[co]
    return p


def summary() -> pd.DataFrame:
    rows = []
    for co in NAMES:
        p = company(co)
        last2, prev = p.tail(2), p.iloc[-6:-4]            # latest two quarters vs the same two a year earlier
        gap = last2.gap.mean()
        rows.append(dict(company=NAMES[co], as_of=str(p.quarter.iloc[-1]),
                         liquid=p.liquid.iloc[-1], liquid_year_ago=p.liquid.iloc[-5],
                         gap_per_quarter=gap, gap_year_ago=prev.gap.mean(),
                         buybacks_2q=last2.buybacks.sum(min_count=1), buybacks_2q_year_ago=prev.buybacks.sum(min_count=1),
                         payouts_complete=bool(last2.payouts_complete.all()),
                         runway_quarters=(p.liquid.iloc[-1] / gap) if gap > 0 else float("inf")))
    return pd.DataFrame(rows).set_index("company")


if __name__ == "__main__":
    s = summary()
    os.makedirs("results", exist_ok=True)
    s.to_csv("results/runway.csv")
    pd.concat([company(c) for c in NAMES]).to_csv("results/runway_quarterly.csv")
    B = lambda x: "n/t" if pd.isna(x) else f"{x/1e9:,.1f}"
    out = s.copy()
    for c in ("liquid", "liquid_year_ago", "gap_per_quarter", "gap_year_ago", "buybacks_2q", "buybacks_2q_year_ago"):
        out[c] = out[c].map(B)
    out["runway_quarters"] = s.runway_quarters.map(lambda x: "no gap" if x == float("inf") else f"{x:.1f}")
    pd.set_option("display.width", 220)
    print(out.to_string())
    tot_gap, tot_liq = s.gap_per_quarter.sum(), s.liquid.sum()
    print(f"\ncombined: liquid ${tot_liq/1e9:,.0f}B, gap ${tot_gap/1e9:,.0f}B per quarter (year ago ${s.gap_year_ago.sum()/1e9:,.0f}B)")
