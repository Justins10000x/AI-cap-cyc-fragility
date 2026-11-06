"""
Every quantitative claim in results/RESULTS_v3.md that can be checked without
market data is enforced here. Run:  pytest -q   (about 1-2 minutes, 2 cores)

Tolerances were set from measured rates with sampling error in mind, not tuned
until green: e.g. a nominal-5% size test passes below 10%, never "below 5.1%".
"""
import math
import numpy as np
import pandas as pd
import pytest

from fast_psy import bsadf_fast, _min_obs_from_r0
from psy_bubble_detector import bsadf_sequence
from psy_v3 import (wild_paths, gaussian_null_bsadf, familywise_cv, pointwise_cv,
                    date_episodes, min_duration, episode_table, benjamini_hochberg)
from fundamentals import boom_vs_bubble_study, log_valuation


def _rw(rng, T, scale=None):
    e = rng.standard_normal(T - 1) * (1.0 if scale is None else scale)
    return np.concatenate([[0.0], np.cumsum(e)])


# ---------------------------------------------------------------- correctness
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_fast_bsadf_equals_reference_implementation(seed):
    rng = np.random.default_rng(seed); T = 120; y = _rw(rng, T)
    ref = bsadf_sequence(y, lags=0)
    fast = bsadf_fast(y, int(np.floor((0.01 + 1.8 / np.sqrt(T)) * T)) - 1)
    m = np.isfinite(ref) & np.isfinite(fast)
    assert m.sum() > 90
    assert np.max(np.abs(ref[m] - fast[m])) < 1e-10


def test_wild_paths_preserve_volatility_path_exactly():
    rng = np.random.default_rng(3)
    y = _rw(rng, 300, scale=np.where(np.arange(299) < 150, 1.0, 5.0))
    P = wild_paths(y, 50, seed=4)
    e = np.diff(y) - np.diff(y).mean()
    assert np.allclose(np.abs(np.diff(P, axis=1)), np.abs(e)[None, :])
    assert np.all(P[:, 0] == 0)


def test_min_duration_is_log_T():
    assert min_duration(922) == math.ceil(math.log(922)) == 7


def test_benjamini_hochberg_known_values():
    out = benjamini_hochberg({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.20})
    assert out["a"][1] == pytest.approx(0.04)
    assert out["b"][1] == pytest.approx(0.0533333, rel=1e-4)
    assert out["a"][2] and not out["d"][2]


# ------------------------------------------------------- size under the null
def test_gaussian_null_breaks_and_wild_bootstrap_holds_under_volatility_shift():
    """The v2 defect as a regression test: a late 5x volatility increase, no bubble."""
    T, M = 250, 300; mo = _min_obs_from_r0(T); rng = np.random.default_rng(7)
    cv_g = np.quantile(np.nanmax(gaussian_null_bsadf(T, 600, seed=1), axis=1), .95)
    scale = np.where(np.arange(T - 1) < int(.8 * T), 1.0, 5.0)
    obs, boot = [], []
    for _ in range(M):
        y = _rw(rng, T, scale)
        obs.append(np.nanmax(bsadf_fast(y, mo)))
        b = wild_paths(y, 1, seed=int(rng.integers(1 << 31)))[0]      # warp-speed MC
        boot.append(np.nanmax(bsadf_fast(b, mo)))
    obs = np.array(obs)
    size_gauss = np.mean(obs > cv_g)
    size_wild = np.mean(obs > np.quantile(boot, .95))
    assert size_gauss > 0.30, size_gauss      # measured ~60%: v2 would cry "bubble"
    assert size_wild < 0.10, size_wild        # measured ~5%


def test_familywise_cv_controls_false_flags_per_window():
    T, W = 300, 52; mo = _min_obs_from_r0(T)
    cal = gaussian_null_bsadf(T, 500, seed=11)
    val = gaussian_null_bsadf(T, 500, seed=12)
    fw, pw = familywise_cv(cal, W), pointwise_cv(cal)
    rng = np.random.default_rng(13)
    starts = rng.integers(mo + 1, T - W, size=len(val))
    def rate(cv):
        return np.mean([np.any(v[s:s + W] > cv[s:s + W]) for v, s in zip(val, starts)])
    assert rate(fw) < 0.09                    # ~5% by design
    assert rate(pw) > 2 * rate(fw)            # pointwise dating has no such control


# ---------------------------------------------------------------------- power
def test_detects_planted_bubble():
    """Power at rho=1.04 over 50 obs. Measured (M=400): wild bootstrap ~71%, Gaussian
    null ~81%. The wild bootstrap pays ~10 points of power here -- it resamples the
    bubble's own large increments -- in exchange for fixing size (60% -> 5% under a
    volatility shift). Threshold guards against regression, not a target."""
    T, M = 250, 120; mo = _min_obs_from_r0(T); rng = np.random.default_rng(21)
    obs, boot = [], []
    for _ in range(M):
        y = np.zeros(T)
        for t in range(1, T):
            y[t] = (1.04 * y[t - 1] if 150 <= t < 200 else y[t - 1]) + rng.normal()
        obs.append(np.nanmax(bsadf_fast(y, mo)))
        boot.append(np.nanmax(bsadf_fast(wild_paths(y, 1, int(rng.integers(1 << 31)))[0], mo)))
    assert np.mean(np.array(obs) > np.quantile(boot, .95)) > 0.60


# ------------------------------------------------------ the fundamentals point
def test_price_test_cannot_tell_boom_from_bubble_but_ratio_test_can():
    r = boom_vs_bubble_study(M=120, seed=5)
    assert r["boom"]["price"] > 0.40          # price test calls an earnings boom a bubble
    assert r["boom"]["ratio"] < 0.05
    assert r["bubble"]["ratio"] > 0.90
    assert r["null"]["ratio"] < 0.10 and r["null"]["price"] < 0.12


def test_valuation_ratio_has_no_lookahead():
    q_end = pd.to_datetime(["2020-03-31", "2020-06-30", "2020-09-30", "2020-12-31", "2021-03-31"])
    filed = q_end + pd.Timedelta(days=45)
    fund = pd.DataFrame({"period_end": q_end, "filed": filed, "value": [1., 1., 1., 1., 2.]})
    idx = pd.date_range("2020-01-03", "2021-12-31", freq="W-FRI")
    px = pd.Series(10.0, index=idx)
    lv = log_valuation(px, fund)
    assert lv.index.min() >= filed[3]                     # nothing before TTM is public
    assert np.allclose(lv[lv.index < filed[4]], np.log(10 / 4))
    assert np.allclose(lv[lv.index >= filed[4]], np.log(10 / 5))   # switch on FILING date


# ------------------------------------------------------------------ evaluation
def test_episode_table_on_known_path():
    idx = pd.date_range("2020-01-03", periods=40, freq="W-FRI")
    v = np.r_[np.ones(10), np.linspace(1, 3, 10), np.linspace(3, 1.5, 20)]
    px = pd.Series(v, index=idx)
    t = episode_table(px, [(10, 21, 22)])
    row = t.iloc[0]
    assert row["peak"] == idx[19].date()
    assert row["gain_detect_to_peak"] == pytest.approx(2.0)
    assert row["exit_lag_weeks"] == 3
    assert row["dd_peak_to_termination"] == pytest.approx(v[22] / 3 - 1)
