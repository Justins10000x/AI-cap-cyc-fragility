"""
depreciation.py -- are the earnings that fund the build-out as strong as they look?

Servers and network gear are the short-lived part of the AI build-out. Each company
chooses how many years to spread their cost over (its "useful life"); a longer life
means less depreciation each year and higher reported profit. This module asks:

  1. How much depreciation is already locked in by capex that has been spent?
     (next four quarters, if capex stopped today, and if it stayed at the latest quarter's level)
  2. How much lower would operating income be if servers lasted 4 or 3 years
     instead of the stated life?
  3. How much of operating profit before depreciation does depreciation now take?

Model (a vintage, straight-line model): each quarter's capex is split into a short-lived
part (share s, depreciated over the stated server life) and a long-lived part (1 - s,
over LONG_LIFE years -- buildings, land improvements, fit-out). Depreciation starts the
quarter after an asset is placed in service, `lag` quarters after the cash is paid.
For each lag in LAGS, s is fitted by least squares to the company's reported
depreciation since its latest useful-life change (FIT_FROM). The fit is reported, and
the answers are shown for every lag that fits (RMSE below MAX_RMSE), so the reader can
see how much they depend on the unobserved lag.

Identification note: s and lag trade off (a longer lag with a bigger s fits nearly as
well), and a free scale on the long-lived part is not identified at all. The useful-life
sensitivity turns out to be stable along that ridge; the locked-in-depreciation figure
less so, which is why both are reported as ranges over lags.

Data: SEC company facts (quarterly flows derived from YTD filings and reconciled to the
10-K annuals). Stated lives: reported/useful_lives.csv (each with source and grade).
CoreWeave buys much of its equipment on credit, so its cash capex understates what it
puts in service; for CoreWeave the additions are the quarterly change in gross PP&E.

Limits: cash capex excludes finance leases (large at Microsoft and Amazon), so s is an
"effective" share per dollar of cash capex, not a physical share; disposals are ignored;
Amazon runs a subset of servers at five years but the model uses six for all, which
slightly overstates its sensitivity to a 4-year life; a shorter life is a counterfactual
on accounting, not a forecast that companies will change it.
"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
import circular_funding as cf
from hyperscalers import CAPEX_TAG

DATA = os.environ.get("DATA_DIR", "data")
REPORTED = os.environ.get("REPORTED_DIR", "reported")
COS = ["msft", "googl", "amzn", "meta", "orcl", "crwv"]
LABEL = {"msft": "Microsoft", "googl": "Alphabet", "amzn": "Amazon", "meta": "Meta",
         "orcl": "Oracle", "crwv": "CoreWeave"}
DEP_TAG = {c: "Depreciation" for c in COS}
DEP_TAG["crwv"] = "DepreciationDepletionAndAmortization"   # its "Depreciation" Q4 2025 is off the 10-K by $17M
# fit only on quarters after the latest stated change in server life (source: useful_lives.csv);
# for companies whose last change is older, the last ~9 quarters
FIT_FROM = {"msft": "2024-07-01", "googl": "2024-07-01", "amzn": "2025-01-01",
            "meta": "2025-01-01", "orcl": "2024-07-01", "crwv": "2025-01-01"}
# Meta's quarterly depreciation is presented rounded to $10M; its quarters miss the 10-K totals
# by exactly $10M in FY2023 and FY2024, so its tolerance is $25M (0.2%) instead of $1M
REC_TOL = {("meta", "Depreciation"): 25e6}
LONG_LIFE = 20
LAGS = (0, 1, 2)
MAX_RMSE = 0.10
HORIZON = 4
ALT_LIVES = (4, 3)


def stated_lives(path: str | None = None) -> dict:
    d = pd.read_csv(path or os.path.join(REPORTED, "useful_lives.csv"))
    return dict(zip(d.key, d.life_years_used.astype(float)))


def straight_line(placed: np.ndarray, life_years: float) -> np.ndarray:
    """Depreciation per quarter of assets placed in service each quarter, straight line over
    round(4 * life) quarters, starting the quarter after placement."""
    n = int(round(4 * life_years))
    c = np.concatenate([[0.0], np.cumsum(placed)])
    t = np.arange(len(placed))
    return (c[t] - c[np.maximum(0, t - n)]) / n


def placed_in_service(additions: np.ndarray, lag: int) -> np.ndarray:
    return np.concatenate([np.zeros(lag), additions[:len(additions) - lag]]) if lag else additions.copy()


def model(additions: np.ndarray, s: float, lag: int, life: float, long_life: float = LONG_LIFE):
    p = placed_in_service(additions, lag)
    short, long_ = straight_line(p, life), straight_line(p, long_life)
    return s * short + (1 - s) * long_, s * short


def fit_share(additions: pd.Series, dep: pd.Series, life: float, lag: int, fit_from) -> tuple[float, float, int]:
    """Least-squares short-lived share s for a given lag; returns (s, relative RMSE, n obs)."""
    p = placed_in_service(additions.values, lag)
    m = pd.DataFrame({"A": straight_line(p, life), "B": straight_line(p, LONG_LIFE)}, index=additions.index)
    j = m.join(dep.rename("D"), how="inner")
    j = j[j.index >= pd.Timestamp(fit_from)]
    x, y = j.A - j.B, j.D - j.B
    if len(j) < 4 or (x * x).sum() == 0:
        return float("nan"), float("nan"), len(j)
    s = float((x * y).sum() / (x * x).sum())
    fit = s * j.A + (1 - s) * j.B
    return s, float(np.sqrt(np.mean((fit / j.D - 1) ** 2))), len(j)


def additions_series(co: str, f: dict) -> pd.Series:
    if co == "crwv":
        g = cf.instant(f, "PropertyPlantAndEquipmentGross")
        a = g.diff()
        a.iloc[0] = g.iloc[0]          # opening stock treated as one vintage (all < 6 years old)
        return a.sort_index()
    return cf.quarterly(f, CAPEX_TAG[co]).sort_index()


def company(co: str, lives: dict | None = None) -> dict:
    lives = lives or stated_lives()
    life = lives[co]
    f = cf.load_facts(os.path.join(DATA, f"{co}_companyfacts.json"))
    since = pd.Timestamp(FIT_FROM[co]) - pd.DateOffset(years=2)
    for t in (DEP_TAG[co], "OperatingIncomeLoss"):
        cf.reconcile(f, t, tol=REC_TOL.get((co, t), 1e6), since=since)   # raises on any mismatch with the 10-K
    add = additions_series(co, f)
    dep = cf.quarterly(f, DEP_TAG[co])
    oi = cf.quarterly(f, "OperatingIncomeLoss")
    last = add.index[-1]
    assert last == dep.index[-1] == oi.index[-1], f"{co}: series end on different quarters"
    oi4, dep4 = oi.tail(4).sum(), dep.tail(4).sum()
    n0 = len(add)
    rows = []
    for lag in LAGS:
        s, rmse, n = fit_share(add, dep, life, lag, FIT_FROM[co])
        if not np.isfinite(s):
            continue
        r = dict(company=LABEL[co], lag_q=lag, s=s, rmse=rmse, n_fit=n, life=life, as_of=str(last.date()),
                 op_income_4q=oi4, dep_4q=dep4)
        for fut, ext in (("stop", np.zeros(HORIZON)), ("flat", np.repeat(add.values[-1], HORIZON))):
            full, _ = model(np.concatenate([add.values, ext]), s, lag, life)
            r[f"dep_next4q_{fut}"] = full[n0:n0 + HORIZON].sum()
            r[f"dep_growth_{fut}"] = r[f"dep_next4q_{fut}"] / dep4 - 1
        full, short = model(add.values, s, lag, life)
        r["short_share_of_dep"] = short[-1] / full[-1]
        for L2 in ALT_LIVES:
            p = placed_in_service(add.values, lag)
            extra = 4 * s * (straight_line(p, L2)[-1] - straight_line(p, life)[-1])
            r[f"extra_dep_{L2}y"] = extra
            r[f"extra_dep_{L2}y_pct_oi"] = extra / oi4 if oi4 > 0 else float("nan")
            r[f"op_income_4q_at_{L2}y"] = oi4 - extra
        rows.append(r)
    out = pd.DataFrame(rows)
    out["fits"] = out.rmse < MAX_RMSE
    out["central"] = out.rmse == out.rmse.min()
    return dict(fits=out, quarterly=pd.DataFrame({"depreciation": dep, "op_income": oi, "additions": add}))


def quarterly_panel(q: pd.DataFrame) -> pd.DataFrame:
    q = q.dropna(subset=["depreciation", "op_income"]).copy()
    q["dep_share_pre_dep_profit"] = q.depreciation / (q.op_income + q.depreciation)
    q["additions_over_dep"] = q.additions / q.depreciation
    q["dep_yoy"] = q.depreciation.pct_change(4)
    return q


def oracle_check(dep: pd.Series, path: str | None = None) -> dict:
    """Cross-check the fitted short-lived share against Oracle's 10-K PP&E by class:
    servers at six years on the average of opening and closing gross cost, as a share of
    depreciation in the same fiscal year (an approximation: ignores fully depreciated assets
    still in gross cost, which would push it up, and timing within the year)."""
    c = pd.read_csv(path or os.path.join(REPORTED, "ppe_classes.csv"))
    c = c[(c.company == "Oracle") & (c.item == "servers_network_gross")].set_index("date").value * 1e6
    avg = (c["2025-05-31"] + c["2026-05-31"]) / 2
    fy = dep[(dep.index > "2025-05-31") & (dep.index <= "2026-05-31")]
    assert len(fy) == 4
    return dict(avg_server_gross=avg, server_dep=avg / 6, dep_fy=fy.sum(), share=avg / 6 / fy.sum())


if __name__ == "__main__":
    lives = stated_lives()
    fits, panels = [], []
    for co in COS:
        r = company(co, lives)
        fits.append(r["fits"])
        q = quarterly_panel(r["quarterly"]); q["company"] = LABEL[co]
        panels.append(q[q.index >= "2023-01-01"])
    F = pd.concat(fits, ignore_index=True)
    Q = pd.concat(panels)
    os.makedirs("results", exist_ok=True)
    F.to_csv("results/depreciation_fits.csv", index=False)
    Q.to_csv("results/depreciation_quarterly.csv")
    B = lambda x: f"${x/1e9:,.1f}B"
    P = lambda x: "n/a" if x != x else f"{x:+.0%}" if abs(x) < 10 else "n/a"
    pd.set_option("display.width", 250)
    print("fit of the vintage model to reported depreciation (lags with RMSE < 10% are used):")
    print(F[["company", "life", "lag_q", "s", "rmse", "n_fit", "short_share_of_dep", "fits", "central"]]
          .round(3).to_string(index=False))
    G = F[F.fits]
    agg = lambda col, fmt: G.groupby("company", sort=False)[col].agg(
        lambda v: fmt(v.iloc[0]) if len(v) == 1 or fmt(v.min()) == fmt(v.max()) else f"{fmt(v.min())} to {fmt(v.max())}")
    C = F[F.central].set_index("company")
    print("\nCENTRAL (best-fitting lag); ranges over all fitting lags in brackets")
    t = pd.DataFrame({
        "as of": C.as_of, "op. income 4q": C.op_income_4q.map(B), "depreciation 4q": C.dep_4q.map(B),
        "next 4q if capex stops": C.dep_next4q_stop.map(B) + " (" + C.dep_growth_stop.map(P) + ")",
        "  range": agg("dep_growth_stop", P),
        "next 4q, capex flat": C.dep_next4q_flat.map(B) + " (" + C.dep_growth_flat.map(P) + ")",
        "  range ": agg("dep_growth_flat", P)})
    print(t.to_string())
    t = pd.DataFrame({
        "extra dep. at 4y": C.extra_dep_4y.map(B), "% op. income": C.extra_dep_4y_pct_oi.map(P),
        "  range": agg("extra_dep_4y_pct_oi", P),
        "extra dep. at 3y": C.extra_dep_3y.map(B), "% op. income ": C.extra_dep_3y_pct_oi.map(P),
        "  range ": agg("extra_dep_3y_pct_oi", P),
        "op. income 4q at 4y": C.op_income_4q_at_4y.map(B)})
    print("\nif servers lasted fewer years than stated (annual, at the latest quarter's fleet):")
    print(t.to_string())
    h = C.loc[["Microsoft", "Alphabet", "Amazon", "Meta", "Oracle"]]
    print(f"\nfive hyperscalers, depreciation next 4q at flat capex: {B(h.dep_next4q_flat.sum())} vs "
          f"{B(h.dep_4q.sum())} last 4q (+{B(h.dep_next4q_flat.sum() - h.dep_4q.sum())}, "
          f"{(h.dep_next4q_flat.sum() - h.dep_4q.sum()) / h.op_income_4q.sum():.0%} of their op. income)")
    oc = oracle_check(Q[Q.company == "Oracle"].depreciation)
    print(f"Oracle cross-check (10-K PP&E by class): servers averaged {B(oc['avg_server_gross'])} gross in "
          f"FY2026 -> {B(oc['server_dep'])} at six years = {oc['share']:.0%} of FY2026 depreciation "
          f"({B(oc['dep_fy'])}); model's short-lived share at the best-fitting lag: "
          f"{C.loc['Oracle'].short_share_of_dep:.0%}")
    g = Q.groupby("company", sort=False).apply(lambda d: pd.Series({
        "depreciation, 4q vs year before": d.depreciation.tail(4).sum() / d.depreciation.iloc[-8:-4].sum() - 1,
        "op. income, 4q vs year before": (d.op_income.tail(4).sum() / d.op_income.iloc[-8:-4].sum() - 1)
        if min(d.op_income.iloc[-8:-4].sum(), d.op_income.tail(4).sum()) > 0 else float("nan")}))
    print("\ngrowth, last four quarters vs the four before:")
    g.to_csv("results/depreciation_growth.csv")
    hq = Q[Q.company != "CoreWeave"].groupby("company").apply(lambda d: pd.Series({
        "dep_now": d.depreciation.tail(4).sum(), "dep_before": d.depreciation.iloc[-8:-4].sum(),
        "oi_now": d.op_income.tail(4).sum(), "oi_before": d.op_income.iloc[-8:-4].sum()})).sum()
    print(f"five hyperscalers, last 4q vs the 4 before: depreciation {B(hq.dep_before)} -> {B(hq.dep_now)} "
          f"(+{B(hq.dep_now - hq.dep_before)}, {hq.dep_now / hq.dep_before - 1:+.0%}); operating income "
          f"{B(hq.oi_before)} -> {B(hq.oi_now)} (+{B(hq.oi_now - hq.oi_before)}, {hq.oi_now / hq.oi_before - 1:+.0%})")
    print(g.map(lambda x: "n/a (no profit)" if x != x else f"{x:+.0%}").to_string())
    print("\ndepreciation as a share of operating profit before depreciation:")
    print(Q.pivot(columns="company", values="dep_share_pre_dep_profit").tail(8)
          .map(lambda x: "" if x != x else f"{x:.0%}").to_string())
    print("\nadditions (capex) / depreciation:")
    print(Q.pivot(columns="company", values="additions_over_dep").tail(4).round(1).to_string())
