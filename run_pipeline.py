"""One command: generate data -> run controls -> commentary -> Excel/Power BI outputs."""
import sqlite3, pandas as pd
import logging
from fincontrol import config as C, checks, commentary, report
from fincontrol.generate_data import build

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run():
    logging.info("Starting pipeline")
    build()
    con = sqlite3.connect(C.DB_PATH)
    
    con.execute("DROP VIEW IF EXISTS v_valuation_join")
    con.execute("""
        CREATE VIEW v_valuation_join AS 
        SELECT p.date, p.position_id, p.desk, p.asset_class, p.quantity, p.book_mark, v.ind_price
        FROM positions p LEFT JOIN vendor_prices v USING (date, position_id)
        WHERE p.date = (SELECT MAX(date) FROM positions)
    """)
    
    raw = pd.read_sql("SELECT * FROM positions", con)
    ipv_in = pd.read_sql("SELECT * FROM v_valuation_join", con)
    
    psp = pd.read_sql("SELECT * FROM psp", con)
    bank = pd.read_sql("SELECT * FROM bank", con)
    ledger = pd.read_sql("SELECT * FROM ledger", con)
    
    pnl_raw = pd.read_sql("SELECT * FROM pnl", con)
    hq = pd.read_sql("SELECT * FROM hqla", con)
    cf = pd.read_sql("SELECT * FROM cashflows", con)
    con.close()
    
    dq = checks.data_quality(raw)
    ipv = checks.valuation_control(ipv_in)
    recon = checks.payments_recon(psp, bank, ledger)
    pnl = checks.pnl_variance(pnl_raw)
    tsy = checks.treasury(hq, cf)
    
    summary = commentary.ai_polish(commentary.build_summary(ipv, recon, pnl, tsy, dq), C.DB_PATH)
    tables = {"dq": dq, "ipv": ipv, "recon": recon, "pnl": pnl, "liquidity_gap": tsy["gap_ladder"]}
    xl = report.write_all(tables, summary)
    ex = report.audit_log(C.DB_PATH, tables)
    
    logging.info(f"Pipeline complete. Exceptions: {ex}")
    return tables, tsy, summary

if __name__ == "__main__":
    run()
