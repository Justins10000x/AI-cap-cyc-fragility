"""Tests for src/labs.py (data-free except the tracked reported/openai.csv)."""
import csv
import pytest
import labs


@pytest.fixture
def p():
    return labs.plan(labs.load())


def test_reported_totals_are_consistent(p):
    assert p["rev_cum"] - p["compute"] - p["other"] == pytest.approx(p["fcf"])


def test_inconsistent_reported_totals_are_rejected(tmp_path):
    rows = list(csv.DictReader(open(labs.os.path.join(labs.ROOT, "reported", "openai.csv"))))
    for r in rows:
        if r["item"] == "other_costs":
            r["value_usd_bn"] = "200"
    f = tmp_path / "bad.csv"
    with open(f, "w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    with pytest.raises(AssertionError, match="inconsistent"):
        labs.plan(labs.load(str(f)))


def test_cumulative_revenue_formula():
    assert labs.cum_revenue(36, 0.0) == pytest.approx(180)
    assert labs.cum_revenue(36, 1.0) == pytest.approx(36 * 31)


def test_implied_growth_reproduces_plan_revenue(p):
    g = labs.implied_constant_growth(p)
    assert labs.cum_revenue(p["rev_2026"], g) == pytest.approx(p["rev_cum"], rel=1e-6)


def test_on_plan_every_case_needs_the_same_money(p):
    for c in labs.CASES:
        assert labs.to_raise(p, p["rev_cum"], c) == pytest.approx(-p["fcf"] - p["raised"])


def test_flexible_costs_shrink_with_revenue_and_fixed_do_not(p):
    lo, hi = 300.0, 800.0
    assert labs.costs(p, lo, "fixed") == labs.costs(p, hi, "fixed")
    for c in ("other_flex", "half_flex"):
        assert labs.costs(p, lo, c) < labs.costs(p, hi, c)
    assert labs.compute_spent(p, lo, "half_flex") < p["compute"] == labs.compute_spent(p, lo, "fixed")


def test_funding_need_never_negative(p):
    assert labs.to_raise(p, 5000.0, "fixed") == 0.0


def test_2026_checkpoint(p):
    c = labs.checkpoint_2026(labs.load(), p)
    assert c["h1_actual"] == pytest.approx(12.4) and c["h2_needed"] == pytest.approx(23.6)
