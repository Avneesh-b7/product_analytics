# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Script

```bash
python event_data_agg.py
```

Requires: `pandas`, `numpy`, `sqlite3` (stdlib), `pyarrow` (for Parquet export).

## What This Is

A single-file lab (`event_data_agg.py`) for a product analytics course. It generates a synthetic 50k-row user event dataset in memory (no external data files), loads it into an in-memory SQLite database, and walks through three practice challenges:

1. **SQL dialect comparison** — write equivalent window function queries in ANSI-SQL and Spark-SQL (focus: window frame specification differences like `ROWS UNBOUNDED PRECEDING`)
2. **Pandas hourly aggregation** — `groupby('hour').agg({...})` with multiple metrics: session count, unique users, avg duration, most popular device
3. **Analytics pipeline function** — `create_analytics_pipeline()` stub that should aggregate, optimize dtypes, and export to Parquet

## Code Structure

- `create_sample_dataset()` — provided, generates the DataFrame; do not modify
- `setup_sql_database(df)` — provided, loads data into SQLite; do not modify
- `validate_results()` — provided, checks challenge completion; do not modify
- The three `# YOUR CODE HERE` sections are the student work areas

## Parquet Export Note

Challenge 3 requires exporting to Parquet. Install `pyarrow` if needed:
```bash
pip install pyarrow
```
