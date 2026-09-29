# FinControl Hub
Automated **finance control & treasury analytics pipeline** - a production-grade portfolio project designed for Group Finance roles.

## Architecture
- **Data Layer**: Synthetic multi-day SQLite warehouse simulating real enterprise data (stale prices, FX, missing data).
- **Control Layer**: Python-based pipeline for DQ, 3-way Recon, IPV (Rules + ML), P&L Variance, and LCR Treasury.
- **Reporting Layer**: Streamlit interactive dashboard, Excel control pack with Data Lineage, and Power BI star schema CSVs.
- **AI Layer**: LLM-generated executive summary protected by deterministic numeric-consistency guardrails.

## Business Problem & Results
Manual month-end controls typically involve downloading massive CSVs, doing VLOOKUPs, and comparing limits—taking ~3 hours.
*Result*: FinControl Hub reduces this process to a <20-second automated run with full audit logging, anomaly detection, and interactive drill-downs.

## Features
1. **Realism**: 30-day dataset, FX conversions, stale-price scenarios, 3-way payments recon with tolerance.
2. **Treasury Depth**: Basel III LCR calculation with a 20% deposit outflow stress test scenario.
3. **Engineering Quality**: Config-driven rules (YAML), unit testing, CI/CD (GitHub Actions), idempotent runs, and SQL views.
4. **Responsible AI**: Isolation Forest for anomaly detection, and LLM text generation with a strict numeric guardrail.

## Run
```bash
pip install -r requirements.txt
python run_pipeline.py        # builds DB, runs controls, writes output/
streamlit run app.py          # interactive dashboard
pytest                        # unit tests
```

*Note: Data is 100% synthetic. No real bank data is used.*
