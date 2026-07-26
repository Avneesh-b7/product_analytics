"""
PostgreSQL performance audit script for the analytics database (app schema).
Run: python db_audit.py
Requires: psycopg2-binary  ->  pip install psycopg2-binary
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

DSN = (
    f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)
SCHEMA = "app"
TABLES = ["customers", "orders", "order_items", "products"]

# Recommended indexes: (index_name, table, description, sql)
RECOMMENDED_INDEXES = [
    (
        "idx_orders_customer_id",
        "orders",
        "FK index on orders.customer_id — eliminates seq scan on customer joins",
        f"CREATE INDEX CONCURRENTLY idx_orders_customer_id ON {SCHEMA}.orders (customer_id);",
    ),
    (
        "idx_order_items_order_id",
        "order_items",
        "FK index on order_items.order_id — eliminates seq scan on order→items joins",
        f"CREATE INDEX CONCURRENTLY idx_order_items_order_id ON {SCHEMA}.order_items (order_id);",
    ),
    (
        "idx_order_items_product_id",
        "order_items",
        "FK index on order_items.product_id — eliminates seq scan on product→items joins",
        f"CREATE INDEX CONCURRENTLY idx_order_items_product_id ON {SCHEMA}.order_items (product_id);",
    ),
    (
        "idx_orders_status_active",
        "orders",
        "Partial index for active orders — faster status filters without scanning cancelled/completed rows",
        (
            f"CREATE INDEX CONCURRENTLY idx_orders_status_active ON {SCHEMA}.orders (status, order_date)\n"
            f"    WHERE status IN ('pending', 'processing');"
        ),
    ),
    (
        "idx_orders_customer_revenue",
        "orders",
        "Covering index for revenue rollups — enables index-only scans on customer/region aggregations",
        (
            f"CREATE INDEX CONCURRENTLY idx_orders_customer_revenue ON {SCHEMA}.orders (customer_id, region)\n"
            f"    INCLUDE (total_amount, order_date);"
        ),
    ),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def run(cur, sql):
    cur.execute(sql)
    return cur.fetchall()

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

def print_table(rows, headers):
    if not rows:
        print("  (no results)")
        return
    widths = [
        max(len(str(h)), max(len(str(r.get(h, "") if isinstance(r, dict) else r[i])) for r in rows))
        for i, h in enumerate(headers)
    ]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  " + "  ".join("─" * w for w in widths))
    for row in rows:
        vals = [row.get(h, "") if isinstance(row, dict) else row[i] for i, h in enumerate(headers)]
        print(fmt.format(*[str(v) for v in vals]))

# ── Audit checks (each returns findings for the summary) ───────────────────────

def check_table_sizes(cur):
    section("1. TABLE SIZES & ROW COUNTS")
    rows = run(cur, f"""
        SELECT
            relname                                                        AS table_name,
            n_live_tup                                                     AS row_count,
            pg_size_pretty(pg_total_relation_size('{SCHEMA}.' || relname)) AS total_size,
            pg_size_pretty(pg_relation_size('{SCHEMA}.' || relname))       AS table_size,
            pg_size_pretty(pg_indexes_size('{SCHEMA}.' || relname))        AS index_size
        FROM pg_stat_user_tables
        WHERE schemaname = '{SCHEMA}'
        ORDER BY n_live_tup DESC
    """)
    print_table(rows, ["table_name", "row_count", "total_size", "table_size", "index_size"])
    return rows


def check_cache_hit(cur):
    section("2. CACHE HIT RATE  (pg_stat_database)")
    rows = run(cur, """
        SELECT
            datname,
            blks_hit,
            blks_read,
            ROUND(blks_hit::numeric / NULLIF(blks_hit + blks_read, 0) * 100, 2) AS cache_hit_pct,
            xact_commit,
            xact_rollback
        FROM pg_stat_database
        WHERE datname = current_database()
    """)
    print_table(rows, ["datname", "blks_hit", "blks_read", "cache_hit_pct", "xact_commit", "xact_rollback"])
    hit_pct = float(rows[0]["cache_hit_pct"]) if rows else 0
    if hit_pct < 95:
        print(f"\n  ⚠  Cache hit rate {hit_pct}% is below 95% — consider increasing shared_buffers.")
    else:
        print(f"\n  ✓  Cache hit rate {hit_pct}% is healthy (>= 95%).")
    return hit_pct


def check_missing_fk_indexes(cur):
    section("3. MISSING INDEXES ON FOREIGN KEYS")
    rows = run(cur, f"""
        SELECT
            tc.table_name,
            kcu.column_name                                                     AS fk_column,
            ccu.table_name                                                      AS references,
            CASE WHEN ix.indexname IS NULL THEN 'MISSING' ELSE 'EXISTS' END    AS index_status
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        LEFT JOIN pg_indexes ix
            ON ix.tablename = tc.table_name
           AND ix.indexdef LIKE '%' || kcu.column_name || '%'
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = '{SCHEMA}'
        ORDER BY tc.table_name
    """)
    print_table(rows, ["table_name", "fk_column", "references", "index_status"])
    missing = [r for r in rows if r["index_status"] == "MISSING"]
    if missing:
        print(f"\n  ⚠  {len(missing)} FK column(s) without an index — see recommendations below.")
    else:
        print("\n  ✓  All FK columns are indexed.")
    return missing


def check_explain_analyze(cur):
    section("4. EXPLAIN ANALYZE — orders ⨝ customers (revenue by customer)")
    rows = run(cur, """
        EXPLAIN ANALYZE
        SELECT c.customer_id, c.country, c.tier,
               COUNT(o.order_id)    AS order_count,
               SUM(o.total_amount)  AS revenue
        FROM app.customers c
        JOIN app.orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.country, c.tier
        ORDER BY revenue DESC
        LIMIT 20
    """)
    scan_types = set()
    exec_time = None
    for r in rows:
        line = r["QUERY PLAN"]
        if any(k in line for k in ("Execution Time", "Planning Time", "Seq Scan", "Hash Join", "Index")):
            print(f"  {line}")
        if "Seq Scan" in line:
            scan_types.add("Seq Scan")
        if "Index Scan" in line or "Index Only Scan" in line:
            scan_types.add("Index Scan")
        if "Execution Time" in line:
            exec_time = line.strip()
    return scan_types, exec_time


def check_null_rates(cur):
    section("5. NULL RATES PER COLUMN")
    high_null_cols = []
    for tbl in TABLES:
        cols = run(cur, f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{SCHEMA}' AND table_name = '{tbl}'
            ORDER BY ordinal_position
        """)
        col_names = [c["column_name"] for c in cols]
        null_checks = ", ".join(
            f"ROUND(100.0 * SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS \"{c}\""
            for c in col_names
        )
        result = run(cur, f"SELECT {null_checks} FROM {SCHEMA}.{tbl}")
        if result:
            print(f"\n  {tbl}")
            for col, pct in result[0].items():
                flag = " ⚠" if float(pct) > 5 else ""
                print(f"    {col:<30} {pct:>6}% null{flag}")
                if float(pct) > 5:
                    high_null_cols.append((tbl, col, float(pct)))
    return high_null_cols


def check_bloat(cur):
    section("6. TABLE BLOAT (dead tuples)")
    rows = run(cur, f"""
        SELECT
            relname                                          AS table_name,
            n_live_tup                                       AS live_rows,
            n_dead_tup                                       AS dead_rows,
            ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
            last_autovacuum::date                            AS last_autovacuum
        FROM pg_stat_user_tables
        WHERE schemaname = '{SCHEMA}'
        ORDER BY n_dead_tup DESC
    """)
    print_table(rows, ["table_name", "live_rows", "dead_rows", "dead_pct", "last_autovacuum"])
    bloated = [r for r in rows if float(r["dead_pct"] or 0) > 10]
    return bloated


def check_existing_indexes(cur):
    rows = run(cur, f"""
        SELECT indexname FROM pg_indexes WHERE schemaname = '{SCHEMA}'
    """)
    return {r["indexname"] for r in rows}


# ── Dynamic recommendations ────────────────────────────────────────────────────

def print_recommendations(existing_indexes):
    missing = [(name, tbl, desc, sql) for name, tbl, desc, sql in RECOMMENDED_INDEXES
               if name not in existing_indexes]

    print("\n" + "═" * 60)
    print("  OPTIMIZATION RECOMMENDATIONS")
    print("═" * 60)

    if not missing:
        print("\n  ✓  All recommended indexes are already in place. No action needed.")
        return

    for i, (_, __, desc, sql) in enumerate(missing, 1):
        print(f"\n{i}. {desc.upper()}")
        print(f"\n   {sql}\n")


# ── Dynamic findings summary ───────────────────────────────────────────────────

def print_findings_summary(missing_fk, cache_hit_pct, scan_types, exec_time,
                            high_null_cols, bloated_tables, existing_indexes):
    section("FINDINGS SUMMARY")

    findings = []

    # FK indexes
    if missing_fk:
        cols = ", ".join(f"{r['table_name']}.{r['fk_column']}" for r in missing_fk)
        findings.append((f"Missing FK indexes: {cols}", "Seq scans on joins", "HIGH"))
    else:
        findings.append(("All FK columns indexed", "Joins can use index lookups", "OK"))

    # Recommended indexes not yet applied
    missing_recommended = [idx_name for idx_name, _, _, _ in RECOMMENDED_INDEXES if idx_name not in existing_indexes]
    if missing_recommended:
        findings.append((
            f"{len(missing_recommended)} recommended index(es) missing",
            "Suboptimal query plans possible",
            "MEDIUM",
        ))
    else:
        findings.append(("All recommended indexes applied", "Query plans fully optimized", "OK"))

    # Scan types from EXPLAIN ANALYZE
    if "Seq Scan" in scan_types and "Index Scan" not in scan_types:
        findings.append((
            f"Join query using Seq Scan ({exec_time or 'see above'})",
            "Expected at small scale; watch at >100k rows",
            "LOW",
        ))
    elif "Index Scan" in scan_types:
        findings.append(("Join query using Index Scan", "Planner is using indexes", "OK"))

    # Cache hit rate
    if cache_hit_pct < 95:
        findings.append((
            f"Cache hit rate {cache_hit_pct}%",
            "Too many disk reads — increase shared_buffers",
            "HIGH",
        ))
    else:
        findings.append((f"Cache hit rate {cache_hit_pct}%", "Healthy (>= 95%)", "OK"))

    # Null rates
    if high_null_cols:
        for tbl, col, pct in high_null_cols:
            findings.append((f"{tbl}.{col} has {pct}% nulls", "Possible data quality issue", "MEDIUM"))
    else:
        findings.append(("No high-null columns (> 5%)", "Data completeness is healthy", "OK"))

    # Bloat
    if bloated_tables:
        for r in bloated_tables:
            findings.append((
                f"{r['table_name']}: {r['dead_pct']}% dead tuples",
                "Run VACUUM to reclaim space",
                "MEDIUM",
            ))
    else:
        findings.append(("No table bloat detected", "Autovacuum is keeping up", "OK"))

    print()
    print(f"  {'Issue':<45}  {'Impact':<38}  {'Priority'}")
    print("  " + "─" * 45 + "  " + "─" * 38 + "  " + "─" * 8)
    for issue, impact, priority in findings:
        print(f"  {issue:<45}  {impact:<38}  {priority}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'═'*60}")
    print(f"  PostgreSQL Performance Audit — {SCHEMA} schema")
    print(f"  {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'═'*60}")

    with psycopg2.connect(DSN, cursor_factory=RealDictCursor) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            check_table_sizes(cur)
            cache_hit_pct   = check_cache_hit(cur)
            missing_fk      = check_missing_fk_indexes(cur)
            scan_types, exec_time = check_explain_analyze(cur)
            high_null_cols  = check_null_rates(cur)
            bloated_tables  = check_bloat(cur)
            existing_indexes = check_existing_indexes(cur)

    print_recommendations(existing_indexes)
    print_findings_summary(
        missing_fk, cache_hit_pct, scan_types, exec_time,
        high_null_cols, bloated_tables, existing_indexes,
    )


if __name__ == "__main__":
    main()
