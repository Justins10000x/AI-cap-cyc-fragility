"""
circular_funding.py -- v1 of the circular-funding ratio, from SEC XBRL company facts.

Question: how much of the AI capital loop is Nvidia's own money coming back?

v1 measures, quarter by quarter, from data/{nvda,crwv}_companyfacts.json:

  NVDA exposure ratio = (stakes in private companies + stakes in listed companies
                         + guarantee maximum exposure) / trailing-12-month revenue
  NVDA earnings loop  = gains on investments / pre-tax income
  CRWV funding gap    = 1 - operating cash flow / capex  (share of capex funded externally)
  CRWV interest load  = interest expense on debt / revenue

What the SEC's company-facts API cannot give (it carries only standard us-gaap tags
and drops facts broken down by an axis): customer concentration, stakes by investee,
Nvidia's custom-tagged cash-flow line for non-marketable investments, and the text
describing what each commitment is. Those need the filing text and are out of scope
for v1. Every "n/t" in the output means "not tagged in this form", never zero.

Interpretation limits, stated wherever results are reported:
  * Stakes are carried values and include revaluation gains, not only cash invested.
  * Guarantee exposure is the MAXIMUM Nvidia could owe, not an expected loss.
  * Not every investee is a customer, so the exposure ratio is an upper bound on
    vendor-financed demand.
"""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd

DATA = os.environ.get("DATA_DIR", "data")


def load_facts(path: str) -> dict:
    return json.load(open(path))["facts"]["us-gaap"]


def _frame(facts: dict, tag: str) -> pd.DataFrame | None:
    t = facts.get(tag)
    if t is None or "USD" not in t["units"]:
        return None
    df = pd.DataFrame(t["units"]["USD"])
    for c in ("start", "end", "filed"):
        if c in df:
            df[c] = pd.to_datetime(df[c])
    return df


def instant(facts: dict, tag: str) -> pd.Series:
    """Point-in-time values by period end, as FIRST reported (point-in-time integrity)."""
    df = _frame(facts, tag)
    if df is None:
        return pd.Series(dtype=float, name=tag)
    df = df[df.get("start").isna()] if "start" in df else df
    g = df.sort_values("filed").groupby("end").first()
    return g["val"].astype(float).rename(tag).sort_index()


def quarterly(facts: dict, tag: str) -> pd.Series:
    """Quarterly flow values. 10-Q cash-flow facts are year-to-date (90/180/270 days),
    10-K facts are annual, so a quarter = YTD(k) - YTD(k-1) within a fiscal year.
    Directly reported ~90-day facts are used as-is where they exist."""
    df = _frame(facts, tag)
    if df is None or "start" not in df:
        return pd.Series(dtype=float, name=tag)
    df = df.dropna(subset=["start"])
    df = df.sort_values("filed").groupby(["start", "end"], as_index=False).first()
    df["days"] = (df.end - df.start).dt.days
    out = {}
    for r in df[df.days.between(80, 100)].itertuples():
        out[r.end] = float(r.val)
    for start, g in df.groupby("start"):          # YTD chains share a fiscal-year start
        g = g[g.days > 80].sort_values("end")
        prev_end, prev_val = None, 0.0
        for r in g.itertuples():
            q_days = (r.end - (prev_end if prev_end is not None else start)).days
            if 80 <= q_days <= 100 and r.end not in out:
                out[r.end] = float(r.val) - prev_val
            prev_end, prev_val = r.end, float(r.val)
    return pd.Series(out, name=tag, dtype=float).sort_index()


def reconcile(facts: dict, tag: str, tol: float = 1e6) -> int:
    """Check that derived quarters sum to every annual (10-K) figure with four
    derived quarters inside it. Raises on any mismatch; returns years checked."""
    q = quarterly(facts, tag)
    df = _frame(facts, tag)
    if df is None or "start" not in df or q.empty:
        return 0
    df = df.dropna(subset=["start"])
    ann = df[(df.end - df.start).dt.days.between(350, 380)].sort_values("filed").groupby("end").first()
    n = 0
    for e, r in ann.iterrows():
        qs = q[(q.index > r.start) & (q.index <= e)]
        if len(qs) == 4:
            n += 1
            if abs(qs.sum() - r.val) > tol:
                raise AssertionError(f"{tag}: quarters for FY ending {e.date()} sum to "
                                     f"{qs.sum():,.0f}, 10-K says {r.val:,.0f}")
    return n


NVDA_FLOWS = ["EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount",
              "GainLossOnInvestments",
              "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"]
CRWV_FLOWS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "PaymentsToAcquirePropertyPlantAndEquipment",
              "NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInFinancingActivities",
              "InterestExpenseDebt"]


# ---------------------------------------------------------------------------
def nvda_panel(path_facts: str, ttm_revenue: pd.Series) -> pd.DataFrame:
    f = load_facts(path_facts)
    priv = instant(f, "EquitySecuritiesWithoutReadilyDeterminableFairValueAmount")
    pub = instant(f, "EquitySecuritiesFvNi")
    guar = instant(f, "GuaranteeObligationsMaximumExposure")
    unrec = instant(f, "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount")
    reval = quarterly(f, "EquitySecuritiesWithoutReadilyDeterminableFairValueUpwardPriceAdjustmentAnnualAmount")
    gains = quarterly(f, "GainLossOnInvestments")
    pretax = quarterly(f, "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest")
    ends = ttm_revenue.index[ttm_revenue.index >= priv.index.min()]
    p = pd.DataFrame(index=ends)
    p["ttm_revenue"] = ttm_revenue
    p["private_stakes"] = priv
    p["listed_stakes"] = pub
    p["guarantee_max"] = guar
    p["unrecorded_purchase_obligations"] = unrec
    p["private_reval_gain_q"] = reval
    p["investment_gains_q"] = gains
    p["pretax_income_q"] = pretax
    p["private_stakes_net_new_q"] = p.private_stakes.diff() - p.private_reval_gain_q
    parts = ["private_stakes", "listed_stakes", "guarantee_max"]
    p["exposure_known"] = p[parts].sum(axis=1, min_count=1)
    p["exposure_complete"] = p[parts].notna().all(axis=1)
    p["exposure_pct_ttm_revenue"] = p.exposure_known / p.ttm_revenue
    p["gains_pct_pretax"] = p.investment_gains_q / p.pretax_income_q
    return p


def crwv_panel(path_facts: str) -> pd.DataFrame:
    f = load_facts(path_facts)
    q = {
        "revenue_q": quarterly(f, "RevenueFromContractWithCustomerExcludingAssessedTax"),
        "capex_q": quarterly(f, "PaymentsToAcquirePropertyPlantAndEquipment"),
        "ocf_q": quarterly(f, "NetCashProvidedByUsedInOperatingActivities"),
        "financing_q": quarterly(f, "NetCashProvidedByUsedInFinancingActivities"),
        "interest_q": quarterly(f, "InterestExpenseDebt"),
    }
    p = pd.DataFrame(q)
    p["debt"] = instant(f, "DebtInstrumentCarryingAmount")
    p["backlog_rpo"] = instant(f, "RevenueRemainingPerformanceObligation")
    p["op_lease_liability"] = instant(f, "OperatingLeaseLiability")
    p["external_funding_share"] = 1 - p.ocf_q / p.capex_q
    p["interest_pct_revenue"] = p.interest_q / p.revenue_q
    return p.sort_index()


if __name__ == "__main__":
    from nvda_valuation import quarterly_revenue
    rev = quarterly_revenue(os.path.join(DATA, "nvda_revenue.json"))
    ttm = rev.set_index("period_end").value.rolling(4).sum()
    for path, tags in ((os.path.join(DATA, "nvda_companyfacts.json"), NVDA_FLOWS),
                       (os.path.join(DATA, "crwv_companyfacts.json"), CRWV_FLOWS)):
        f = load_facts(path)
        checked = {t: reconcile(f, t) for t in tags}
        print(f"reconciled with 10-K annuals ({os.path.basename(path)}): "
              + ", ".join(f"{t[:28]}… {n}y" for t, n in checked.items()))
    nv = nvda_panel(os.path.join(DATA, "nvda_companyfacts.json"), ttm)
    cw = crwv_panel(os.path.join(DATA, "crwv_companyfacts.json"))
    os.makedirs("results", exist_ok=True)
    nv.to_csv("results/circular_nvda.csv"); cw.to_csv("results/circular_crwv.csv")
    B = lambda x: "n/t" if pd.isna(x) else f"{x/1e9:,.1f}"
    P = lambda x: "n/t" if pd.isna(x) else f"{x:.0%}"
    pd.set_option("display.width", 220)
    print("NVIDIA ($B; n/t = not tagged in this form)")
    print(pd.DataFrame({"TTM revenue": nv.ttm_revenue.map(B), "private stakes": nv.private_stakes.map(B),
                        "listed stakes": nv.listed_stakes.map(B), "guarantees (max)": nv.guarantee_max.map(B),
                        "exposure % TTM rev": nv.exposure_pct_ttm_revenue.map(P),
                        "complete?": nv.exposure_complete, "inv. gains % pretax": nv.gains_pct_pretax.map(P),
                        "net new private $ (q)": nv.private_stakes_net_new_q.map(B)}).to_string())
    print("\nCOREWEAVE ($B)")
    print(pd.DataFrame({"revenue": cw.revenue_q.map(B), "capex": cw.capex_q.map(B), "op. cash flow": cw.ocf_q.map(B),
                        "capex funded externally": cw.external_funding_share.map(P), "debt": cw.debt.map(B),
                        "interest % revenue": cw.interest_pct_revenue.map(P), "backlog": cw.backlog_rpo.map(B)}).to_string())
