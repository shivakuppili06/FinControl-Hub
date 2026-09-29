"""Dashboard:  streamlit run app.py"""
import streamlit as st
import sqlite3
from run_pipeline import run
import pandas as pd
from fincontrol import config as C

st.set_page_config(page_title="FinControl Hub", layout="wide")
st.title("FinControl Hub - Finance Controls & Treasury Dashboard")

@st.cache_data
def get_data():
    return run()

t, tsy, summary = get_data()

c1, c2, c3, c4 = st.columns(4)
c1.metric("LCR (Stress)", f"{tsy['lcr']:.0%} ({tsy['lcr_stress']:.0%})", "Compliant" if tsy["compliant"] else "BREACH")
c2.metric("IPV breaches", int(t["ipv"].breach.sum()))
c3.metric("Recon breaks", int((t["recon"].status != "Matched").sum()))
c4.metric("DQ exceptions", len(t["dq"]))

st.info(summary)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Valuation (IPV)", "Payments Recon", "P&L Variance", "Treasury", "Data Quality", "Run History"
])

with tab1:
    st.subheader("Independent Price Verification (ML + Rules)")
    desk_filter = st.selectbox("Filter Desk (IPV)", ["All"] + list(t["ipv"]["desk"].unique()))
    df_ipv = t["ipv"] if desk_filter == "All" else t["ipv"][t["ipv"]["desk"] == desk_filter]
    st.dataframe(df_ipv[df_ipv.breach | df_ipv.ml_anomaly])

with tab2:
    st.subheader("3-Way Payments Reconciliation")
    st.dataframe(t["recon"][t["recon"].status != "Matched"])

with tab3:
    st.subheader("Month-End P&L Variance")
    st.dataframe(t["pnl"])

with tab4:
    st.subheader("Liquidity Gap Ladder")
    st.bar_chart(t["liquidity_gap"].set_index("bucket")[["inflow", "outflow"]])

with tab5:
    st.subheader("Data Quality Exceptions")
    st.dataframe(t["dq"])

with tab6:
    st.subheader("Control Run History")
    con = sqlite3.connect(C.DB_PATH)
    try:
        history = pd.read_sql("SELECT * FROM control_log ORDER BY run_ts DESC", con)
        # pivot to have control types as columns
        if not history.empty:
            pivot_history = history.pivot(index="run_ts", columns="control", values="exceptions")
            st.line_chart(pivot_history)
            st.dataframe(history)
    except:
        st.write("No history available yet.")
    con.close()
