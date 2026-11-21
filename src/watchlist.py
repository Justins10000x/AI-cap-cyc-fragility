"""
watchlist.py -- the warning lights. Pre-registered thresholds for the signals that tend to move
before a capex downturn, evaluated against the latest readings.

THRESHOLDS WERE WRITTEN ON 21 NOVEMBER 2026, before the next readings of any indicator.
Do not edit them to fit later data; add a new, dated version instead.

Inputs: reported/capex_guidance.csv, reported/watchlist_readings.csv (each reading with its
source and grade), plus figures refreshed from SEC/FRED data in data/ when present.
Usage (repo root): python src/watchlist.py
"""
from __future__ import annotations
import csv, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("DATA_DIR", os.path.join(ROOT, "data"))
PREREGISTERED_ON = "2026-11-21"

GUIDANCE_CUT = -0.10          # T1b: a standing capex guidance midpoint cut by 10% or more
TSMC_YOY_FLOOR = 20.0         # T2: monthly revenue growth below +20% year on year...
TSMC_MONTHS = 2               # ...in two consecutive monthly reports
GPU_DROP = -0.15              # T3: H100 or B200 rate 15% or more below its level 3 months earlier
DRAM_FLOOR = 0.0              # T4: a forecast or reported quarterly DRAM contract price decline
RPO_DROP = -0.03              # T5: backlog down 3% or more in a quarter, or down two quarters running
CDS_CEILING, HY_CEILING = 1500.0, 5.0   # T6: CoreWeave 5y CDS (bp) / US high-yield spread (%)
DSO_CEILING = 75.0            # T7: Nvidia days sales outstanding
OPENAI_VALUATION = 852.0      # T8: a new OpenAI round below the March 2026 post-money ($bn)
CRWV_INTEREST_CEILING = 0.30  # T9: CoreWeave interest expense above 30% of quarterly revenue


def load_csv(path):
    return pd.DataFrame(list(csv.DictReader(open(path))))


def guidance_changes(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()
    g["mid"] = (g.low_usd_bn.astype(float) + g.high_usd_bn.astype(float)) / 2
    g = g.sort_values("given_on")
    rows = []
    for (co, per), x in g.groupby(["company", "period"]):
        if len(x) >= 2:
            a, b = x.iloc[-2], x.iloc[-1]
            rows.append(dict(company=co, period=per, prev=a["mid"], latest=b["mid"],
                             change=b["mid"] / a["mid"] - 1, given_on=b["given_on"]))
    return pd.DataFrame(rows, columns=["company", "period", "prev", "latest", "change", "given_on"])


def next_year_below_this_year(g: pd.DataFrame) -> list:
    """T1a: a company guides next year's capex below this year's."""
    g = g.copy(); g["mid"] = (g.low_usd_bn.astype(float) + g.high_usd_bn.astype(float)) / 2
    if g.empty:
        return []
    latest = g.sort_values("given_on").groupby(["company", "period"]).last().reset_index()
    out = []
    for co, x in latest.groupby("company"):
        yrs = {p: m for p, m in zip(x.period, x.mid)}
        for p, m in yrs.items():
            nxt = p[:-4] + str(int(p[-4:]) + 1)
            if nxt in yrs and yrs[nxt] < m:
                out.append(f"{co}: {nxt} {yrs[nxt]:.0f} < {p} {m:.0f}")
    return out


def series(r: pd.DataFrame, name: str) -> pd.Series:
    x = r[r.indicator == name]
    return pd.Series(x.value.astype(float).values, index=x.date.values).sort_index()


def refresh_filed(r: pd.DataFrame) -> pd.DataFrame:
    """Add readings computed from SEC company facts and FRED, if data/ is present."""
    import circular_funding as cf
    add = []
    for co in ("msft", "googl", "orcl", "crwv"):
        p = os.path.join(DATA, f"{co}_companyfacts.json")
        if os.path.exists(p):
            s = cf.instant(cf.load_facts(p), "RevenueRemainingPerformanceObligation")
            for d, v in s.tail(3).items():
                add.append(dict(indicator=f"rpo_{co}_usd_bn", date=str(d.date()), value=v / 1e9, unit="USD bn",
                                source="SEC company facts", grade="filed"))
    p = os.path.join(DATA, "crwv_companyfacts.json")
    if os.path.exists(p):
        f = cf.load_facts(p)
        i = cf.quarterly(f, "InterestExpenseDebt"); rv = cf.quarterly(f, "RevenueFromContractWithCustomerExcludingAssessedTax")
        d = i.index.intersection(rv.index)[-1]
        add.append(dict(indicator="crwv_interest_share", date=str(d.date()), value=i[d] / rv[d], unit="share",
                        source="SEC company facts", grade="filed"))
    p = os.path.join(DATA, "hy_spread.csv")
    if os.path.exists(p):
        h = pd.read_csv(p).dropna(); h = h[pd.to_numeric(h.iloc[:, 1], errors="coerce").notna()]
        add.append(dict(indicator="us_high_yield_spread_pct", date=str(h.iloc[-1, 0]), value=float(h.iloc[-1, 1]),
                        unit="%", source="FRED BAMLH0A0HYM2", grade="filed"))
    return pd.concat([r, pd.DataFrame(add)], ignore_index=True)


def evaluate(r: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    out = []
    def row(code, name, reading, threshold, tripped, note=""):
        # bool() matters: numpy's True is not Python's True, so "is True" would hide real trips
        status = "waiting for data" if tripped is None else ("TRIPPED" if bool(tripped) else "clear")
        out.append(dict(code=code, signal=name, latest=reading, threshold=threshold, status=status, note=note))

    ch = guidance_changes(g)
    cuts = ch[ch.change < 0]
    worst = ch.change.min() if len(ch) else None
    row("T1a", "capex guided down year on year", "no next-year figures yet", "any company", None if not len(g) else bool(next_year_below_this_year(g)),
        "first 2027 figures due on Jan/Feb calls")
    row("T1b", "standing capex guidance cut", f"worst change {worst:+.1%}" if worst is not None else "n/a", f"{GUIDANCE_CUT:.0%}",
        bool(worst is not None and worst <= GUIDANCE_CUT), "; ".join(f"{c.company} {c.change:+.1%}" for c in cuts.itertuples()))
    rounds = cuts.assign(q=pd.PeriodIndex(pd.to_datetime(cuts.given_on), freq="Q")).groupby("q").company.nunique() if len(cuts) else pd.Series(dtype=int)
    row("T1c", "two or more companies cut in the same round", f"{int(rounds.max()) if len(rounds) else 0} in a round", "2", bool(len(rounds) and rounds.max() >= 2))

    t = series(r, "tsmc_revenue_yoy_pct")
    row("T2", "TSMC monthly revenue growth", f"{t.iloc[-1]:+.1f}% ({t.index[-1]})" if len(t) else "n/a",
        f"< +{TSMC_YOY_FLOOR:.0f}% for {TSMC_MONTHS} months", None if len(t) < TSMC_MONTHS and not len(t) else bool(len(t) >= TSMC_MONTHS and (t.tail(TSMC_MONTHS) < TSMC_YOY_FLOOR).all()))

    gpu = []
    for name in ("gpu_h100_usd_hr", "gpu_b200_usd_hr"):
        s = series(r, name)
        if len(s) >= 4:
            gpu.append(s.iloc[-1] / s.iloc[-4] - 1)
    h, b = series(r, "gpu_h100_usd_hr"), series(r, "gpu_b200_usd_hr")
    gpu_trip = (min(gpu) <= GPU_DROP) if gpu else None
    row("T3", "GPU rental prices", f"H100 ${h.iloc[-1]:.2f}, B200 ${b.iloc[-1]:.2f} ({h.index[-1]})", f"{GPU_DROP:.0%} vs 3 months earlier",
        gpu_trip, "needs 4 monthly readings; Oct to Nov rose 7-8%")

    m = series(r, "dram_next_quarter_price_change_low_pct")
    dram_trip = bool(len(m) and m.iloc[-1] < DRAM_FLOOR)
    row("T4", "memory (DRAM) contract prices", f"next quarter {m.iloc[-1]:+.0f}% or more ({m.index[-1]})", "a forecast or actual decline",
        dram_trip, "increases narrowing through 2027 (TrendForce)")
    row("C1", "early warning: GPU rents AND memory prices falling", "", "T3 and T4 together",
        None if gpu_trip is None else bool(gpu_trip and dram_trip))

    rpo_notes, rpo_trip = [], False
    for co in ("msft", "googl", "orcl", "crwv"):
        s = series(r, f"rpo_{co}_usd_bn")
        if len(s) >= 2:
            c1 = s.iloc[-1] / s.iloc[-2] - 1
            two = len(s) >= 3 and s.iloc[-1] < s.iloc[-2] < s.iloc[-3]
            rpo_trip |= (c1 <= RPO_DROP) or two
            rpo_notes.append(f"{co.upper()} {c1:+.1%}")
    row("T5", "cloud backlog (remaining performance obligations)", ", ".join(rpo_notes) or "n/a", f"{RPO_DROP:.0%} in a quarter or 2 declines",
        rpo_trip if rpo_notes else None)

    cds, hy = series(r, "crwv_cds_5y_bp"), series(r, "us_high_yield_spread_pct")
    row("T6", "neocloud and broad credit", f"CoreWeave CDS {cds.iloc[-1]:.0f}bp; HY spread {hy.iloc[-1]:.2f}%" if len(hy) else f"CoreWeave CDS {cds.iloc[-1]:.0f}bp",
        f"> {CDS_CEILING:.0f}bp or > {HY_CEILING:.1f}%", bool(cds.iloc[-1] > CDS_CEILING or (len(hy) and hy.iloc[-1] > HY_CEILING)))
    d = series(r, "nvda_dso_days")
    row("T7", "Nvidia days to collect", f"{d.iloc[-1]:.0f} days ({d.index[-1]})", f"> {DSO_CEILING:.0f}", bool(d.iloc[-1] > DSO_CEILING))
    v = series(r, "openai_round_valuation_usd_bn")
    row("T8", "OpenAI funding", f"last round ${v.iloc[-1]:.0f}B ({v.index[-1]})", "down-round, failed raise, or 2026 revenue < $30B",
        bool(v.iloc[-1] < OPENAI_VALUATION), "2026 revenue not yet reported")
    ci = series(r, "crwv_interest_share")
    row("T9", "CoreWeave interest / revenue", f"{ci.iloc[-1]:.0%} ({ci.index[-1]})" if len(ci) else "n/a", f"> {CRWV_INTEREST_CEILING:.0%}",
        bool(ci.iloc[-1] > CRWV_INTEREST_CEILING) if len(ci) else None)
    return pd.DataFrame(out)


if __name__ == "__main__":
    r = load_csv(os.path.join(ROOT, "reported", "watchlist_readings.csv"))
    r = refresh_filed(r)
    g = load_csv(os.path.join(ROOT, "reported", "capex_guidance.csv"))
    e = evaluate(r, g)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    e.to_csv(os.path.join(ROOT, "results", "watchlist_status.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
    print(f"thresholds pre-registered {PREREGISTERED_ON}\n")
    print(e.to_string(index=False))
    print(f"\n{(e.status == 'TRIPPED').sum()} tripped, {(e.status == 'clear').sum()} clear, {(e.status == 'waiting for data').sum()} waiting")
