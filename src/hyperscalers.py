"""
hyperscalers.py -- circular-funding ratio v2, part 1: can Nvidia's biggest buyers
pay for the build-out from their own cash?

For Microsoft, Alphabet, Amazon, Meta and Oracle, from SEC XBRL company facts:
  capex / operating cash flow, per quarter   (>100% = spending more than the business earns in cash)
  long-term debt, per quarter-end

Every quarterly flow is derived from year-to-date filings and reconciled to the
annual 10-K totals (circular_funding.reconcile) on each run.

Limits: cash capex only -- finance leases and leases signed but not yet started are
NOT included, so true spending commitments are higher. The debt tag differs by
company (see DEBT_TAG), so compare each company's debt with its own past, not
with the others'. Oracle's fiscal quarters end a month before the others'.
"""
from __future__ import annotations
import os
import pandas as pd
import circular_funding as cf

DATA = os.environ.get("DATA_DIR", "data")
NAMES = {"msft": "Microsoft", "googl": "Alphabet", "amzn": "Amazon", "meta": "Meta", "orcl": "Oracle"}
CAPEX_TAG = {"msft": "PaymentsToAcquirePropertyPlantAndEquipment",
             "googl": "PaymentsToAcquirePropertyPlantAndEquipment",
             "amzn": "PaymentsToAcquireProductiveAssets",
             "meta": "PaymentsToAcquirePropertyPlantAndEquipment",
             "orcl": "PaymentsToAcquirePropertyPlantAndEquipment"}
OCF_TAG = "NetCashProvidedByUsedInOperatingActivities"
DEBT_TAG = {"msft": "LongTermDebt", "googl": "LongTermDebtNoncurrent", "amzn": "LongTermDebt",
            "meta": "LongTermDebtNoncurrent", "orcl": "LongTermNotesAndLoans"}


def calendar_quarter(idx: pd.DatetimeIndex) -> pd.PeriodIndex:
    """Map fiscal quarter-ends to calendar quarters (Oracle's Aug 31 -> Q3)."""
    return pd.PeriodIndex(idx, freq="Q")


def company_panel(co: str, start="2022-01-01") -> pd.DataFrame:
    f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
    # reconcile every fiscal year that overlaps the reported window
    since = pd.Timestamp(start) - pd.DateOffset(months=7)
    years = {t: cf.reconcile(f, t, since=since) for t in (CAPEX_TAG[co], OCF_TAG)}
    assert min(years.values()) >= 3, f"{co}: too few fiscal years reconciled: {years}"
    p = pd.DataFrame({"capex": cf.quarterly(f, CAPEX_TAG[co]), "ocf": cf.quarterly(f, OCF_TAG)})
    p["debt"] = cf.instant(f, DEBT_TAG[co])
    p = p[p.index >= start].dropna(subset=["capex", "ocf"])
    p["capex_pct_ocf"] = p.capex / p.ocf
    p["quarter"] = calendar_quarter(p.index)
    p["company"] = NAMES[co]
    return p


def all_panels(start="2022-01-01") -> pd.DataFrame:
    return pd.concat([company_panel(c, start) for c in NAMES])


if __name__ == "__main__":
    d = all_panels()
    os.makedirs("results", exist_ok=True)
    d.to_csv("results/hyperscalers.csv")
    pd.set_option("display.width", 200)
    print("capex as % of operating cash flow:")
    print(d.pivot(index="quarter", columns="company", values="capex_pct_ocf").tail(9).map(lambda x: f"{x:.0%}" if pd.notna(x) else "").to_string())
    for col in ("capex", "ocf", "debt"):
        print(f"\n{col} ($B):")
        print((d.pivot(index="quarter", columns="company", values=col) / 1e9).tail(9).round(1).to_string())
    tot = d.groupby("quarter")[["capex", "ocf"]].agg(["sum", "count"])
    full = tot[tot[("capex", "count")] == 5]
    print("\nall five combined ($B, quarters with all five reported):")
    print(pd.DataFrame({"capex": full[("capex", "sum")] / 1e9, "ocf": full[("ocf", "sum")] / 1e9,
                        "capex % ocf": full[("capex", "sum")] / full[("ocf", "sum")]}).tail(9).round(2).to_string())
