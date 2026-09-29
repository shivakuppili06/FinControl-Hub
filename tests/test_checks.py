import pandas as pd
from fincontrol import checks, commentary

def test_recon_flags_break_and_missing():
    psp = pd.DataFrame({"ref": ["A", "B", "C"], "psp_amount": [100.0, 5000.0, 10.0]})
    bank = pd.DataFrame({"ref": ["A", "B"], "bank_amount": [100.0, 100.0]})
    ledger = pd.DataFrame({"ref": ["A", "B"], "ledger_amount": [100.0, 100.0]})
    s = checks.payments_recon(psp, bank, ledger).set_index("ref").status
    assert s["A"] == "Matched" and s["B"] == "Break" and s["C"] == "Missing side"

def test_ipv_threshold():
    d = pd.DataFrame({"position_id": ["1", "2"], "asset_class": ["FX", "FX"], "quantity": [10, 10],
                      "book_mark": [100.1, 101.0], "ind_price": [100.0, 100.0]})
    r = checks.valuation_control(d).set_index("position_id")
    assert not r.loc["1", "breach"] and r.loc["2", "breach"]

def test_lcr():
    h = pd.DataFrame({"level": ["L1"], "market_value": [200.0], "haircut": [0.0]})
    cf = pd.DataFrame({"bucket": ["0-7d", "8-30d"], "inflow": [100.0, 100.0], "outflow": [100.0, 100.0]})
    t = checks.treasury(h, cf)
    assert round(t["lcr"], 2) == 200 / 50 and t["compliant"]

def test_dq_finds_missing_and_duplicate():
    p = pd.DataFrame({"position_id": ["a", "a", "b"], "quantity": [1, 1, 1], "book_mark": [1.0, 1.0, None], "date": ["2026-09-01"]*3})
    assert set(checks.data_quality(p).issue) == {"Duplicate position_id", "Missing book mark"}

def test_guardrail_catches_fabricated_number():
    orig = "Valuation: 5 of 100 marks breach. LCR 110%."
    good = "5 out of 100 marks breached. LCR is 110."
    bad = "5 out of 100 marks breached. LCR is 120%."
    assert commentary.numeric_consistency_check(orig, good) is True
    assert commentary.numeric_consistency_check(orig, bad) is False
