"""Data-free tests for the NVDA revenue reconstruction (src/nvda_valuation.py)."""
import json
import pandas as pd
import pytest

import nvda_valuation as nv


def _fact(start, end, val, filed, form="10-Q"):
    return dict(start=start, end=end, val=val, filed=filed, form=form)


def _write(tmp_path, facts, name="nvda_revenue.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"units": {"USD": facts}}))
    return str(p)


def test_q4_is_derived_and_dated_by_the_10k(tmp_path, monkeypatch):
    monkeypatch.setattr(nv, "SUPPLEMENT_ANNUALS", [])
    monkeypatch.setattr(nv, "FIRST_FISCAL_START", pd.Timestamp("2015-01-01"))
    facts = [
        _fact("2015-02-02", "2015-05-03", 10, "2015-05-28"),
        _fact("2015-05-04", "2015-08-02", 20, "2015-08-27"),
        _fact("2015-08-03", "2015-11-01", 30, "2015-11-25"),
        _fact("2015-02-02", "2016-01-31", 100, "2016-03-01", "10-K"),
        # standalone Q4 first tagged a YEAR later, as a comparative: must not delay it
        _fact("2015-11-02", "2016-01-31", 40, "2017-02-28", "10-K"),
        _fact("2016-02-01", "2016-05-01", 50, "2016-05-26"),
    ]
    rev = nv.quarterly_revenue(_write(tmp_path, facts))
    q4 = rev[rev.period_end == pd.Timestamp("2016-01-31")].iloc[0]
    assert q4.value == 40
    assert q4.filed == pd.Timestamp("2016-03-01")          # knowable from the 10-K
    assert rev.value.rolling(4).sum().iloc[3] == 100       # TTM == annual


def test_late_comparative_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(nv, "SUPPLEMENT_ANNUALS", [])
    monkeypatch.setattr(nv, "FIRST_FISCAL_START", pd.Timestamp("2015-01-01"))
    facts = [_fact("2015-02-02", "2015-05-03", 10, "2016-05-28")]   # filed a year late
    with pytest.raises(AssertionError, match="late or impossible filing date"):
        nv.quarterly_revenue(_write(tmp_path, facts))


def test_supplement_is_verified_against_the_asc606_file(tmp_path):
    good = [dict(start=s["start"], end=s["end"], val=s["val"], filed=s["filed"])
            for s in nv.SUPPLEMENT_ANNUALS]
    assert nv._verify_supplement(_write(tmp_path, good, "a.json"))
    bad = [dict(g, val=g["val"] + 1) if i == 0 else g for i, g in enumerate(good)]
    with pytest.raises(AssertionError, match="value mismatch"):
        nv._verify_supplement(_write(tmp_path, bad, "b.json"))
    assert nv._verify_supplement(str(tmp_path / "missing.json")) is False
