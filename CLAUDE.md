# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Lab

The lab exists in two forms — prefer the notebook for interactive work:

```bash
# Notebook (primary)
jupyter notebook "event data aggregation/event_data_agg.ipynb"

# Script (reference copy)
python "event data aggregation/event_data_agg.py"
```

Requires: `pandas`, `numpy`, `sqlite3` (stdlib), `pyarrow` (for Parquet export). The k-means lab additionally needs `scikit-learn`, `matplotlib`, `seaborn`, `openpyxl` (to read `.xlsx`).

```bash
pip install -r requirements.txt
```

## What This Is

A product analytics course lab (`event data aggregation/event_data_agg.ipynb` / `event data aggregation/event_data_agg.py`) that generates a synthetic 50k-row user event dataset in memory, loads it into an in-memory SQLite database (`user_events` table), and walks through three practice challenges:

1. **SQL dialect comparison** — write equivalent window function queries in ANSI-SQL and Spark-SQL; key difference is Spark requires explicit `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` where ANSI-SQL allows the frame to be implicit.
2. **Pandas hourly aggregation** — `groupby('hour').agg({...})` with session count, unique users, avg duration, most popular device.
3. **Analytics pipeline function** — `create_analytics_pipeline()` that aggregates, optimizes dtypes, exports to Parquet, and returns summary stats.

## Code Structure

These functions are provided and must not be modified (in the `.py` script):

- `create_sample_dataset()` — generates the DataFrame with columns: `user_id`, `timestamp`, `device_type`, `action_type`, `session_duration_minutes`
- `setup_sql_database(df)` — loads data into in-memory SQLite as table `user_events`
- `validate_results()` — checks challenge completion

The three `# YOUR CODE HERE` sections are the student work areas.

## Data Engineering Project (MCP)

A second lab in `data engg proj (MCP)/` focused on local data engineering with Docker and PostgreSQL.

### Setup

```bash
# Start the container
docker run -d --name pg-local \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=analytics \
  -p 5432:5432 postgres:16

# Load the dataset
docker exec -i pg-local psql -U postgres -d analytics < "data engg proj (MCP)/demo_data.sql"

# Connect
docker exec -it pg-local psql -U postgres -d analytics
```

### Users

- **postgres** — superuser, used for admin tasks
- **app** — read-only access to the `app` schema; created with:

```sql
CREATE USER app WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE analytics TO app;
GRANT USAGE ON SCHEMA app TO app;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO app;
```

### dbt

A dbt project lives in `data engg proj (MCP)/analytics_dbt/`. It uses the `.venv` in the repo root.

```bash
# Run all models
.venv/bin/dbt run

# Run a specific model
.venv/bin/dbt run --select customer_analytics

# Run tests
.venv/bin/dbt test --select customer_analytics

# Build + test in one shot
.venv/bin/dbt build
```

Connection config is in `~/.dbt/profiles.yml` (not in repo). Output lands in the `dbt_dev` schema.

Current models:

- `customer_analytics` — joins all 4 `app` tables into a customer-level view with LTV, segmentation, and favorite category

### Performance Audit

`data engg proj (MCP)/db_audit.py` (`python db_audit.py`, requires `psycopg2-binary` and a `.env` with `DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`/`DB_NAME`) checks table sizes, cache hit rate, and missing FK indexes on the `app` schema, and applies the recommended `CREATE INDEX CONCURRENTLY` statements. See `data engg proj (MCP)/audit_explainer.md` for what each check measures and `indexes_explainer.md` for the B-tree/ctid mechanics behind why the recommended indexes help.

### MCP Servers

Configured in `.claude/settings.json` (project-level, gitignored):

- **docker** — `docker/mcp-toolkit:latest` with Docker socket mounted
- **postgres** — `@modelcontextprotocol/server-postgres` connecting to `postgresql://postgres:password@localhost:5432/analytics`

### Dataset

Synthetic e-commerce data, 43,000 rows across 4 tables in the `app` schema:

- `app.customers` (2,000) — customer_id, email, registration_date, country, tier
- `app.products` (1,000) — product_id, name, category, price, stock_quantity
- `app.orders` (10,000) — order_id, customer_id, order_date, status, total_amount, region
- `app.order_items` (30,000) — item_id, order_id, product_id, quantity, price

## Notebook-Specific Notes

- The SQLite table is named `user_events`, not `events_data` — use the correct name in SQL queries or they will fail silently.
- `validate_results()` uses `locals()` in the original `.py` script, which works at module level. In the notebook, this must be `globals()` — the notebook copy has already been patched to use `globals()`.
- The ANSI-SQL query can actually execute against the SQLite connection; the Spark-SQL query is a string for comparison only.

## K-Means Clustering Lab

A third lab in `k-means clustering/kmeans_clustering.ipynb` — customer segmentation on the **Online Retail II** dataset (`online_retail_II.xlsx`, sheet `Year 2009-2010`).

**Read `k-means clustering/CLAUDE.md` before working in this folder** — it documents the dataset columns and requires all plots to use IBM Carbon Design Language colors (`https://www.ibm.com/design/language/color`), not the repo-wide dataviz defaults.

Key data-cleaning steps applied before clustering: drop cancelled invoices (`Invoice` starting with `C`), drop non-standard `StockCode` values (not 5-digit numeric + optional single letter), drop rows with null `Customer ID`, drop non-positive `Price`. RFM features (`monetary_value`, `frequency`, `recency`) are aggregated to one row per `Customer ID` from the cleaned transaction-level data, then split by IQR on `monetary_value` into `whale_customers_df`/`low_val_cust_df`/`customer_df` — only `customer_df` (the main population) is log-transformed and clustered.

**Read `k-means clustering/rfm_preprocessing_explainer.md` for the full preprocessing/clustering pipeline** — log-transform before scaling (and why), elbow method + silhouette score explained, and the reasoning behind the chosen K (currently K=4).

Recency in this lab is **raw days since last purchase**, not an inverted RFM score — low recency = bought recently = good. Business interpretation of the fitted K=4 clusters (segment names, revenue share, PM actions per segment) is documented in `k-means clustering/cluster_interpretation_explainer.md`.

The clustered customer-level RFM data (`all_combined`, with the `cluster` label column) is exported from this notebook to `k-means clustering/all_combined.pkl` via `to_pickle`/`read_pickle` — this is the mechanism for sharing that DataFrame with the retention analysis lab without re-running the clustering pipeline. `.pkl` files are gitignored, so this file must be regenerated locally by re-running the export cell if missing.

## Retention Analysis Lab

A fourth lab in `retention_analysis/retention_analytics.ipynb` — time-based cohort retention analysis on the **Online Retail II** dataset, reusing `k-means clustering/online_retail_II.xlsx` but reading sheet `Year 2010-2011`. The analysis is framed as if performed on 1 Jan 2012.

**Read `retention_analysis/explainer.md` for the full walkthrough** — cleaning steps, cohort date/index derivation, the retention pivot, and the heatmap code.

Cleaning steps before building cohorts: drop rows with null/zero `Customer ID`, filter to `Quantity > 0` and `Price > 0`, drop duplicate rows.

Cohort construction, all derived from `InvoiceDate`:

- `first_purchase_date` — per-customer min `InvoiceDate`, via `groupby('Customer ID')['InvoiceDate'].transform('min')`
- `cohort_date` — `first_purchase_date` truncated to the 1st of its month (the acquisition cohort)
- `cohort_year` / `cohort_month` — pulled from `first_purchase_date`, not re-derived from `cohort_date`
- `cohort_index` — months elapsed since acquisition: `(year - cohort_year) * 12 + (month - cohort_month) + 1`, so a customer's first active month is index `1`. This formula holds across multi-year spans without special-casing year boundaries.

The retention triangle is built by pivoting distinct customer counts — `groupby(['cohort_date', 'cohort_index'])['Customer ID'].nunique()` then `.pivot(index='cohort_date', columns='cohort_index', values='Customer ID')`. Column index `1` is each cohort's size; dividing every column by it (`cohort_pivot.divide(cohort_pivot.iloc[:, 0], axis=0) * 100`) gives retention %. The staircase of `NaN`s in the upper-right is structural, not missing data — later cohorts haven't had enough calendar time to reach higher cohort indices.

The retention heatmap uses a single-hue sequential blue colormap (light→dark) per the repo's `dataviz` skill conventions, not the IBM Carbon categorical palette used in the k-means lab — the heatmap encodes one continuous magnitude (retention %), not discrete cluster categories.

## Experimentation Lab (Hypothesis Testing)

A fifth lab in `Experimentation/hypothesis_testing1.0.ipynb` — A/B test analysis on the Kaggle **ab-testing-dataset** (`amirmotefaker/ab-testing-dataset`), comparing a control campaign vs. a test campaign across 30 days.

The dataset has two semicolon-delimited CSVs (`control_group.csv`, `test_group.csv`) and is loaded with `sep=";"`. Download it with:

```bash
kaggle datasets download -d amirmotefaker/ab-testing-dataset \
  -p "Experimentation/data/ab-testing-dataset" --unzip
```

Requires a Kaggle API token at `~/.kaggle/kaggle.json` (from Kaggle account settings → Create New Token). `Experimentation/data/` is gitignored — regenerate by rerunning the download cell if missing.

The lab tests CTR (clicks / impressions) using two approaches:

1. **Two-proportion z-test** — treats each impression as a Bernoulli trial; uses pooled proportion under H₀; normality checked via success-failure condition (n × p̂ > 10)
2. **Welch's t-test on daily CTR** — treats each of the 29 daily CTR values as one observation; accounts for day-to-day variance; normality checked via Q-Q plots

Both are one-tailed (H₁: CTR_test > CTR_control) at α = 0.10 (90% confidence). Derived metrics added to both DataFrames: CTR, Conversion Rate, Cost per Click, Cost per Purchase, Add-to-Cart Rate.

## A/B Test Lab (Conversion Rate)

A sixth lab in `Experimentation/a_b_test1.0.ipynb` — end-to-end A/B test on a product page conversion rate using the **Udacity A/B Testing dataset** (`ab_data.csv`, 294k rows).

Dataset lives at `Experimentation/data/ab_testing_dataset_new/ab_data.csv`. Columns: `user_id`, `timestamp`, `group` (control/treatment), `landing_page` (old_page/new_page), `converted`.

**Scenario:** baseline conversion rate 13%, team wants to detect a +2pp lift (target 15%).

**Cleaning steps:** drop mismatched group/page rows (control on new_page and vice versa), then deduplicate on `user_id` (keep first visit) → 290,584 clean rows.

**Experiment design (set upfront before any test):**

- H₀: CR_treatment = CR_control (two-tailed)
- α = 0.05, Power = 0.80, MDE = 2pp absolute
- Required sample size: 4,720 per group (computed via `NormalIndPower` + `proportion_effectsize`)
- Test duration check: at ~13,837 users/day the required sample is reached in under 1 day; dataset runs 21 days so sample is more than adequate

**Test:** two-proportion z-test (`proportions_ztest`, two-sided). Normality validated via success-failure condition (n × p̂ > 10). A random sample of 4,720 per group is drawn (simulating the point at which the test would have been called).

**Visualisation:** single combined plot — standard normal curve with rejection regions (red), p-value area (blue), observed z-statistic (dashed blue), critical z boundaries (dotted red), and a 95% CI bar (purple) plotted below the curve with difference-scale annotations.

**Conclusion framework:** four-step structured report — (1) statistical significance, (2) effect size and direction vs MDE, (3) CI check, (4) Ship / Do Not Ship verdict with three-line reason. Result for this dataset: p = 0.70, not significant, genuine null (sample was adequately powered).

## A/B Testing Practice Lab

A seventh lab in `Experimentation/smart-ab_testing.ipynb` — structured scenario-based practice for the full A/B test pipeline. No external dataset; results are provided as part of each scenario prompt.

**Scenario 1 — Checkout page conversion rate:** two-tailed two-proportion z-test, baseline 12%, 12% relative MDE (→ 1.44pp absolute), α=0.05, power=80%, 3,000 visitors/day 50/50 split. Result: p=0.033, significant, but lift (+1.09pp) fell short of MDE (+1.44pp) — Do Not Ship yet.

**Scenario 2 — Ad creative CTR:** one-tailed two-proportion z-test, baseline CTR 3%, 15% relative MDE (→ 0.45pp absolute), α=0.05, power=80%, 5,000 impressions/day per variant. Guardrail: CPC must not rise. Result: p=0.021, significant, but lift (+0.36pp) fell short of MDE (+0.45pp) and CI lower bound nearly zero — Do Not Ship yet.

**Scenario 3 — Streaming recommendation algorithm (ANOVA):** three-arm test (control vs collaborative filtering vs deep learning), metric is avg watch time per user per week (continuous, right-skewed). Test: one-way ANOVA on log-transformed data, followed by Tukey's HSD pairwise comparisons if H₀ rejected. Variance estimated from control arm in week 1 (no historical data). Novelty effect detected by tracking weekly trends per arm — arm C spiked week 1 then decayed below control by week 3. Result: B (collaborative filtering) ships, C (deep learning) does not.

**Scenario 4 — Meta ad targeting algorithm (feasibility):** one-tailed two-proportion z-test, baseline CTR assumed 2% (not given in prompt — typical for display ads), 12% relative MDE (→ +0.24pp absolute), α=0.05, power=80%. Traffic constraint: 2.5M impressions/day × 30% cap = 750k/day total, 375k per group. Max duration: 6 weeks (42 days) → 15.75M impressions per group budget. Includes three sensitivity tables — (1) vary α, (2) vary power, (3) vary relative MDE — each showing how sample size and test duration shift, with business justification for why each parameter moves n in its direction. MDE is the biggest lever: 5% MDE vs 20% MDE can differ by 10–20× in required sample size.

Each scenario follows an 8-step pipeline: hypotheses → MDE → sample size → duration → guardrails → run test → statistical test → interpret and conclude. Includes a reusable 6-check Ship vs No-Ship checklist (p-value, direction, lift vs MDE, CI excludes zero, CI lower vs MDE, guardrails).
