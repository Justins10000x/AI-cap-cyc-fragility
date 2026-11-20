"""Tests for src/rate_stress.py arithmetic."""
import math
import pytest
import rate_stress as rs


def test_shock_bounds_and_share_of_earnings():
    r = rs.stress(op_income=100e9, interest_run=4e9, debt=80e9, repriced=20e9, bp=75)
    assert r["extra_lo"] == pytest.approx(0.15e9) and r["extra_hi"] == pytest.approx(0.6e9)
    assert r["extra_lo_pct_op"] == pytest.approx(0.0015) and r["extra_hi_pct_op"] == pytest.approx(0.006)
    assert r["coverage_after_hi"] == pytest.approx(100 / 4.6)


def test_negative_earnings_give_no_share_rather_than_a_misleading_number():
    r = rs.stress(op_income=-0.2e9, interest_run=2.2e9, debt=35e9, repriced=27e9, bp=100)
    assert math.isnan(r["extra_lo_pct_op"]) and math.isnan(r["extra_hi_pct_op"])
    assert r["coverage_after_hi"] < 0
