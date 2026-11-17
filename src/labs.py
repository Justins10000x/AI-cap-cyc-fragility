"""
labs.py -- the demand end of the loop: can the AI labs pay for the compute everyone
else is building for them?  v1: OpenAI.

DATA GRADE. OpenAI is private. Every input here is a REPORTED figure (leaked
projections or press reports), recorded with its source in reported/openai.csv and
never mixed with SEC-filed data. This is a scenario tool, not a measurement.

WHAT IS MODELLED. Only five-year totals (2026-2030) were reported, not a year-by-year
path, so the model works on cumulative totals and does not invent annual figures:

  cumulative revenue R(g) = rev_2026 * sum_{k=0..4} (1+g)^k   (constant growth g, 2027-2030)
  costs under three assumptions about how much of the plan can be cut if revenue falls:
    fixed      all $1,118B of planned costs are spent regardless (compute is largely contracted)
    other_flex compute fixed; other costs scale with revenue
    half_flex  half of compute and all other costs scale with revenue
  funding still to raise by 2030 = max(0, costs - R - money already raised)

Outputs: results/labs_openai_scenarios.csv and a near-term checkpoint on 2026 revenue.
"""
from __future__ import annotations
import csv, os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = ("fixed", "other_flex", "half_flex")
CASE_LABEL = {"fixed": "all costs fixed", "other_flex": "compute fixed, other costs flex",
              "half_flex": "half of compute flexes too"}


def load(path=os.path.join(ROOT, "reported", "openai.csv")) -> dict:
    d = {}
    for r in csv.DictReader(open(path)):
        d[(r["item"], r["period"])] = float(r["value_usd_bn"])
    return d


def plan(d: dict) -> dict:
    p = dict(rev_2026=d[("revenue", "2026")], rev_2030=d[("revenue", "2030")],
             rev_cum=d[("revenue_cumulative", "2026-2030")],
             compute=d[("compute_and_infrastructure", "2026-2030")],
             other=d[("other_costs", "2026-2030")],
             fcf=d[("free_cash_flow_cumulative", "2026-2030")],
             raised=d[("funding_raised", "2026-03")])
    # the reported totals must agree with each other before they are used
    gap = p["rev_cum"] - p["compute"] - p["other"] - p["fcf"]
    assert abs(gap) < 1.0, f"reported totals inconsistent by ${gap:.1f}B"
    return p


def cum_revenue(rev_2026: float, g: float) -> float:
    return rev_2026 * sum((1 + g) ** k for k in range(5))


def rev_2030(rev_2026: float, g: float) -> float:
    return rev_2026 * (1 + g) ** 4


def costs(p: dict, R: float, case: str) -> float:
    s = R / p["rev_cum"]                       # revenue relative to plan
    if case == "fixed":
        return p["compute"] + p["other"]
    if case == "other_flex":
        return p["compute"] + p["other"] * s
    if case == "half_flex":
        return p["compute"] / 2 + p["compute"] / 2 * s + p["other"] * s
    raise ValueError(case)


def compute_spent(p: dict, R: float, case: str) -> float:
    """Compute and infrastructure actually bought: what OpenAI's suppliers receive."""
    s = R / p["rev_cum"]
    return p["compute"] if case in ("fixed", "other_flex") else p["compute"] / 2 * (1 + s)


def to_raise(p: dict, R: float, case: str) -> float:
    return max(0.0, costs(p, R, case) - R - p["raised"])


def implied_constant_growth(p: dict) -> float:
    """Constant 2027-30 growth that reproduces the plan's cumulative revenue."""
    lo, hi = 0.0, 3.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cum_revenue(p["rev_2026"], mid) < p["rev_cum"] else (lo, mid)
    return (lo + hi) / 2


def scenarios(p: dict, growths=(0.20, 0.30, 0.40, 0.50, 0.60, 0.70)) -> pd.DataFrame:
    g_plan = implied_constant_growth(p)
    rows = []
    for g in sorted(set(growths) | {round(g_plan, 4)}):
        R = cum_revenue(p["rev_2026"], g)
        row = dict(growth=g, is_plan=abs(g - g_plan) < 1e-3, rev_2030=rev_2030(p["rev_2026"], g),
                   rev_cum=R, rev_cum_pct_plan=R / p["rev_cum"])
        for c in CASES:
            row[f"burn_{c}"] = costs(p, R, c) - R
            row[f"to_raise_{c}"] = to_raise(p, R, c)
            row[f"compute_cut_{c}"] = p["compute"] - compute_spent(p, R, c)
        rows.append(row)
    return pd.DataFrame(rows)


def checkpoint_2026(d: dict, p: dict) -> dict:
    h1 = d[("revenue", "2026Q1")] + d[("revenue", "2026Q2")]
    h2_needed = p["rev_2026"] - h1
    return dict(h1_actual=h1, h2_needed=h2_needed, h2_vs_h1=h2_needed / h1)


if __name__ == "__main__":
    d = load(); p = plan(d)
    s = scenarios(p)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    s.to_csv(os.path.join(ROOT, "results", "labs_openai_scenarios.csv"), index=False)
    print(f"reported plan consistent: {p['rev_cum']:.0f} - {p['compute']:.0f} - {p['other']:.0f} = {p['fcf']:.0f}")
    print(f"constant growth reproducing $840B cumulative revenue: {implied_constant_growth(p):.0%} a year\n")
    out = pd.DataFrame({"growth 2027-30": s.growth.map(lambda x: f"{x:.0%}"),
                        "2030 revenue": s.rev_2030.map(lambda x: f"${x:,.0f}B"),
                        "5-yr revenue": s.rev_cum.map(lambda x: f"${x:,.0f}B"),
                        **{f"to raise: {CASE_LABEL[c]}": s[f"to_raise_{c}"].map(lambda x: f"${x:,.0f}B") for c in CASES}})
    print(out.to_string(index=False))
    print("\ncompute not bought vs the $856B plan, if half of compute flexes:",
          ", ".join(f"{g:.0%} growth -> ${v:,.0f}B" for g, v in zip(s.growth, s.compute_cut_half_flex)))
    c = checkpoint_2026(d, p)
    print(f"\n2026 checkpoint: H1 actual ${c['h1_actual']:.1f}B; the $36B plan needs ${c['h2_needed']:.1f}B in H2 "
          f"({c['h2_vs_h1']:.1f}x H1)")
