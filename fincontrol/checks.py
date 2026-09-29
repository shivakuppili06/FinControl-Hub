"""Core controls: data quality, reconciliation, valuation (IPV), P&L variance, treasury."""
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from sklearn.ensemble import IsolationForest
from . import config as C

def data_quality(pos: pd.DataFrame) -> pd.DataFrame:
    """Row-level DQ exceptions on the raw positions extract."""
    out = []
    latest_date = pos['date'].max() if 'date' in pos.columns else None
    df = pos[pos['date'] == latest_date] if latest_date else pos
    
    for pid in df[df.duplicated("position_id", keep=False)].position_id.unique():
        out.append((pid, "Duplicate position_id"))
    for pid in df[df["book_mark"].isna()].position_id:
        out.append((pid, "Missing book mark"))
    for pid in df[df["quantity"] <= 0].position_id:
        out.append((pid, "Non-positive quantity"))
    return pd.DataFrame(out, columns=["position_id", "issue"])

def fuzzy_match(s1, s2):
    if pd.isna(s1) or pd.isna(s2): return 0
    return SequenceMatcher(None, str(s1), str(s2)).ratio()

def payments_recon(psp: pd.DataFrame, bank: pd.DataFrame, ledger: pd.DataFrame) -> pd.DataFrame:
    """3-way reconciliation (PSP vs Bank vs Ledger) with fuzzy matching."""
    m = psp.merge(bank, on="ref", how="outer").merge(ledger, on="ref", how="outer")
    m["status"] = "Matched"
    m.loc[m["psp_amount"].isna() | m["bank_amount"].isna() | m["ledger_amount"].isna(), "status"] = "Missing side"
    
    m["diff_bank"] = m["psp_amount"].fillna(0) - m["bank_amount"].fillna(0)
    m["diff_ledger"] = m["psp_amount"].fillna(0) - m["ledger_amount"].fillna(0)
    
    m.loc[(m["status"] == "Matched") & ((m["diff_bank"].abs() > 1.0) | (m["diff_ledger"].abs() > 1.0)), "status"] = "Break"
    return m

def valuation_control(df: pd.DataFrame) -> pd.DataFrame:
    """Independent price verification: book mark vs vendor price, per asset-class threshold."""
    d = df.dropna(subset=["book_mark", "ind_price"]).copy()
    d["diff_bps"] = ((d.book_mark - d.ind_price) / d.ind_price * 1e4).round(1)
    d["threshold_bps"] = d.asset_class.map(C.IPV_THRESHOLD_BPS)
    d["breach"] = d.diff_bps.abs() > d.threshold_bps
    d["proposed_adj"] = ((d.ind_price - d.book_mark) * d.quantity).where(d.breach, 0).round(0)
    
    if len(d) > 10:
        iso = IsolationForest(contamination=0.05, random_state=42)
        d["ml_anomaly"] = iso.fit_predict(d[["diff_bps", "quantity"]].fillna(0)) == -1
    else:
        d["ml_anomaly"] = False
        
    return d.sort_values("diff_bps", key=abs, ascending=False)

def pnl_variance(pnl: pd.DataFrame) -> pd.DataFrame:
    p = pnl.copy()
    p["var_abs"] = p.actual_pnl - p.prior_pnl
    p["var_pct"] = (p.var_abs / p.prior_pnl).round(4)
    p["needs_explanation"] = (p.var_pct.abs() > C.PNL_PCT_THRESHOLD) & (p.var_abs.abs() > C.PNL_ABS_THRESHOLD)
    return p

def treasury(hqla: pd.DataFrame, cf: pd.DataFrame) -> dict:
    """Simplified Basel III LCR + liquidity gap ladder + stress scenario."""
    stock = (hqla.market_value * (1 - hqla.haircut)).sum()
    c30 = cf[cf.bucket.isin(["0-7d", "8-30d"])]
    out30, in30 = c30.outflow.sum(), c30.inflow.sum()
    net = out30 - min(in30, C.INFLOW_CAP * out30)
    
    out30_stress = out30 * 1.2
    net_stress = out30_stress - min(in30, C.INFLOW_CAP * out30_stress)
    
    gap = cf.assign(net_gap=cf.inflow - cf.outflow, cumulative_gap=(cf.inflow - cf.outflow).cumsum())
    return {"hqla_stock": stock, "net_outflow_30d": net, "lcr": stock / net if net else float('inf'),
            "lcr_stress": stock / net_stress if net_stress else float('inf'),
            "compliant": (stock / net) >= C.LCR_MINIMUM if net else True, "gap_ladder": gap}
