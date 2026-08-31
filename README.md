# What's Covered

1. **SQL Dialect Comparison** — Write equivalent window function queries in ANSI-SQL and Spark-SQL, focusing on how window frame specification differs between dialects (`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` in Spark vs. implicit frames in ANSI).
2. **Pandas Hourly Aggregation** — Aggregate event data by hour with multiple metrics: session count, unique users, average duration, and most popular device.
3. **Analytics Pipeline** — Build a `create_analytics_pipeline()` function that aggregates, optimizes data types for memory efficiency, and exports results to Parquet.
4. **K-Means Clustering** — Customer segmentation on the Online Retail II dataset: clean transaction data (drop cancellations, non-standard stock codes, null customer IDs, non-positive prices), engineer RFM features (recency, frequency, monetary value) per customer, and cluster with K-Means.
5. **Retention Cohort Analysis** — Time-based cohort retention on the Online Retail II dataset: derive each customer's acquisition cohort and cohort index (months since first purchase), then pivot into a retention triangle of active-customer counts and retention %.
6. **Hypothesis Testing** — A/B test analysis on the Kaggle `amirmotefaker/ab-testing-dataset` (control vs. test campaign, 30 days each). Tests CTR using a two-proportion z-test and a Welch's t-test on daily CTR values, including normality checks (success-failure condition, Q-Q plots), one-tailed hypothesis setup at α=0.10, and lift calculation.
7. **A/B Test — Conversion Rate** — End-to-end A/B test on a product page (Udacity dataset, 294k rows). Covers full experiment design upfront (hypothesis, MDE, sample size, test duration), two-proportion z-test (two-tailed, α=0.05), combined visualisation of p-value / rejection regions / 95% CI on a single z-distribution chart, and a structured four-step conclusion framework (significance → effect size → CI → Ship/No-Ship verdict).
8. **A/B Testing Practice** — Scenario-based practice notebook (`smart-ab_testing.ipynb`) covering the full 8-step pipeline across two scenarios (checkout page conversion rate, ad creative CTR). Includes one-tailed vs two-tailed decision logic, guardrail metrics, sample size calculation with manual formula + statsmodels, and a reusable 6-check Ship vs No-Ship checklist.
9. **E2E Project** — End-to-end analysis on synthetic FitTrack data combining clustering, cohort retention, and A/B testing. Covers outlier detection and segmentation, RFM feature engineering, K-Means segmentation (K=6 core clusters + 3 outlier segments: Champions, Frequent Users, High Monetary Value). Cohort analysis includes weekly retention heatmaps by cohort and channel, N-day exact-day retention (D1/D3/D7/D30), rolling 2-week retention by cohort and channel, observation window correction, anomaly detection (isolated cohort dip vs. platform-wide event), and seasonality analysis — all computed in DuckDB SQL with no pandas transformation layer. Experiment analysis covers novelty effect detection (weekly CR chart), SRM check, power analysis (relative and absolute MDE scenarios), and a two-proportion z-test on activity-based daily CR (post-novelty window only); result: statistically significant lift (+1.14pp) but below the +2pp MDE threshold → Do Not Ship Yet.
10. **Funnel Analytics** — Marketing-to-customer conversion funnel built in BigQuery SQL on the public GA4 ecommerce sample dataset (92 days, 4.3M events, 270k users). Covers stage definition (`session_start` → `view_item` → `add_to_cart` → `begin_checkout` → `add_payment_info` → `purchase`), strict first-touch channel attribution, a 30-day conversion window with a right-censoring fix, a `LEFT JOIN`-based funnel build that preserves drop-off users, and a validation layer that surfaces and documents chronology anomalies and tracking gaps rather than silently correcting them.
11. **Process Variance Detection** — Statistical process control (SPC) on a synthetic streaming session-depth metric (90 days, 4 labeled periods: baseline/degradation/recovery/final_stable). Covers baseline-derived control limits (mean ± 3σ, held fixed and applied to the full timeline rather than recalculated), Western Electric zone classification (Zone C/B/A + beyond limits), and Western Electric run rules 1–4 (single-point breach, 2-of-3, 4-of-5, 8-in-a-row) implemented as consecutive-run flags to catch a moderate sustained shift that no single-point threshold check would detect.
12. **Correlation Analysis** — Correlation and activation-based risk segmentation on a synthetic GrowthTech SaaS dataset (1,200 users). Covers Pearson vs. Spearman coefficient choice (point-biserial for binary flags, Spearman as primary for right-skewed `total_sessions`), significance testing (p-values + 95% Fisher-z confidence intervals) paired with Cohen's effect-size thresholds so p-value isn't mistaken for importance at n=1,200, an unweighted composite `activation_score` (0–3) built from the activation steps that actually showed signal, and a two-signal (`activation_score` × `total_sessions`) rule-based High risk / Watch list / High potential segmentation validated against actual 30d/90d retention rates.

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
├── e2e_project/              # Lab 9: E2E clustering + cohort retention + experimentation
├── funnel_analytics/         # Lab 10: BigQuery SQL marketing-to-customer funnel
├── process_var_detection/    # Lab 11: SPC control chart + Western Electric rules
├── correl_analysis/          # Lab 12: correlation analysis + activation risk segmentation
├── requirements.txt
└── CLAUDE.md
```

Each lab folder has its own notes/docs alongside the notebook — see `k-means clustering/CLAUDE.md` and `retention_analysis/explainer.md` for the deeper walkthroughs, `data engg proj (MCP)/README.md` for the Postgres/dbt setup, and `funnel_analytics/README.md` for the funnel spec and build log.

## Key Dependencies

- `pandas`, `numpy` — data generation and aggregation
- `sqlite3` — in-memory SQL engine for dialect comparison
- `pyarrow` — Parquet export
- `plotly` — EDA visualizations
- `dbt-postgres` — SQL transformation layer for the data engg project
- `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl` — K-means clustering lab
- `statsmodels` — statistical testing in the Experimentation lab
- `kaggle` — downloads the Experimentation lab dataset
- `duckdb` — SQL queries on CSVs in the e2e cohort analysis
