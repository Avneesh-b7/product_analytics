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

Requires: `pandas`, `numpy`, `sqlite3` (stdlib), `pyarrow` (for Parquet export).

```bash
pip install pyarrow
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

## Notebook-Specific Notes

- The SQLite table is named `user_events`, not `events_data` — use the correct name in SQL queries or they will fail silently.
- `validate_results()` uses `locals()` in the original `.py` script, which works at module level. In the notebook, this must be `globals()` — the notebook copy has already been patched to use `globals()`.
- The ANSI-SQL query can actually execute against the SQLite connection; the Spark-SQL query is a string for comparison only.
