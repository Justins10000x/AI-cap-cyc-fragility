"""Data-free tests for src/circular_funding.py."""
import json
import numpy as np
import pandas as pd
import pytest

import circular_funding as cf


def _facts(tag_rows: dict) -> dict:
    return {tag: {"units": {"USD": rows}} for tag, rows in tag_rows.items()}


def F(end, val, filed, start=None):
    d = dict(end=end, val=val, filed=filed)
    if start: d["start"] = start
    return d


def test_quarterly_derives_quarters_from_year_to_date():
    s = "2025-01-27"
    f = _facts({"X": [F("2025-04-27", 10, "2025-05-28", s), F("2025-07-27", 25, "2025-08-27", s),
                      F("2025-10-26", 45, "2025-11-19", s), F("2026-01-25", 70, "2026-02-25", s)]})
    q = cf.quarterly(f, "X")
    assert list(q.values) == [10, 15, 20, 25]
    assert cf.reconcile(f, "X") == 1


def test_quarterly_prefers_direct_90_day_facts_and_does_not_double_count():
    s = "2025-01-27"
    f = _facts({"X": [F("2025-04-27", 10, "2025-05-28", s),
                      F("2025-07-27", 25, "2025-08-27", s), F("2025-07-27", 15, "2025-08-27", "2025-04-28")]})
    q = cf.quarterly(f, "X")
    assert list(q.values) == [10, 15]


def test_reconcile_raises_on_inconsistent_annual():
    # realistic dollar magnitudes: the check tolerates $1M of rounding, no more
    s, B = "2025-01-27", 1e9
    f = _facts({"X": [F("2025-04-27", 10 * B, "2025-05-28", s), F("2025-07-27", 25 * B, "2025-08-27", s),
                      F("2025-10-26", 45 * B, "2025-11-19", s), F("2026-01-25", 70 * B, "2026-02-25", s),
                      F("2026-01-25", 26 * B, "2026-02-25", "2025-10-27")]})   # direct Q4 off by $1B
    with pytest.raises(AssertionError, match="10-K says"):
        cf.reconcile(f, "X")
    ok = _facts({"X": f["X"]["units"]["USD"][:4]})
    assert cf.reconcile(ok, "X") == 1


def test_instant_keeps_first_reported_value():
    f = _facts({"S": [F("2026-01-25", 100, "2026-02-25"), F("2026-01-25", 120, "2027-02-25")]})
    assert cf.instant(f, "S").loc["2026-01-25"] == 100


def test_missing_tags_are_not_zero(tmp_path):
    ends = ["2026-01-25", "2026-04-26"]
    us = _facts({"EquitySecuritiesWithoutReadilyDeterminableFairValueAmount":
                 [F(e, v, "2026-06-01") for e, v in zip(ends, [10e9, 20e9])]})
    p = tmp_path / "cf.json"; p.write_text(json.dumps({"facts": {"us-gaap": us}}))
    ttm = pd.Series([100e9, 100e9], index=pd.to_datetime(ends))
    out = cf.nvda_panel(str(p), ttm)
    assert out.listed_stakes.isna().all() and out.guarantee_max.isna().all()
    assert not out.exposure_complete.any()
    assert np.allclose(out.exposure_pct_ttm_revenue, [0.10, 0.20])   # known parts only, flagged


def test_reconcile_since_skips_old_restated_years():
    B = 1e9
    def year(s, ends, vals):
        return [F(e, v * B, "2099-01-01", s) for e, v in zip(ends, vals)]
    old = year("2015-01-01", ["2015-03-31", "2015-06-30", "2015-09-30", "2015-12-31"], [1, 2, 3, 4])
    old.append(F("2015-12-31", 5 * B, "2016-02-01", "2015-10-01"))        # restated Q4: breaks 2015
    new = year("2024-01-01", ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"], [1, 2, 3, 4])
    f = _facts({"X": old + new})
    with pytest.raises(AssertionError):
        cf.reconcile(f, "X")
    assert cf.reconcile(f, "X", since="2023-06-01") == 1


def test_calendar_quarter_maps_oracle_fiscal_ends():
    import hyperscalers as hs
    q = hs.calendar_quarter(pd.to_datetime(["2026-08-31", "2026-09-30", "2026-05-31"]))
    assert [str(x) for x in q] == ["2026Q3", "2026Q3", "2026Q2"]
