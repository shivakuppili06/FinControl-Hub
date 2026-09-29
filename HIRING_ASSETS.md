# Hiring Assets

## 1. One-page project summary (CV Bullets)
- **Automated Finance Control Platform**: Architected a Python-based valuation, P&L variance, and reconciliation pipeline that reduces manual month-end control time from ~3 hours to <20 seconds.
- **Advanced Treasury Analytics**: Developed a daily liquidity tracking dashboard factoring in Basel III LCR rules and stress-testing for a 20% deposit outflow scenario, dynamically visualized via Streamlit.
- **Responsible AI & Anomaly Detection**: Integrated ML-based Isolation Forest for identifying suspicious valuation marks missed by static rules, and applied LLM-generated commentary with strict numeric-consistency guardrails to prevent hallucinations.

## 2. 60-Second Interview Pitch
"For my off-cycle internship application, I wanted to prove I can bring modern engineering to finance controls. I built 'FinControl Hub', an automated pipeline that replaces manual Excel work. It covers Independent Price Verification with both rule-based and ML anomaly detection, 3-way payments reconciliation with fuzzy matching, P&L variance analysis, and Treasury LCR stress testing. The whole system runs in seconds, logs an audit trail in SQLite, and serves the results on a Streamlit dashboard. It even uses an LLM to draft the executive summary, but includes a hard-coded numeric guardrail to ensure the AI never fabricates a financial figure. It’s fully CI/CD integrated with GitHub Actions and ready for Power BI."

## 3. Top 10 Interview Questions & Answers

**Q1: What would you change to run this on real SAP HANA / Databricks data?**
A: Instead of generating synthetic data and writing to SQLite, I would replace the data generation module with an ODBC connector (`pyodbc` or `databricks-sql-connector`) to pull directly from the warehouse views, or execute the SQL pushdown directly on the server to minimise data transfer.

**Q2: How does the ML Anomaly Detection work alongside rule-based limits?**
A: Rule-based limits (e.g. 20bps threshold for FX) are great for hard compliance but miss subtle, systemic pricing errors well within limits. I used an Isolation Forest to flag points that are statistically anomalous compared to the rest of the book's pricing diffs and quantities, providing a 'second line of defense'.

**Q3: How do you ensure the LLM commentary is safe for finance?**
A: It only reads aggregate statistics, so no position-level data leaves the firm. Also, a regex-based `numeric_consistency_check` acts as a guardrail, rejecting the AI output if it hallucinates any number not present in the original prompt.

**Q4: Why use a star schema for Power BI?**
A: It separates facts (exceptions, balances) from dimensions (desk, date, asset class), which allows Power BI to build a highly performant and interactive data model, enabling slicing across any attribute without duplicating data.

**Q5: How does your 3-way reconciliation work?**
A: It does an outer join across the PSP settlement file, Bank statement, and internal Ledger based on transaction references. Any missing sides or differences above a defined tolerance are flagged as breaks for investigation. 

**Q6: What is the LCR Stress Scenario testing?**
A: It tests the firm's liquidity buffer under a severe condition—a sudden 20% spike in 30-day outflows. It recalculates the net outflows and ensures the high-quality liquid assets (HQLA) stock is still sufficient to maintain a ratio above 1.0.

**Q7: How did you implement idempotency in your pipeline?**
A: The database generation and processing steps use `IF EXISTS REPLACE` patterns and timestamped audit logs. Running it multiple times on the same date will simply overwrite the reporting views without double-counting, while preserving the history of *when* it was run.

**Q8: Why is the config separated into a YAML file?**
A: In a production banking environment, thresholds (like IPV limits or LCR minimums) are owned by Risk or Finance, not developers. Putting them in a YAML file allows business users to review and update limits without altering the core Python codebase.

**Q9: How do you handle stale prices in your dataset?**
A: The multi-day simulation allows vendor prices to remain static while book marks shift, eventually triggering a valuation breach as the gap widens over the days.

**Q10: What did you learn about testing from this project?**
A: I learned to test for 'bad' behaviour just as much as 'good'. For example, I specifically wrote a test to prove the numeric consistency guardrail correctly catches an AI hallucinating a "120%" LCR when the input was 110%.

## 4. LinkedIn Post
Excited to share **FinControl Hub**, a portfolio project I built to automate Group Finance & Treasury controls! 🚀

I wanted to see how modern Python data engineering could transform traditional Excel-heavy month-end processes. The result is a pipeline that handles Independent Price Verification, 3-way Payments Reconciliation, P&L Variance, and Basel III LCR Stress Testing—cutting processing time from hours to seconds. 

Key features include:
✅ Config-driven rules with ML anomaly detection (Isolation Forest)
✅ An LLM-generated executive summary with strict numeric guardrails to prevent AI hallucinations
✅ CI/CD, unit testing, and a Streamlit dashboard

If you're in Finance Tech or Quantitative Risk, I’d love to hear your thoughts! Check out the architecture and code here: [GitHub link] #Finance #Python #DataEngineering #RiskManagement #Treasury
