"""Data-free tests for src/returns.py."""
import json
import numpy as np
import pandas as pd

import returns as rt


def _q(n, start="2022-03-31"):
    return pd.date_range(start, periods=n, freq="QE")


def test_returns_panel_definitions():
    idx = _q(16)
    oi = pd.Series(10.0, index=idx); oi.iloc[12:] = 15.0               # profit steps up in year 4
    kv = np.array([100 + 10 * i + i * i for i in range(16)], dtype=float)  # capital accelerating
    p = rt.returns_panel(oi, pd.Series(kv, index=idx))
    last = p.iloc[-1]
    assert last.op_income_4q == 60
    assert np.isclose(last.capital_avg, kv[11:16].mean())
    assert np.isclose(last.return_on_capital, 60 / kv[11:16].mean())
    assert np.isclose(last.incremental_8q, (60 - 40) / (kv[15] - kv[7]))      # 8q change in profit / in capital
    assert np.isclose(last.incremental_8q_lag4, (60 - 40) / (kv[11] - kv[3]))  # capital lagged 4 quarters
    assert p.return_on_capital.iloc[:4].isna().all()                          # needs 4 quarters and 5 ends


def test_hurdle_test_arithmetic():
    r = rt.hurdle_test(capex_q=50, dep_next4q=60, op_income_growth_last=30, h=0.10)
    assert r["new_capital_next4q"] == 140 and np.isclose(r["oi_growth_needed"], 14) and np.isclose(r["cover"], 30 / 14)


def test_capital_prefers_combined_tag_and_falls_back(tmp_path):
    def F(end, val, filed): return dict(end=end, val=val, filed=filed)
    us = {rt.PPE_WITH_LEASES: {"units": {"USD": [F("2025-12-31", 120, "2026-02-01")]}},
          "PropertyPlantAndEquipmentNet": {"units": {"USD": [F("2024-12-31", 90, "2025-02-01"),
                                                             F("2025-12-31", 100, "2026-02-01")]}}}
    k = rt.capital(us, "meta")
    assert k.loc["2025-12-31"] == 120 and k.loc["2024-12-31"] == 90


def test_combined_needs_all_five():
    rows = []
    for c in ["Microsoft", "Alphabet", "Amazon", "Meta", "Oracle"]:
        for q in pd.period_range("2025Q1", "2026Q2", freq="Q"):
            if c == "Oracle" and q == pd.Period("2026Q2", "Q"):
                continue
            rows.append(dict(company=c, quarter=q, op_income_4q=10.0, capital=50.0))
    t = rt.combined(pd.DataFrame(rows))
    assert str(t.index.max()) == "2026Q1" and (t.op_income_4q == 50).all()
