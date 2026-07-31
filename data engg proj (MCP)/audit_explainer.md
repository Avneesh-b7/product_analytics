# What Are We Measuring in the Performance Audit?

Each check in `db_audit.py` answers a specific question about whether PostgreSQL is doing unnecessary work.

---

## 1. Table Sizes & Row Counts

Just a baseline — how big are the tables, how much of that is indexes vs actual data. Useful for knowing where to focus; a 30k-row table needs more attention than a 1k-row table.

---

## 2. Cache Hit Rate

PostgreSQL tries to serve data from RAM (the buffer cache) rather than reading from disk. The cache hit rate tells you what % of reads came from memory vs disk.

- **Below 95%** — too many disk reads; fix by increasing `shared_buffers` (more RAM for Postgres)
- **Above 95%** — healthy

Ours is ~99.9%, so no action needed.

---

## 3. Missing FK Indexes

When you join two tables (e.g. `orders JOIN customers ON customer_id`), Postgres needs to find matching rows quickly. Without an index on the join column, it reads *every row* in the table — called a **Sequential Scan (Seq Scan)**. An index lets it jump straight to the matching rows.

We had 3 FK columns with no index and added them all:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_id      ON app.orders (customer_id);
CREATE INDEX CONCURRENTLY idx_order_items_order_id    ON app.order_items (order_id);
CREATE INDEX CONCURRENTLY idx_order_items_product_id  ON app.order_items (product_id);
```

`CONCURRENTLY` means the index is built in the background without locking the table.

`db_audit.py`'s `RECOMMENDED_INDEXES` also defines two more targeted indexes beyond these FK indexes — a partial index (`idx_orders_status_active`) and a covering index (`idx_orders_customer_revenue`). Those aren't about missing FK coverage, so they're covered in `indexes_explainer.md` instead.

---

## 4. EXPLAIN ANALYZE

This is Postgres showing its work. Instead of just running a query, it tells you *how* it ran it:

- What **scan type** it used (Seq Scan vs Index Scan vs Index Only Scan)
- How long **each step** took
- How many **rows** it touched at each step

It's the primary tool for diagnosing a slow query. Example output:

```
Seq Scan on orders  (cost=0.00..180.00 rows=10000) (actual time=0.002..0.577)
```

At small scale (10k rows) a Seq Scan can still be fast. At 10M+ rows the same query becomes a bottleneck.

---

## 5. Null Rates

A data quality check — if a column is 30% null it might indicate a pipeline bug, an optional field being misused, or data that was never populated. The audit flags any column where nulls exceed 5%.

---

## 6. Table Bloat (Dead Tuples)

Every time you `UPDATE` or `DELETE` a row in Postgres, the old version isn't immediately removed — it stays as a **dead tuple** until `VACUUM` cleans it up.

High bloat means:
- Wasted disk space
- Slower scans (Postgres skips over dead rows but still reads them)

`autovacuum` handles cleanup automatically. This check just confirms it's keeping up.

---

## Summary

| Check | Question it answers |
|---|---|
| Table sizes | Where should I focus first? |
| Cache hit rate | Is Postgres reading too much from disk? |
| Missing FK indexes | Are joins doing unnecessary full-table scans? |
| EXPLAIN ANALYZE | How is Postgres actually executing this query? |
| Null rates | Is the data complete and trustworthy? |
| Table bloat | Is autovacuum keeping up with deletes/updates? |
