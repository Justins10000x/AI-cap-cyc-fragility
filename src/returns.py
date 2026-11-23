"""
returns.py -- does the build-out earn its keep? Return on the physical capital of the
five hyperscalers and CoreWeave, from SEC company facts.

  capital (K)          net property and equipment INCLUDING finance-lease assets, at quarter-end
  return on capital    operating income, last 4 quarters / average K over the same 5 quarter-ends
  incremental return   change in 4-quarter operating income / change in K, over 8 quarters
                       (also with K lagged 4 quarters: new capital needs time to start earning)
  hurdle test          next year, at flat capex, K grows by (4 x latest capex - next-4q depreciation);
                       earning a pre-tax hurdle h on that new capital needs operating income to
                       grow by h x that amount

Everything is PRE-TAX (operating income), so it is compared with a PRE-TAX hurdle: a cost of
capital of 8-10% grossed up at a ~18% tax rate gives HURDLE = 10-12%. That band is an
assumption, stated wherever it is used, not an estimate.

How to read the incremental return: operating income also grows for reasons that need little
new equipment (advertising pricing, software). So change in profit / change in capital is an
UPPER BOUND on what the new, mostly AI, capital earns, unless the rest of the business shrank.
A falling incremental return is informative; a high one is not proof the AI capital pays.

Limits: K is net book value, so it depends on the depreciation lives (depreciation.py);
finance leases are in K but leases signed and not yet started are not; operating income
includes businesses that use little capital, which flatters the level of return on capital
(the trend is the informative part); Oracle's quarters end a month earlier than the others'.
"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
import circular_funding as cf
from hyperscalers import CAPEX_TAG, calendar_quarter

DATA = os.environ.get("DATA_DIR", "data")
COS = ["msft", "googl", "amzn", "meta", "orcl", "crwv"]
FIVE = COS[:5]
LABEL = {"msft": "Microsoft", "googl": "Alphabet", "amzn": "Amazon", "meta": "Meta",
         "orcl": "Oracle", "crwv": "CoreWeave"}
PPE_WITH_LEASES = "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"
HURDLE = (0.10, 0.12)          # pre-tax; assumption, see docstring
PRE_BOOM = ("2019-01-01", "2021-12-31")   # reference years before the AI build-out


def capital(f: dict, co: str) -> pd.Series:
    """Net PP&E including finance-lease assets. Uses the combined tag where filed, the plain
    PP&E tag before that (finance leases were small then); Oracle reports them separately.
    Microsoft includes finance-lease assets in property and equipment, net."""
    k = cf.instant(f, PPE_WITH_LEASES).combine_first(cf.instant(f, "PropertyPlantAndEquipmentNet"))
    if co == "orcl":
        k = k.add(cf.instant(f, "FinanceLeaseRightOfUseAsset"), fill_value=0)
    return k.sort_index()


def returns_panel(oi: pd.Series, k: pd.Series) -> pd.DataFrame:
    """Quarterly panel from quarterly operating income and quarter-end capital."""
    d = pd.DataFrame({"op_income_q": oi, "capital": k}).sort_index()
    d = d[d.op_income_q.notna()]
    d["op_income_4q"] = d.op_income_q.rolling(4).sum()
    # average capital over the five quarter-ends spanning the 4 quarters (needs all five)
    d["capital_avg"] = d.capital.rolling(5).mean()
    d["return_on_capital"] = d.op_income_4q / d.capital_avg
    d["incremental_8q"] = d.op_income_4q.diff(8) / d.capital.diff(8)
    d["incremental_8q_lag4"] = d.op_income_4q.diff(8) / d.capital.shift(4).diff(8)
    return d


def company(co: str) -> pd.DataFrame:
    f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
    cf.reconcile(f, "OperatingIncomeLoss", since="2016-01-01" if co != "msft" else "2017-07-01")
    p = returns_panel(cf.quarterly(f, "OperatingIncomeLoss"), capital(f, co))
    p["capex_q"] = cf.quarterly(f, CAPEX_TAG.get(co, "PaymentsToAcquirePropertyPlantAndEquipment"))
    p["company"] = LABEL[co]
    p["quarter"] = calendar_quarter(p.index)
    return p


def hurdle_test(capex_q: float, dep_next4q: float, op_income_growth_last: float, h: float) -> dict:
    """Operating-income growth needed next year to earn pre-tax hurdle h on next year's
    new capital, at flat capex; compared with last year's growth."""
    new_capital = 4 * capex_q - dep_next4q
    need = h * new_capital
    return dict(new_capital_next4q=new_capital, oi_growth_needed=need,
                oi_growth_last_year=op_income_growth_last, cover=op_income_growth_last / need if need > 0 else np.nan)


def combined(panels: pd.DataFrame) -> pd.DataFrame:
    """The five hyperscalers summed by calendar quarter (only quarters with all five)."""
    h = panels[panels.company.isin([LABEL[c] for c in FIVE])]
    g = h.groupby("quarter")
    t = g[["op_income_4q", "capital"]].sum(min_count=1)
    t["n"] = g.company.nunique()
    t["n_oi"] = g.op_income_4q.count()
    t["n_k"] = g.capital.count()
    t = t[(t.n_oi == 5) & (t.n_k == 5)].copy()
    t["capital_avg"] = t.capital.rolling(5).mean()
    t["return_on_capital"] = t.op_income_4q / t.capital_avg
    t["incremental_4q"] = t.op_income_4q.diff(4) / t.capital.diff(4)
    t["incremental_8q"] = t.op_income_4q.diff(8) / t.capital.diff(8)
    t["incremental_8q_lag4"] = t.op_income_4q.diff(8) / t.capital.shift(4).diff(8)
    return t


if __name__ == "__main__":
    panels = pd.concat([company(c) for c in COS])
    os.makedirs("results", exist_ok=True)
    panels.to_csv("results/returns_quarterly.csv")
    C = combined(panels)
    C.to_csv("results/returns_combined.csv")
    P = lambda x: "n/a" if x != x else f"{x:.0%}"
    B = lambda x: f"${x/1e9:,.0f}B"
    pd.set_option("display.width", 220)

    rows = []
    for name, d in panels.groupby("company", sort=False):
        d = d.dropna(subset=["return_on_capital"])
        if d.empty:
            last = panels[panels.company == name].dropna(subset=["op_income_4q"]).iloc[-1]
            rows.append({"company": name, "as of": str(last.name.date()), "capital": B(last.capital),
                         "op. income 4q": B(last.op_income_4q), "return on capital": "n/a (short history)"})
            continue
        pre = d[(d.index >= PRE_BOOM[0]) & (d.index <= PRE_BOOM[1])].return_on_capital.mean()
        last = d.iloc[-1]
        rows.append({"company": name, "as of": str(last.name.date()), "capital": B(last.capital),
                     "op. income 4q": B(last.op_income_4q),
                     "return on capital 2019-21 avg": P(pre), "return on capital now": P(last.return_on_capital),
                     "incremental, 8q": P(last.incremental_8q), "incremental, 8q, capital lagged 4q": P(last.incremental_8q_lag4)})
    print("pre-tax return on physical capital (operating income / net PP&E incl. finance leases)")
    print(pd.DataFrame(rows).set_index("company").fillna("").to_string())

    print("\nfive hyperscalers combined, by calendar quarter:")
    show = C[["op_income_4q", "capital", "return_on_capital", "incremental_4q", "incremental_8q", "incremental_8q_lag4"]].copy()
    show[["op_income_4q", "capital"]] = show[["op_income_4q", "capital"]].map(B)
    for c in ("return_on_capital", "incremental_4q", "incremental_8q", "incremental_8q_lag4"):
        show[c] = show[c].map(P)
    print(show.iloc[3::4].tail(8).to_string())
    print(show.tail(1).to_string(header=False))

    print("\nconstruction in progress (capital not yet in service), where tagged:")
    for co in ("googl", "orcl"):
        f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
        cip, k = cf.instant(f, "ConstructionInProgressGross"), capital(f, co)
        d = cip.index[-1]
        print(f"  {LABEL[co]} {d.date()}: {B(cip.iloc[-1])} = {cip.iloc[-1] / k.loc[d]:.0%} of capital")

    # hurdle test, using the depreciation model's central projection at flat capex
    fits = pd.read_csv("results/depreciation_fits.csv")
    fits = fits[fits.central].set_index("company")
    last_q = panels.dropna(subset=["capex_q"]).groupby("company").tail(1).set_index("company")
    five = [LABEL[c] for c in FIVE]
    capex_q = last_q.loc[five, "capex_q"].sum()
    dep_next = fits.loc[five, "dep_next4q_flat"].sum()
    oi_growth = C.op_income_4q.iloc[-1] - C.op_income_4q.iloc[-5]
    print(f"\nhurdle test, five combined (latest {C.index[-1]}; capex flat at {B(capex_q)} a quarter):")
    print(f"  new net capital over the next 4 quarters: {B(4 * capex_q - dep_next)} "
          f"(capex {B(4 * capex_q)} minus depreciation {B(dep_next)})")
    for h in HURDLE:
        r = hurdle_test(capex_q, dep_next, oi_growth, h)
        print(f"  at a {h:.0%} pre-tax hurdle: operating income must grow {B(r['oi_growth_needed'])} a year; "
              f"last year it grew {B(oi_growth)} ({r['cover']:.1f}x the need)")
    print(f"  if operating income grows next year by as much as last year, next year's new capital earns at most "
          f"{oi_growth / (4 * capex_q - dep_next):.1%} pre-tax")
    pd.DataFrame([dict(hurdle=h, **hurdle_test(capex_q, dep_next, oi_growth, h)) for h in HURDLE]).to_csv(
        "results/returns_hurdle.csv", index=False)
