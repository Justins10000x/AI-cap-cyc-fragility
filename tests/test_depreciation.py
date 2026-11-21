"""Data-free tests for src/depreciation.py (the vintage straight-line model and its fit)."""
import numpy as np
import pandas as pd

import depreciation as dp


def test_straight_line_single_vintage():
    placed = np.zeros(40); placed[2] = 240.0
    d = dp.straight_line(placed, 6)
    assert d[:3].sum() == 0                      # starts the quarter after placement
    assert np.allclose(d[3:27], 10.0)            # 240 over 24 quarters
    assert np.allclose(d[27:], 0.0)              # fully depreciated, nothing after
    assert np.isclose(d.sum(), 240.0)


def test_steady_capex_depreciation_converges_to_capex():
    placed = np.full(60, 5.0)
    assert np.isclose(dp.straight_line(placed, 6)[-1], 5.0)


def test_lag_shifts_placement():
    add = np.array([0, 100.0, 0, 0, 0, 0, 0, 0])
    assert np.array_equal(dp.placed_in_service(add, 2), [0, 0, 0, 100.0, 0, 0, 0, 0])
    assert np.array_equal(dp.placed_in_service(add, 0), add)


def test_fit_recovers_known_share_and_prefers_true_lag():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2016-03-31", periods=44, freq="QE")
    add = pd.Series(np.exp(np.linspace(0, 2.5, 44)) * 10 + rng.uniform(0, 2, 44), index=idx)
    full, _ = dp.model(add.values, s=0.6, lag=1, life=6)
    dep = pd.Series(full, index=idx)
    res = {lag: dp.fit_share(add, dep, 6, lag, "2024-01-01") for lag in (0, 1, 2)}
    s, rmse, n = res[1]
    assert abs(s - 0.6) < 1e-9 and rmse < 1e-9 and n == 12
    assert min(res, key=lambda k: res[k][1]) == 1


def test_shorter_life_on_young_fleet_matches_closed_form():
    # every vintage younger than the new life: extra = short-lived depreciation * (L / L' - 1)
    add = np.r_[np.zeros(30), np.full(10, 100.0)]
    s, life = 0.7, 6
    p = dp.placed_in_service(add, 0)
    short_now = s * dp.straight_line(p, life)[-1]
    extra = s * (dp.straight_line(p, 4)[-1] - dp.straight_line(p, life)[-1])
    assert np.isclose(extra, short_now * (life / 4 - 1))


def test_locked_in_depreciation_grows_when_capex_stops_after_a_ramp():
    add = np.r_[np.full(20, 10.0), np.linspace(10, 50, 8), np.zeros(4)]
    full, _ = dp.model(add, s=0.8, lag=0, life=6)
    assert full[-4:].sum() > full[-8:-4].sum()   # spending already done keeps depreciation rising
