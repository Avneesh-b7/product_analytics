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
