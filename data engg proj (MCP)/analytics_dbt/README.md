# analytics_dbt

A dbt project that transforms raw e-commerce data in PostgreSQL into clean, tested analytics models.

---

## What is dbt?

dbt (data build tool) handles the **T** in ELT — it transforms data that's already loaded into your database using SQL `SELECT` statements. You write the logic; dbt handles materializing it as tables or views.

```
Raw data (app schema)
      ↓
   dbt models (SQL SELECT statements)
      ↓
Clean tables/views (dbt_dev schema)
      ↓
   Query / BI tool
```

dbt runs on your **local machine** and connects to the database over the network. Nothing runs inside the container except the SQL itself.

---

## What's Happening Here

### Source data
Raw tables live in the `app` schema inside the `analytics` Postgres database:

| Table | Rows | Description |
|---|---|---|
| `app.customers` | 2,000 | Customer profiles |
| `app.products` | 1,000 | Product catalog |
| `app.orders` | 10,000 | Order headers |
| `app.order_items` | 30,000 | Line items per order |

### dbt output
Transformed models land in the `dbt_dev` schema, separate from the raw data.

---

## Models

### `customer_analytics`
Joins all 4 source tables into a single customer-level view with:
- Order history (total orders, lifetime value, first/last order date)
- Avg order value
- Favorite product category (by spend)
- Days since registration + customer lifespan
- Segment label: `inactive`, `occasional`, `regular`, or `vip`

**CTE structure:**
```
app.customers + app.orders
        ↓
  customer_orders        ← order totals per customer

app.order_items + app.orders + app.products
        ↓
  product_preferences    ← spend per customer per category
        ↓
  top_category_per_customer  ← best category per customer (ROW_NUMBER)

customer_orders + top_category_per_customer
        ↓
  final SELECT           ← dbt_dev.customer_analytics
```

---

## Key Commands

```bash
# Activate the project virtualenv first
source .venv/bin/activate   # from repo root

# Test the database connection
dbt debug

# Build all models
dbt run

# Run a specific model only
dbt run --select customer_analytics

# Run all tests
dbt test

# Run tests for a specific model
dbt test --select customer_analytics

# Build + test in one shot
dbt build

# Generate documentation
dbt docs generate

# Serve docs locally (opens at http://localhost:8080)
dbt docs serve
```

---

## Project Structure

```
analytics_dbt/
├── models/
│   ├── customer_analytics.sql   # main model
│   └── schema.yml               # column descriptions + tests
├── dbt_project.yml              # project config (name, paths, materializations)
└── .gitignore                   # excludes target/, logs/, dbt_packages/
```

---

## Tests Defined

| Test | Column | What it checks |
|---|---|---|
| `not_null` | `customer_id` | No missing IDs |
| `unique` | `customer_id` | One row per customer |
| `not_null` | `email` | Every customer has an email |
| `not_null` | `lifetime_value` | No null spend (inactive = 0, not null) |
| `not_null` | `total_orders` | Order count always present |
| `not_null` | `customer_segment` | Every customer has a segment |
| `accepted_values` | `customer_segment` | Only valid segment labels |

---

## Connection

Configured in `~/.dbt/profiles.yml` (not in the repo):

```yaml
analytics_dbt:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: <your_password>
      dbname: analytics
      schema: dbt_dev
```
