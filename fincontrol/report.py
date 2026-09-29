"""Outputs: formatted Excel pack, Power BI-ready CSVs, and an audit log table."""
import os, sqlite3, datetime as dt, pandas as pd
from openpyxl.styles import PatternFill, Font

def write_all(tables: dict, summary: str, outdir="output"):
    os.makedirs(outdir, exist_ok=True)
    xl = os.path.join(outdir, "control_pack.xlsx")
    with pd.ExcelWriter(xl, engine="openpyxl") as w:
        pd.DataFrame({"Summary": summary.split("\n")}).to_excel(w, sheet_name="Summary", index=False)
        for name, df in tables.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
        red = PatternFill("solid", fgColor="F8CBAD")
        for ws in w.book.worksheets:
            for c in ws[1]: c.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(len(str(c.value or "")) for c in col) + 2)
        for sheet, col in [("ipv", "breach"), ("recon", "status"), ("pnl", "needs_explanation")]:
            ws = w.book[sheet]; idx = [c.value for c in ws[1]].index(col) + 1
            for row in ws.iter_rows(min_row=2):
                if row[idx - 1].value in (True, "Break", "Missing side"):
                    for c in row: c.fill = red
    pbi = os.path.join(outdir, "powerbi"); os.makedirs(pbi, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(os.path.join(pbi, f"{name}.csv"), index=False)
    return xl

def audit_log(db_path, tables):
    """Governance: every run records what was checked and how many exceptions were found."""
    ex = {"dq": len(tables["dq"]), "ipv": int(tables["ipv"].breach.sum()),
          "recon": int((tables["recon"].status != "Matched").sum()),
          "pnl": int(tables["pnl"].needs_explanation.sum())}
    con = sqlite3.connect(db_path)
    pd.DataFrame([{"run_ts": dt.datetime.now().isoformat(timespec="seconds"), "control": k,
                   "exceptions": v} for k, v in ex.items()]).to_sql("control_log", con, if_exists="append", index=False)
    con.close()
    return ex
