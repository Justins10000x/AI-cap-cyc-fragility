"""Tests for src/watchlist.py trigger logic (synthetic data)."""
import pandas as pd
import watchlist as wl


def G(rows):
    return pd.DataFrame(rows, columns=["company", "period", "low_usd_bn", "high_usd_bn", "given_on"]).astype(
        {"low_usd_bn": str, "high_usd_bn": str})


def R(rows):
    return pd.DataFrame(rows, columns=["indicator", "date", "value"]).astype({"value": str})


BASE = [("crwv_cds_5y_bp", "2026-11-05", 1268), ("nvda_dso_days", "2026-10-25", 64),
        ("openai_round_valuation_usd_bn", "2026-03-31", 852), ("dram_next_quarter_price_change_low_pct", "2026-11", 5),
        ("tsmc_revenue_yoy_pct", "2026-10", 59.7), ("gpu_h100_usd_hr", "2026-11", 3.5), ("gpu_b200_usd_hr", "2026-11", 8.4)]


def status(e, code):
    return e.set_index("code").loc[code, "status"]


def test_guidance_cut_thresholds():
    g = G([("A", "CY2026", 200, 200, "2026-07-30"), ("A", "CY2026", 178, 178, "2026-10-29"),
           ("B", "CY2026", 100, 100, "2026-07-30"), ("B", "CY2026", 97, 97, "2026-10-28")])
    e = wl.evaluate(R(BASE), g)
    assert status(e, "T1b") == "TRIPPED"            # A cut 11%
    assert status(e, "T1c") == "TRIPPED"            # A and B both cut in Q4 2026


def test_small_single_cut_is_clear():
    g = G([("A", "CY2026", 175, 175, "2026-07-29"), ("A", "CY2026", 170, 170, "2026-10-28")])
    e = wl.evaluate(R(BASE), g)
    assert status(e, "T1b") == "clear" and status(e, "T1c") == "clear"


def test_next_year_below_this_year():
    g = G([("A", "CY2026", 200, 200, "2026-10-29"), ("A", "CY2027", 180, 190, "2027-01-29")])
    assert wl.next_year_below_this_year(g) == ["A: CY2027 185 < CY2026 200"]


def test_gpu_and_memory_composite():
    rows = BASE[:4] + [("tsmc_revenue_yoy_pct", "2026-10", 59.7)]
    for m, h in zip(["2026-08", "2026-09", "2026-10", "2026-11"], [4.0, 3.8, 3.5, 3.3]):
        rows += [("gpu_h100_usd_hr", m, h), ("gpu_b200_usd_hr", m, 8.0)]
    rows[3] = ("dram_next_quarter_price_change_low_pct", "2027-02", -3)
    e = wl.evaluate(R(rows), G([]))
    assert status(e, "T3") == "TRIPPED" and status(e, "T4") == "TRIPPED" and status(e, "C1") == "TRIPPED"


def test_backlog_two_declines_and_credit():
    rows = BASE + [("rpo_msft_usd_bn", d, v) for d, v in [("2026-03-31", 690), ("2026-06-30", 684), ("2026-09-30", 683)]]
    rows[0] = ("crwv_cds_5y_bp", "2026-12-01", 1600)
    e = wl.evaluate(R(rows), G([]))
    assert status(e, "T5") == "TRIPPED" and status(e, "T6") == "TRIPPED"


def test_numpy_booleans_still_trip():
    import numpy as np
    rows = BASE + [("crwv_interest_share", "2026-09-30", 0.31)]
    e = wl.evaluate(R(rows), G([]))
    assert status(e, "T9") == "TRIPPED"
    assert isinstance(np.float64(0.31) > 0.30, np.bool_)      # the case that broke "is True"


# ---- v1.1: E1 earnings squeeze
def E(vals):
    """vals: {company: [(quarter, op_income, depreciation), ...]} -> earnings panel."""
    rows = [dict(quarter=pd.Period(q, freq="Q"), company=c, op_income=o, depreciation=d)
            for c, xs in vals.items() for q, o, d in xs]
    return pd.DataFrame(rows)


FIVE = ("msft", "googl", "amzn", "meta", "orcl")


def test_e1a_trips_only_on_combined_fall_with_rising_depreciation():
    base = {c: [("2025Q4", 30, 5), ("2026Q4", 31, 7)] for c in FIVE}
    base["meta"] = [("2025Q4", 25, 5), ("2026Q4", 10, 7)]          # meta squeezed, combined still down
    e = wl.evaluate(R(BASE), G([]), E(base))
    assert status(e, "E1a") == "TRIPPED"                             # 145 -> 134, depreciation 25 -> 35
    assert status(e, "E1b") == "clear"                               # only one company squeezed


def test_e1a_uses_only_quarters_all_five_reported_and_e1b_counts_breadth():
    v = {c: [("2025Q3", 30, 5), ("2026Q3", 33, 7), ("2025Q4", 30, 5)] for c in FIVE}
    v["meta"] += [("2026Q4", 20, 7)]; v["orcl"] += [("2026Q4", 25, 7)]   # only two have reported Q4
    s = wl.earnings_squeeze(E(v))
    assert s["full_quarter"] == "2026Q3" and s["e1a"] is False      # Q4 incomplete: not used for E1a
    assert s["breadth_quarter"] == "2026Q4" and sorted(s["squeezed"]) == ["meta", "orcl"] and s["e1b"]
    assert s["reported"] == 2


def test_e1_waits_without_data():
    e = wl.evaluate(R(BASE), G([]))
    assert status(e, "E1a") == "waiting for data" and status(e, "E1b") == "waiting for data"
