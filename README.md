# Product Analytics Learning Lab

A hands-on lab from the course _Product Analytics Unlocked: From Metrics to Meaningful Insights_. It walks through core data aggregation techniques using a synthetic 50k-row user event dataset — no external data files required.

## What's Covered

1. **SQL Dialect Comparison** — Write equivalent window function queries in ANSI-SQL and Spark-SQL, focusing on how window frame specification differs between dialects (`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` in Spark vs. implicit frames in ANSI).
2. **Pandas Hourly Aggregation** — Aggregate event data by hour with multiple metrics: session count, unique users, average duration, and most popular device.
3. **Analytics Pipeline** — Build a `create_analytics_pipeline()` function that aggregates, optimizes data types for memory efficiency, and exports results to Parquet.
4. **K-Means Clustering** — Customer segmentation on the Online Retail II dataset: clean transaction data (drop cancellations, non-standard stock codes, null customer IDs, non-positive prices), engineer RFM features (recency, frequency, monetary value) per customer, and cluster with K-Means.

## Getting Started

```bash
pip install -r requirements.txt
jupyter notebook "event data aggregation/event_data_agg.ipynb"
```

## Project Structure

```
├── event data aggregation/
│   ├── event_data_agg.ipynb   # Primary working notebook
│   └── event_data_agg.py      # Script version (reference)
├── data engg proj (MCP)/
│   ├── demo_data.sql          # Synthetic e-commerce dataset (43k rows)
│   ├── schema_diagram.mmd     # Mermaid ER diagram
│   ├── docker_cheatsheet.md   # Docker CLI quick reference
│   ├── audit_explained.md     # PostgreSQL performance audit walkthrough
│   ├── indexes_explained.md   # Indexes explainer
│   ├── README.md              # Setup guide for the Postgres environment
│   └── analytics_dbt/        # dbt project for transforming e-commerce data
│       ├── models/
│       │   ├── customer_analytics.sql  # Customer-level analytics model
│       │   └── schema.yml             # Column descriptions and tests
│       └── dbt_project.yml
├── k-means clustering/
│   ├── kmeans_clustering.ipynb  # Customer segmentation notebook
│   └── CLAUDE.md                # Dataset notes + IBM Carbon color requirement for plots
├── requirements.txt
└── CLAUDE.md
```

## Key Dependencies

- `pandas`, `numpy` — data generation and aggregation
- `sqlite3` — in-memory SQL engine for dialect comparison
- `pyarrow` — Parquet export
- `plotly` — EDA visualizations
- `dbt-postgres` — SQL transformation layer for the data engg project
- `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl` — K-means clustering lab
