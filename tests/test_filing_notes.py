"""Data-free tests for src/filing_notes.py."""
import pytest
import filing_notes as fn


def test_to_text_flattens_tables_and_entities():
    raw = "<html><style>x{}</style><table><tr><td>Net&nbsp;additions</td><td>13,106</td><td>299</td></tr></table><p>A&amp;B</p></html>"
    t = fn.to_text(raw)
    assert "Net additions | 13,106 | 299 |" in t and "A&B" in t and "x{}" not in t


def test_extract_reads_values_and_fails_loudly_when_wording_changes():
    spec = {"g": (r"capped at a total of \$(\d+) billion", "USD bn", "guarantee")}
    assert fn.extract("guarantees, capped at a total of $105 billion, to", spec)["g"][0] == 105.0
    with pytest.raises(SystemExit, match="no longer matches"):
        fn.extract("guarantees of up to one hundred billion", spec)


def test_num_handles_commas_and_brackets():
    assert fn.num("12,323") == 12323.0 and fn.num("(121)") == -121.0
