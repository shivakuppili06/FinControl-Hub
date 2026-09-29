"""Creates a synthetic SQLite 'finance warehouse' with realistically simulated data."""
import sqlite3, numpy as np, pandas as pd
from datetime import datetime, timedelta
from .config import DB_PATH
import os

def build(db_path=DB_PATH, seed=42):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    rng = np.random.default_rng(seed)
    n = 200
    days = 30
    
    # Generate multi-day positions
    base_date = datetime(2026, 9, 1)
    dates = [base_date + timedelta(days=i) for i in range(days) if (base_date + timedelta(days=i)).weekday() < 5]
    
    pos_data = []
    vp_data = []
    
    for d in dates:
        cls = rng.choice(["Equity", "Bond", "FX", "Derivative"], n)
        ind = rng.uniform(10, 500, n).round(4)
        book = ind * (1 + rng.normal(0, 0.0015, n))
        
        # Stale price scenario (vendor price doesn't change for a few days)
        # We can implement this simply by carrying over some prices if d > base_date
        
        bad = rng.choice(n, 10, replace=False) # injected mark breaks
        book[bad] *= 1 + rng.choice([-1, 1], 10) * rng.uniform(0.02, 0.06, 10)
        
        # FX conversion
        ccy = rng.choice(["USD", "EUR", "GBP", "JPY"], n)
        fx_rates = {"USD": 1.0, "EUR": 1.1, "GBP": 1.3, "JPY": 0.007}
        
        for i in range(n):
            pos_data.append({
                "date": d.strftime("%Y-%m-%d"),
                "position_id": f"P{i:04d}",
                "desk": rng.choice(["Rates", "Credit", "FX", "Equities", "Commodities", "Wealth"]),
                "asset_class": cls[i],
                "ccy": ccy[i],
                "quantity": rng.integers(100, 10_000),
                "book_mark": book[i],
                "fx_rate": fx_rates[ccy[i]]
            })
            vp_data.append({
                "date": d.strftime("%Y-%m-%d"),
                "position_id": f"P{i:04d}",
                "ind_price": ind[i]
            })

    pos = pd.DataFrame(pos_data)
    pos.loc[3, "book_mark"] = np.nan # DQ issue
    pos = pd.concat([pos, pos.iloc[[7]]]) # DQ issue
    
    vp = pd.DataFrame(vp_data)
    vp = vp.drop(index=[15, 16]) # DQ issue
    
    # Payments reconciliation (PSP vs bank vs ledger)
    psp = pd.DataFrame({
        "ref": [f"TXN{i:05d}" for i in range(100)],
        "psp_amount": rng.uniform(10, 5000, 100).round(2),
        "date": [dates[-1].strftime("%Y-%m-%d")] * 100
    })
    
    # Simulate some fuzzy matches and breaks
    bank = psp.copy().rename(columns={"psp_amount": "bank_amount"})
    bank.loc[5, "bank_amount"] += 0.05 # small tolerance
    bank.loc[10, "bank_amount"] += 100.0 # break
    bank.loc[15, "ref"] = "TXN00015-X" # fuzzy ref match
    
    ledger = psp.copy().rename(columns={"psp_amount": "ledger_amount"})
    ledger = ledger.drop(index=[20]) # missing in ledger
    
    # P&L Variance
    desks = ["Rates", "Credit", "FX", "Equities", "Commodities", "Wealth"]
    pnl = pd.DataFrame({
        "desk": desks,
        "prior_pnl": rng.uniform(2e5, 2e6, 6).round(0),
        "budget_pnl": rng.uniform(2e5, 2e6, 6).round(0),
        "price_driver": rng.normal(0, 50000, 6).round(0),
        "vol_driver": rng.normal(0, 20000, 6).round(0),
        "fx_driver": rng.normal(0, 10000, 6).round(0)
    })
    pnl["actual_pnl"] = pnl["prior_pnl"] + pnl["price_driver"] + pnl["vol_driver"] + pnl["fx_driver"]

    # Treasury
    hqla = pd.DataFrame({"level": ["L1", "L2A", "L2B"], "market_value": [4.2e9, 1.1e9, 0.4e9],
                         "haircut": [0.0, 0.15, 0.50]})
    cf = pd.DataFrame({"bucket": ["0-7d", "8-30d", "31-90d"],
                       "inflow": [0.9e9, 1.3e9, 2.0e9], "outflow": [2.6e9, 2.4e9, 3.1e9]})

    con = sqlite3.connect(db_path)
    for name, df in [("positions", pos), ("vendor_prices", vp), 
                     ("psp", psp), ("bank", bank), ("ledger", ledger), 
                     ("pnl", pnl), ("hqla", hqla), ("cashflows", cf)]:
        df.to_sql(name, con, if_exists="replace", index=False)
    con.close()
    return db_path
