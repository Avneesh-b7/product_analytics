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

Key data-cleaning steps applied before clustering: drop cancelled invoices (`Invoice` starting with `C`), drop non-standard `StockCode` values (not 5-digit numeric + optional single letter), drop rows with null `Customer ID`, drop non-positive `Price`. RFM features (`monetary_value`, `frequency`, `recency`) are aggregated to one row per `Customer ID` from the cleaned transaction-level data.
