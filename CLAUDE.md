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

**Read `k-means clustering/CLAUDE.md` before working in this folder** — it documents the dataset columns and requires all plots to use the repo's `dataviz` skill categorical palette (distinct hues per cluster), not a single-hue sequential palette.

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

The retention heatmap uses a single-hue sequential blue colormap (light→dark) per the repo's `dataviz` skill conventions, not the categorical palette used in the k-means lab — the heatmap encodes one continuous magnitude (retention %), not discrete cluster categories.

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

## E2E Project

An eighth lab in `e2e_project/` — end-to-end analysis on synthetic FitTrack data (10,000 users) combining clustering, cohort retention, and experimentation into one unified workflow.

### Notebooks

- `clustering.ipynb` — RFM segmentation pipeline
- `cohort.ipynb` — retention analysis using DuckDB SQL
- `experiment.ipynb` — A/B test analysis (complete)

### Data Files

`e2e_project/data/` is gitignored. Three files used:

- `user_behavior_data.csv` — 10,000 users with `user_id`, `signup_date`, `last_active_date`, `total_sessions`, `revenue`, `acquisition_channel`
- `users.csv` — `user_id`, `signup_date`, `acquisition_channel`
- `activity_log.csv` — `user_id`, `workout_logged_date` (one row per activity event)

### Clustering pipeline (`clustering.ipynb`)

1. Load data, fill null revenue with 0
2. Outlier detection via IQR on `total_sessions` and `revenue` — outliers separated into `high_sessions_df`, `high_revenue_df`, `overlap_df` (both); cleaned population goes into `df`
3. Build RFM: recency = days from `last_active_date` to reference date `2024-03-31`, frequency = `total_sessions`, monetary = `revenue`
4. Log-transform (`log1p`) all three features before scaling
5. StandardScaler on log-transformed features
6. Elbow method + silhouette score → K=6 chosen
7. KMeans(K=6) fitted on scaled features; labels assigned back to `rfm_df` then merged into `df`
8. Outlier groups labelled: `overlap_df` = "Champions", `high_sessions_df` = "Frequent Users", `high_revenue_df` = "High Monetary Value"
9. All groups stacked into `master_df`; numeric clusters mapped to names:
   - 0 → Active Free Users, 1 → At-Risk Paying Users, 2 → Dormant Free Users
   - 3 → Active Paying Users, 4 → Churned / Inactive, 5 → Lapsed High-Value Users

### Cohort pipeline (`cohort.ipynb`)

Uses DuckDB for all SQL analysis. Tables loaded via `duckdb.connect()` + `CREATE TABLE AS SELECT * FROM read_csv_auto(...)`. Retention metrics (N-day and rolling) computed entirely in SQL — no pandas transformation layer.

Pipeline steps:

1. Load `users.csv` and `activity_log.csv` into DuckDB as `users` and `activity` tables
2. Explore date ranges: `signup_date` spans 2024-01-01 – 2024-03-24; `workout_logged_date` spans 2024-01-08 – 2024-03-15 (snapshot cutoff)
3. Week-bucketing: use DuckDB `week(workout_logged_date)` to get ISO week number; compute `week_signup_cohortindex = week_of_activity - week_of_signup + 1` so week 1 = the user's signup week
4. Join activity weeks to users; users with no activity appear as NaN (`LEFT JOIN` produces nulls for inactive users)
5. **N-week retention by cohort**: % of cohort active in exactly week N — query → `nweek_retention` DataFrame → `retention_pct` (divide by total, replace 0 with NaN for unobservable weeks) → heatmap + retention curves
6. **N-week retention by channel × cohort**: same query with `acquisition_channel` added to `GROUP BY`; produces per-channel heatmaps (5 subplots) and comparison line/bar charts
7. **N-day retention (D1/D3/D7/D30) by channel**: uses `strftime(date, '%m-%d')` to strip year and match exact calendar day; `MAX(CASE WHEN d1_target = month_day THEN 1 ELSE 0 END)` per user; separate eligible denominators per metric (D1 cutoff = Mar 14, D3 = Mar 12, D7 = Mar 8, D30 = Feb 14); stored in `nday_channel_cohort`
8. **Rolling 2-week retention**: built via scaffold pattern — `CROSS JOIN` users × `week_spine([1..8])` → LEFT JOIN activity → flag `hit` if `relative_week IN (check_week, check_week+1)` → `MAX(hit)` per user × check_week. Observation window correction: eligible only if `cohort_week + check_week + 1 <= 11` (snapshot week). Built both by cohort (`rolling_retention`) and by channel × cohort (`rolling_channel`)
9. **Observation-window correction**: each metric needs its own eligible denominator — users too close to the snapshot cutoff are excluded from the denominator but their data still appears in the flagged table; correction only applies at aggregation time via `CASE WHEN cohort_week + N + window <= cutoff_week`
10. **Anomaly detection**: cohort 6 (Feb 5 week) shows depressed week-1 retention across ALL channels simultaneously → operational issue (bug/outage), not acquisition-quality problem
11. **Seasonality check**: weeks 5–6 uptick for cohort 1 maps to mid-February on the calendar and appears across all channels at the same calendar date but different relative weeks → platform-wide event, not cohort quality signal

### Experiment pipeline (`experiment.ipynb`)

Uses DuckDB for all analysis. `experiment_data.csv` loaded via `read_csv_auto()`; `conversion_date` renamed to `measurement_date` at load time via `CAST`.

Dataset: 10,000 users (5,000 per group), 21 days (Feb 1–21, 2024), 210,000 rows. One row per user × day with `converted` and `daily_activity_flag`.

**Metric definition:** daily activity-based conversion rate = `sum(converted) / sum(daily_activity_flag)`. Each active user-day is one observation. This aligns with the 7% historical baseline used in power analysis.

Pipeline steps:

1. **Data load**: DuckDB `CREATE TABLE experiment AS SELECT ... CAST(conversion_date AS DATE) AS measurement_date ...`
2. **Novelty effect check**: weekly CR by group using `week(measurement_date)`; grouped bar chart with per-week lift annotations. Week 1 treatment CR spikes ~3pp above stable weeks 2–3 → novelty effect confirmed
3. **Exposure balance (SRM check)**: `scipy.stats.chisquare` on group sizes vs expected 50/50; also checks date range and avg days active per group. Result: perfectly balanced, no SRM
4. **Power analysis (relative MDE)**: baseline 7%, scenarios 2%/5%/10% relative lift → required n = 526k/85k/22k per group. All exceed actual n (5,000) — underpowered for small relative effects
5. **Power analysis (absolute MDE)**: same baseline, scenarios +2pp/+5pp/+10pp → required n = 2,878/531/159 per group. All achievable with 5,000 users
6. **Z-test (post-novelty)**: filters to `measurement_date >= '2024-02-08'` (weeks 2–3 only); `proportions_ztest` two-tailed; 95% CI on difference via normal approximation. Result: Control 6.90%, Treatment 8.04%, lift +1.14pp, p ≈ 0, CI [+0.77pp, +1.51pp]
7. **Conclusion**: statistically significant (p < 0.001) but lift (+1.14pp) < MDE (+2pp absolute) and CI upper bound (+1.51pp) still below MDE → **Do Not Ship Yet**. Recommended actions: extend experiment 1–2 weeks, or revisit MDE threshold with stakeholders

## Funnel Analytics Project

A ninth project in `funnel_analytics/` — a marketing-to-customer conversion funnel built directly in BigQuery SQL (no notebook), analyzing the public `bigquery-public-data.ga4_obfuscated_sample_ecommerce` dataset (2020-11-01 to 2021-01-31, 92 days, 4.3M events, 270k users).

**Read `funnel_analytics/README.md` for the consolidated spec, build log, and results.** Per-phase detail also lives in `funnel_analytics/phase1_spec.md` (stage/attribution/window spec) and `funnel_analytics/phase4_5_join_and_validation.md` (join logic, the `TIMESTAMP_DIFF` day-rounding bug and its fix, and validation findings). `funnel_analytics/funnel_project_checklist.md` tracks phase-by-phase progress; `funnel_analytics/funnel_think.md` is informal working notes on stage selection and is gitignored.

Key design decisions:

- **Funnel stages**: `session_start` → `view_item` → `add_to_cart` → `begin_checkout` → `add_payment_info` → `purchase`. `add_shipping_info` is deliberately excluded as a near-duplicate of `begin_checkout` (~99.99% overlap).
- **Attribution**: strict first-touch, anchored to each user's true first `session_start` — never re-anchored to a later session.
- **Conversion window**: 30 days from first session, chosen from the days-to-purchase distribution (sits between p90=19 and p95=29 days).
- **Right-censoring fix**: only users whose first session occurred on or before 2021-01-01 are included, so every included user had the full 30-day window.
- **Join structure**: six stage CTEs each collapse to one row per user via `MIN(event_timestamp)`; `LEFT JOIN` (not `INNER JOIN`) preserves drop-off users as `NULL` rather than deleting them; the 30-day window is enforced inside each join's `ON` clause (not `WHERE`), which is what makes "dropped off" distinguishable from "converted but outside window."
- **Validation**: `chronology_status` and `missing_step` diagnostic fields flag out-of-order timestamps and the first missing stage per user; three investigated anomalies (784 users with checkout-before-cart ordering, 3,648 users missing `add_to_cart`, and a tracking-gap subset with `purchase` but no `add_to_cart`) are documented as caveats rather than corrected in the data.
- Query lives in `funnel_analytics/funnel_raw.sql`, parameterized via `DECLARE`d `CUTOFF_DATE` and `WINDOW_DAYS` variables. Also includes Phase 8 reshape queries — stage counts pivoted from wide to long format (one row per stage, with `pct_of_total_users` and `pct_of_prev_stage`), both overall and split by `channel_group` — for feeding a funnel chart.
- Remaining work: connect the Phase 8 queries to Looker Studio and build the funnel/channel-breakdown charts, then Phase 9 (generalizing the methodology to a B2B marketing-channel-to-lead funnel).

## Process Variance Detection Lab

A tenth lab in `process_var_detection/var_detection.ipynb` — statistical process control (SPC) applied to a synthetic **streaming session-depth** metric (`data/streamingtech_session_depth.csv`, 90 days, gitignored), to detect when a metric has genuinely shifted versus normal day-to-day noise.

Dataset columns: `day_index`, `date`, `day_of_week`, `session_depth`, `period` — `period` labels four consecutive phases: `baseline` (days 1–44), `degradation` (45–60), `recovery` (61–75), `final_stable` (76–90).

Key design decisions:

- **Control limits are computed from the `baseline` period only** (`baseline_df = df[df["period"] == "baseline"]`), then held fixed and applied across the full timeline — `mean_val`/`std_val`/`ucl`/`lcl` are never recalculated from the full dataset. Including later periods in the calculation would inflate σ and absorb the degradation into a widened "normal" range, defeating the point of the control chart. Baseline (n=44) checked for normality before trusting σ-based limits: within ±1σ = 68.2% vs. 68.3% theoretical, Shapiro-Wilk p=0.65 — close enough to normal to justify fixed 3σ limits.
- **Western Electric zones**: each side of the baseline mean is split into three 1σ bands (`classify_zone()` → `zone` column) — Zone C (±1σ, ordinary noise), Zone B (1–2σ), Zone A (2–3σ, still in control but worth watching), and "Beyond limits" (>3σ, i.e. past UCL/LCL).
- **Western Electric run rules 1–4** (`flag_consecutive_same_side()` → `rule1_flag`…`rule4_flag`, `any_rule_flag`): Rule 1 = single point beyond ±3σ; Rule 2 = 2 of 3 consecutive points in Zone A, same side; Rule 3 = 4 of 5 consecutive points in Zone B, same side; Rule 4 = 8 consecutive points on one side of the mean regardless of magnitude. Rules 5–8 (15-in-a-row-in-Zone-C, 6-in-a-row trending, 14-in-a-row alternating, 8-in-a-row-none-in-Zone-C) are documented but not implemented — the 90-day/4-period dataset is too short to trigger them meaningfully.
- **Result on this dataset**: only Rule 4 fires (first at day 60) — the degradation period's mean shift (4.46 → 4.13, ~0.44σ) never breaches any single-point or short-run threshold, so it's only caught by the 8-consecutive-same-side rule, with a ~15-day lag from when degradation actually starts (day 45). Flags persist a few days into `recovery` (days 61–64) since those points are still below the baseline mean.
- Charts follow the repo's `dataviz` skill conventions: points colored by `period` using the palette's categorical order (blue/orange/aqua/violet) with a distinct marker shape per period as a color-blind-safe secondary encoding (4 categories exceed the palette's 3-color all-pairs-validated cap for scatter/dot forms); zone bands shaded in neutral gray (not series-colored, to avoid conflating the background zones with period identity); dashed mean line + dotted UCL/LCL lines, both labeled `", baseline"` to make clear the *limits* come from baseline even on charts plotting the full timeline.
