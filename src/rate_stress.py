"""
rate_stress.py -- a feature on the core thesis, not a separate one: rate rises matter
where earnings barely cover interest and where a borrower still needs new credit.

For the five hyperscalers and CoreWeave, from SEC company facts:
  coverage       = operating income (last 4 quarters) / interest expense (latest quarter x 4)
  repriced (12m) = debt due within a year + new borrowing needed over the next year
                   (4 x the quarterly funding gap from runway.py; CoreWeave: capex - op. cash flow)
  extra interest = repriced x shock          (lower bound: only debt that reprices)
                 = all debt x shock          (upper bound: as if all debt were floating)
Shocks: +25, +75, +100 basis points.

Limits: the share of floating-rate debt is not in the company-facts data (CoreWeave's
term loans are largely floating, so its upper bound is the more relevant one); new
borrowing assumes the gap is filled with debt, not cash on hand, so it overstates for
companies with large cash piles; Oracle's latest quarter ends a month earlier.
"""
from __future__ import annotations
import os
import pandas as pd
import circular_funding as cf
import runway
from hyperscalers import DEBT_TAG, NAMES

DATA = os.environ.get("DATA_DIR", "data")
SHOCKS_BP = (25, 75, 100)
INTEREST = {"msft": "InterestExpenseNonoperating", "googl": "InterestExpenseNonoperating",
            "amzn": "InterestExpenseNonoperating", "meta": "InterestExpenseDebt",
            "orcl": "InterestExpense", "crwv": "InterestExpenseDebt"}
DUE_12M = {"msft": "LongTermDebtCurrent", "googl": "LongTermDebtCurrent", "amzn": "LongTermDebtCurrent",
           "meta": "LongTermDebtCurrent", "orcl": "DebtCurrent",
           "crwv": "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths"}
DEBT = dict(DEBT_TAG, crwv="DebtInstrumentCarryingAmount")
LABEL = dict(NAMES, crwv="CoreWeave")


def stress(op_income: float, interest_run: float, debt: float, repriced: float, bp: int) -> dict:
    s = bp / 1e4
    lo, hi = repriced * s, debt * s
    cov = lambda extra: (op_income / (interest_run + extra)) if interest_run + extra > 0 else float("nan")
    return dict(extra_lo=lo, extra_hi=hi,
                extra_lo_pct_op=lo / op_income if op_income > 0 else float("nan"),
                extra_hi_pct_op=hi / op_income if op_income > 0 else float("nan"),
                coverage_after_hi=cov(hi))


def borrower(co: str) -> dict:
    f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
    op = cf.quarterly(f, "OperatingIncomeLoss").tail(4)
    intr = cf.quarterly(f, INTEREST[co])
    debt = cf.instant(f, DEBT[co]).iloc[-1]
    due = cf.instant(f, DUE_12M[co]).iloc[-1]
    if co == "crwv":
        q = pd.DataFrame({"capex": cf.quarterly(f, "PaymentsToAcquirePropertyPlantAndEquipment"),
                          "ocf": cf.quarterly(f, "NetCashProvidedByUsedInOperatingActivities")}).dropna().tail(2)
        gap_q = (q.capex - q.ocf).mean()
        rev_run = cf.quarterly(f, "RevenueFromContractWithCustomerExcludingAssessedTax").iloc[-1] * 4
    else:
        gap_q = runway.company(co).tail(2).gap.mean()
        rev_run = float("nan")
    new_borrow = 4 * max(0.0, gap_q)
    r = dict(company=LABEL[co], as_of=str(op.index[-1].date()), op_income_ttm=op.sum(),
             interest_run=intr.iloc[-1] * 4, debt=debt, due_12m=due, new_borrowing_12m=new_borrow,
             repriced_12m=due + new_borrow, revenue_run=rev_run)
    r["coverage_now"] = r["op_income_ttm"] / r["interest_run"] if r["interest_run"] > 0 else float("nan")
    r["interest_pct_revenue_now"] = r["interest_run"] / rev_run if rev_run == rev_run else float("nan")
    for bp in SHOCKS_BP:
        for k, v in stress(r["op_income_ttm"], r["interest_run"], debt, r["repriced_12m"], bp).items():
            r[f"{k}_{bp}"] = v
    return r


if __name__ == "__main__":
    d = pd.DataFrame([borrower(c) for c in ["msft", "googl", "amzn", "meta", "orcl", "crwv"]]).set_index("company")
    os.makedirs("results", exist_ok=True)
    d.to_csv("results/rate_stress.csv")
    B = lambda x: f"${x/1e9:,.1f}B"
    P = lambda x: "n/a" if x != x else f"{x:.1%}"
    X = lambda x: "below 0" if x != x or x < 0 else f"{x:.0f}x"
    out = pd.DataFrame({"op. income (4q)": d.op_income_ttm.map(B), "interest (run-rate)": d.interest_run.map(B),
                        "covered": d.coverage_now.map(X), "debt": d.debt.map(B), "reprices in 12m": d.repriced_12m.map(B),
                        "+75bp, % of op. income (repriced)": d.extra_lo_pct_op_75.map(P),
                        "+75bp, % (all debt)": d.extra_hi_pct_op_75.map(P),
                        "+100bp, % (all debt)": d.extra_hi_pct_op_100.map(P),
                        "covered after +75bp (all debt)": d.coverage_after_hi_75.map(X)})
    pd.set_option("display.width", 250)
    print(out.to_string())
    c = d.loc["CoreWeave"]
    print(f"\nCoreWeave: operating income {B(c.op_income_ttm)} over 4 quarters vs interest {B(c.interest_run)} a year; "
          f"interest {c.interest_pct_revenue_now:.0%} of revenue now, "
          f"{(c.interest_run + c.extra_hi_75) / c.revenue_run:.0%} after +75bp on all debt")
