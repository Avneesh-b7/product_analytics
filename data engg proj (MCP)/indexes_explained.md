# PostgreSQL Indexes — What They Are and How They Work

---

## The Problem Indexes Solve

A database table is stored on disk as a heap of pages — rows written in the order they arrived, with no particular sorting. To find rows matching `WHERE customer_id = 42`, Postgres has to open every page and check every row. This is a **Sequential Scan**.

```text
Page 1: [row customer_id=7] [row customer_id=201] [row customer_id=42] ...
Page 2: [row customer_id=88] [row customer_id=42] [row customer_id=3]  ...
Page 3: [row customer_id=42] [row customer_id=19] [row customer_id=56] ...
...
Page 78: [row customer_id=5] [row customer_id=42] [row customer_id=99] ...
```

With 10,000 rows across ~80 pages, Postgres reads all of them, keeps 7 matches, discards 9,993. An index solves this.

---

## What an Index Actually Is

An index is a **separate data structure on disk** that Postgres maintains alongside your table. The default type — B-tree — stores your indexed column values in a **sorted tree**, with each entry pointing back to the physical location of the matching row in the heap.

That physical location is called a **ctid** (tuple ID) — explained in the next section.

Here's what the index for `orders.customer_id` actually contains, pulled straight from our database:

```text
Index entry: customer_id=40  → ctid (19,13)   ← page 19, row 13 in the heap
Index entry: customer_id=40  → ctid (35,20)
Index entry: customer_id=40  → ctid (45,42)
Index entry: customer_id=41  → ctid (23,46)
Index entry: customer_id=41  → ctid (63,56)
Index entry: customer_id=42  → ctid (27,95)   ← one of our 7 target rows
Index entry: customer_id=42  → ctid (38,20)
Index entry: customer_id=42  → ctid (42,39)
Index entry: customer_id=42  → ctid (61,63)
Index entry: customer_id=42  → ctid (67,59)
Index entry: customer_id=42  → ctid (75,12)
Index entry: customer_id=43  → ctid (11,4)
...
```

The values are **sorted**, so Postgres can binary-search through the tree to find `customer_id = 42` in O(log n) steps instead of reading every row.

---

## What Is a ctid?

Every row in a Postgres table has a hidden system column called `ctid` — short for **tuple ID**. It is the physical address of that row on disk, expressed as:

```text
(block_number, tuple_offset)
  │               └── which slot within that page (1-based)
  └── which 8KB page on disk (0-based)
```

You can select it directly:

```sql
SELECT ctid, customer_id, order_id, total_amount
FROM app.orders
WHERE customer_id BETWEEN 40 AND 42
ORDER BY customer_id
LIMIT 10;
```

Real output from our database:

```text
  ctid   | customer_id | order_id | total_amount
---------+-------------+----------+--------------
 (19,13) |          40 |     3847 |       234.50
 (35,20) |          40 |     6201 |        89.99
 (45,42) |          40 |     8134 |       412.00
 (23,46) |          41 |     4512 |       178.25
 (63,56) |          41 |     9087 |        55.00
 (27,95) |          42 |     5234 |       310.75   ← page 27, slot 95
 (38,20) |          42 |     6890 |       145.00
 (42,39) |          42 |     7341 |       520.90
```

So `ctid (27,95)` means: open page 27 of the `orders` heap file, go to the 95th row slot on that page. That is the exact disk address Postgres jumps to when it uses an index.

**Why the row numbers look scattered** (`(19,13)`, `(35,20)`, `(45,42)`...) — rows for `customer_id=40` were inserted at different times, so they landed on whatever pages had space. The heap has no sorting. That's exactly the problem an index solves.

**ctid changes** when a row is `UPDATE`d (the old row becomes a dead tuple, a new row is written at a new location) or when `VACUUM FULL` rewrites the table. This is why indexes are maintained automatically — Postgres updates every index entry whenever a ctid changes.

---

## The B-tree Structure

A B-tree index is organised as a hierarchy of **pages** (typically 8KB each):

```text
                    [ Root page ]
                   /      |      \
          [Internal]  [Internal]  [Internal]
          /     \       /    \      /     \
      [Leaf]  [Leaf] [Leaf] [Leaf] [Leaf] [Leaf]
```

- **Root / Internal pages** — store separator keys that guide the search down the tree
- **Leaf pages** — store the actual index entries `(value → ctid)`

When you run `WHERE customer_id = 42`, Postgres:

1. Reads the root page — finds which branch contains values near 42
2. Reads one internal page — narrows it down further
3. Reads one leaf page — finds all entries where `customer_id = 42`
4. Returns the ctids: `(27,95), (38,20), (42,39), (61,63), (67,59), (75,12)` + one more
5. Fetches only those 7 rows from the heap

3–4 page reads total instead of 80.

---

## What Happens When You Run CREATE INDEX

```sql
CREATE INDEX idx_orders_customer_id ON app.orders (customer_id);
```

Postgres does this in sequence:

1. **Full table scan** — reads every row in `orders` to collect `(customer_id, ctid)` pairs
2. **Sort** — sorts all pairs by `customer_id`
3. **Build the tree** — writes sorted leaf pages, then builds internal pages on top
4. **Register** — writes the index to the system catalog so the planner knows it exists

From that point on, every `INSERT`, `UPDATE`, or `DELETE` on `orders` also updates the index — Postgres keeps it in sync automatically.

Without `CONCURRENTLY`, the table is locked during steps 1–3 (no reads or writes). With `CONCURRENTLY`, Postgres does two passes and lets other queries continue — it just takes a bit longer to build.

---

## The 4 Scan Types in EXPLAIN ANALYZE

### 1. Sequential Scan — no index

```sql
EXPLAIN ANALYZE
SELECT order_id, total_amount FROM app.orders WHERE customer_id = 42;
-- (run with the index dropped)
```

```text
Seq Scan on orders  (actual time=0.233..0.647 rows=7)
  Filter: (customer_id = 42)
  Rows Removed by Filter: 9993
Execution Time: 0.678 ms
```

Reads all 10,000 rows. Keeps 7.

---

### 2. Bitmap Index Scan — index exists, multiple rows match

This is what Postgres chose after we added `idx_orders_customer_id`:

```sql
EXPLAIN ANALYZE
SELECT order_id, total_amount, order_date FROM app.orders WHERE customer_id = 42;
```

```text
Bitmap Heap Scan on orders  (actual time=0.021..0.026 rows=7)
  Recheck Cond: (customer_id = 42)
  Heap Blocks: exact=7
  ->  Bitmap Index Scan on idx_orders_customer_id  (actual time=0.016 rows=7)
        Index Cond: (customer_id = 42)
Execution Time: 0.050 ms
```

**Two steps:**

- **Bitmap Index Scan** — walks the B-tree, collects all ctids that match, builds a bitmap of which heap pages to visit
- **Bitmap Heap Scan** — fetches only those heap pages (7 pages instead of 80)

Postgres uses this instead of a plain Index Scan when multiple rows match — batching the heap reads is more efficient than jumping back and forth.

---

### 3. Index Only Scan — all needed columns are in the index

When the query only asks for columns that are already stored in the index, Postgres never touches the heap at all.

```sql
-- idx_orders_customer_revenue covers: customer_id, region, total_amount, order_date
EXPLAIN ANALYZE
SELECT customer_id, region, total_amount, order_date
FROM app.orders WHERE customer_id = 42;
```

```text
Index Only Scan using idx_orders_customer_revenue on orders  (actual time=0.011..0.012 rows=7)
  Index Cond: (customer_id = 42)
  Heap Fetches: 0
Execution Time: 0.031 ms
```

`Heap Fetches: 0` — the heap was never read. Every answer came from the index itself.

Compare this to adding `status` (not in the index):

```sql
EXPLAIN ANALYZE
SELECT customer_id, region, total_amount, order_date, status
FROM app.orders WHERE customer_id = 42;
```

```text
Bitmap Heap Scan on orders  (actual time=0.011..0.025 rows=7)
  Heap Blocks: exact=7
  ->  Bitmap Index Scan on idx_orders_customer_revenue  (actual time=0.004 rows=7)
Execution Time: 0.031 ms
```

Adding `status` forces a heap visit — Postgres uses the index to find rows, then fetches `status` from the table.

---

### 4. Sequential Scan (by choice) — small table or low selectivity

Postgres does not always use an index even when one exists. If the planner estimates that a large % of rows will match (low selectivity), a Seq Scan is actually faster — reading pages sequentially is cheaper than random jumps through an index.

You saw this in the `orders JOIN customers` query: even with all indexes in place, Postgres chose a Hash Join + Seq Scan because it was aggregating _all_ customers, so scanning everything once was faster.

---

## The Numbers From Our Database

```text
Before index:  Seq Scan    → 10,000 rows read → Execution Time: 0.678 ms
After index:   Bitmap Scan →      7 rows read → Execution Time: 0.050 ms
Covering idx:  Index Only  →      0 heap reads → Execution Time: 0.031 ms
```

At 10k rows the gap is milliseconds. At 10 million rows the same ratios apply — the Seq Scan becomes seconds, the index stays sub-millisecond.

---

## Index Usage Stats — Is the Index Actually Being Used?

```sql
SELECT indexrelname AS index_name, idx_scan AS times_used,
       idx_tup_read AS tuples_read, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'app'
ORDER BY idx_scan DESC;
```

From our database right now:

```text
index_name                    times_used   tuples_read   size
orders_pkey                   30000        30000         240 kB   ← heavily used (FK lookups from order_items)
customers_pkey                10020        10020          64 kB
idx_orders_customer_id            2           22         136 kB   ← used in our EXPLAIN tests
idx_orders_customer_revenue       2           14         416 kB
idx_orders_status_active          0            0          72 kB   ← not yet triggered
idx_order_items_order_id          0            0         448 kB   ← no queries have joined yet
```

`times_used = 0` does not mean the index is useless — it means no queries have triggered it yet in this session. If an index stays at 0 over weeks of production traffic, that's when you consider dropping it.

---

## Types of Indexes We Used

### 1. B-tree (default)

Sorted tree. Works for `=`, `<`, `>`, `BETWEEN`, `IN`, `ORDER BY`.

```sql
CREATE INDEX idx_orders_customer_id ON app.orders (customer_id);
```

### 2. Partial Index

Only indexes rows matching a `WHERE` clause. The index is smaller and the planner can use it more aggressively.

```sql
CREATE INDEX idx_orders_status_active
    ON app.orders (status, order_date)
    WHERE status IN ('pending', 'processing');
```

This index contains only ~40% of the orders table rows (the active ones). Queries filtering for active orders get a smaller, faster index. Queries for all orders skip it.

### 3. Covering Index with INCLUDE

Stores extra columns in the leaf pages so heap fetches are avoided entirely.

```sql
CREATE INDEX idx_orders_customer_revenue
    ON app.orders (customer_id, region)
    INCLUDE (total_amount, order_date);
```

`customer_id` and `region` are the search keys (sorted in the tree). `total_amount` and `order_date` are just carried along in the leaf pages — not searchable, but available without a heap trip.

---

## Composite Indexes — Column Order Matters

```sql
CREATE INDEX idx_orders_status_date ON app.orders (status, order_date);
```

The index is sorted by `status` first, then by `order_date` within each status. Postgres can only use the index if the query touches columns **left to right**:

| Query                                                    | Uses index? | Why                                              |
| -------------------------------------------------------- | ----------- | ------------------------------------------------ |
| `WHERE status = 'pending'`                               | Yes         | Leftmost column                                  |
| `WHERE status = 'pending' AND order_date > '2024-01-01'` | Yes         | Both columns, left to right                      |
| `WHERE order_date > '2024-01-01'`                        | No          | Skips `status` — index is sorted by status first |

---

## Quick Reference — Indexes We Created

| Index                         | Table         | Column(s)             | Type            | Purpose                          |
| ----------------------------- | ------------- | --------------------- | --------------- | -------------------------------- |
| `idx_orders_customer_id`      | `orders`      | `customer_id`         | B-tree          | FK join to customers             |
| `idx_order_items_order_id`    | `order_items` | `order_id`            | B-tree          | FK join to orders                |
| `idx_order_items_product_id`  | `order_items` | `product_id`          | B-tree          | FK join to products              |
| `idx_orders_status_active`    | `orders`      | `status, order_date`  | Partial B-tree  | Filter active orders only        |
| `idx_orders_customer_revenue` | `orders`      | `customer_id, region` | Covering B-tree | Revenue rollup — Index Only Scan |

---

## How to Decide What to Index

This is the most practical question. There is no universal rule — you follow the queries, not the schema.

---

### Step 1 — Start with the query, not the table

An index only helps if a query actually uses it. Before creating anything, look at what queries run most often and what they filter on:

```sql
-- What columns appear in WHERE, JOIN ON, ORDER BY?
SELECT customer_id   -- not this
FROM app.orders
WHERE customer_id = 42        -- ← index candidate
  AND status = 'pending'      -- ← index candidate
ORDER BY order_date DESC;     -- ← index candidate
```

If a column is never in a `WHERE`, `JOIN ON`, or `ORDER BY`, an index on it is wasted space.

---

### Step 2 — Check selectivity (how many rows match)

Selectivity = how many rows a filter eliminates. High selectivity = few rows match = index is valuable.

```sql
-- How selective is customer_id?
SELECT customer_id, COUNT(*) as order_count
FROM app.orders
GROUP BY customer_id
ORDER BY order_count DESC
LIMIT 5;
```

```text
 customer_id | order_count
-------------+-------------
         512 |           9
          42 |           7
         178 |           7
```

Each `customer_id` matches ~5–9 out of 10,000 rows (~0.05% of the table). That is **very high selectivity** — an index is a clear win.

Contrast with a `status` column that only has 4 values (`pending`, `processing`, `completed`, `cancelled`). Each value matches ~25% of rows. Low selectivity — Postgres will often choose a Seq Scan anyway because the index doesn't eliminate enough rows to be worth the overhead.

**Rule of thumb:**

| Selectivity                    | Example                | Index useful?              |
| ------------------------------ | ---------------------- | -------------------------- |
| Very high (< 1% of rows match) | `customer_id = 42`     | Yes                        |
| Medium (1–10% match)           | `region = 'APAC'`      | Sometimes                  |
| Low (> 10% match)              | `status = 'completed'` | Rarely — use partial index |

---

### Step 3 — Single column vs composite

**Single column** — use when queries filter on one column in isolation:

```sql
WHERE customer_id = 42
```

```sql
CREATE INDEX idx_orders_customer_id ON app.orders (customer_id);
```

**Composite column** — use when queries regularly filter on multiple columns together. The most selective column goes first:

```sql
WHERE status = 'pending' AND region = 'APAC'
```

```sql
CREATE INDEX idx_orders_status_region ON app.orders (status, region);
```

The key question for composite indexes: **which column eliminates the most rows first?**

In our case `status` has 4 values (~2,500 rows each) and `region` has maybe 5 values (~2,000 rows each). Either could go first — but if you also run queries filtering on `status` alone, put `status` first so that single-column query can also use this index.

**The leftmost prefix rule:**

```text
Index on (status, region, order_date)

WHERE status = 'pending'                          → uses index  ✓
WHERE status = 'pending' AND region = 'APAC'      → uses index  ✓
WHERE status = 'pending' AND order_date > '2024'  → uses index  ✓
WHERE region = 'APAC'                             → does NOT use index  ✗
WHERE order_date > '2024'                         → does NOT use index  ✗
```

A composite index can serve multiple query shapes — as long as they all start from the leftmost column.

---

### Step 4 — Ask: can I make it partial?

If you nearly always filter for a specific subset, a partial index is smaller and faster than a full one:

```sql
-- If 90% of your queries are for active orders only:
CREATE INDEX idx_orders_active
    ON app.orders (customer_id, order_date)
    WHERE status IN ('pending', 'processing');
```

This index is ~40% the size of a full index on the same columns. Postgres can use it more aggressively.

Only do this if the `WHERE` in the index closely matches the `WHERE` in your actual queries.

---

### Step 5 — Ask: do I need INCLUDE (covering)?

If the same query also fetches a few extra columns beyond the filter, add them via `INCLUDE` to avoid heap fetches:

```sql
-- Query: WHERE customer_id = 42 → also needs total_amount and order_date
CREATE INDEX idx_orders_customer_revenue
    ON app.orders (customer_id, region)
    INCLUDE (total_amount, order_date);
```

Only include columns that are **selected**, not filtered on. Columns in `INCLUDE` are not searchable — they are just carried along for free reads.

---

### The Decision Flowchart

```text
Is this column in WHERE / JOIN ON / ORDER BY in frequent queries?
  └── No  → don't index it
  └── Yes → How selective is it?
              └── Very high (< 1% match) → single-column B-tree index
              └── Low (> 10% match)      → consider partial index with a tight WHERE
              └── Medium                 → depends; check EXPLAIN ANALYZE

Does the query filter on multiple columns together?
  └── Yes → composite index, most selective column first
  └── No  → single column

Does the query SELECT columns beyond the filter?
  └── Yes, and it's a hot query → add them via INCLUDE (covering index)
  └── No  → plain index is fine

Is only a subset of rows ever queried?
  └── Yes → partial index with that WHERE condition
  └── No  → full index
```

---

### Applied to Our Database

| Query pattern                                                          | Decision                              | Index created                                |
| ---------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------- |
| `JOIN orders ON customer_id`                                           | FK join, high selectivity             | `idx_orders_customer_id (customer_id)`       |
| `JOIN order_items ON order_id`                                         | FK join, high selectivity             | `idx_order_items_order_id (order_id)`        |
| `WHERE status IN ('pending','processing')`                             | Low selectivity but consistent subset | `idx_orders_status_active` (partial)         |
| Revenue rollup selects `customer_id, region, total_amount, order_date` | Avoid heap fetches                    | `idx_orders_customer_revenue` with `INCLUDE` |

---

## Useful Commands

```sql
-- List all indexes in the schema
SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE schemaname = 'app'
ORDER BY tablename;

-- Check usage stats
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'app'
ORDER BY idx_scan DESC;

-- Drop an index without locking the table
DROP INDEX CONCURRENTLY idx_orders_customer_id;
```
