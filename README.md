## What's Covered

1. **SQL Dialect Comparison** — Write equivalent window function queries in ANSI-SQL and Spark-SQL, focusing on how window frame specification differs between dialects (`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` in Spark vs. implicit frames in ANSI).
2. **Pandas Hourly Aggregation** — Aggregate event data by hour with multiple metrics: session count, unique users, average duration, and most popular device.
3. **Analytics Pipeline** — Build a `create_analytics_pipeline()` function that aggregates, optimizes data types for memory efficiency, and exports results to Parquet.
4. **K-Means Clustering** — Customer segmentation on the Online Retail II dataset: clean transaction data (drop cancellations, non-standard stock codes, null customer IDs, non-positive prices), engineer RFM features (recency, frequency, monetary value) per customer, and cluster with K-Means.
5. **Retention Cohort Analysis** — Time-based cohort retention on the Online Retail II dataset: derive each customer's acquisition cohort and cohort index (months since first purchase), then pivot into a retention triangle of active-customer counts and retention %.
6. **A/B Testing** — Statistical testing on the Kaggle sales-and-satisfaction dataset, following a PLAN → RUN → EVALUATE → TAKE ACTION framework (hypothesis, sample size/power, lift, p-value, confidence interval).

## Getting Started

```bash
pip install -r requirements.txt
jupyter notebook "event data aggregation/event_data_agg.ipynb"
```

## Project Structure

```text
├── event data aggregation/   # Lab 1-3: SQL dialects, pandas aggregation, analytics pipeline
├── data engg proj (MCP)/     # Docker + Postgres + dbt data engineering project
├── k-means clustering/       # Lab 4: RFM feature engineering and customer segmentation
├── retention_analysis/       # Lab 5: cohort retention analysis and heatmap
├── Experimentation/          # Lab 6: A/B testing framework and statistical testing
├── requirements.txt
└── CLAUDE.md
```

Each lab folder has its own notes/docs alongside the notebook — see `k-means clustering/CLAUDE.md` and `retention_analysis/explainer.md` for the deeper walkthroughs, `Experimentation/ab_testing_explainer.md` for the A/B testing framework, and `data engg proj (MCP)/README.md` for the Postgres/dbt setup.

## Key Dependencies

- `pandas`, `numpy` — data generation and aggregation
- `sqlite3` — in-memory SQL engine for dialect comparison
- `pyarrow` — Parquet export
- `plotly` — EDA visualizations
- `dbt-postgres` — SQL transformation layer for the data engg project
- `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl` — K-means clustering lab
- `statsmodels` — statistical testing in the Experimentation lab
- `kaggle` — downloads the Experimentation lab dataset
