# Data Engineering Project — MCP + PostgreSQL Setup

A local PostgreSQL environment using Docker, loaded with a synthetic e-commerce dataset for analytics practice.

---

## Project Files

| File | Description |
|---|---|
| `demo_data.sql` | SQL dump with schema + 43,000 rows of e-commerce data |
| `schema_diagram.mmd` | Mermaid ER diagram of the database schema |
| `docker_cheatsheet.md` | Docker CLI quick reference |
| `README.md` | This file |

---

## Quick Start (clone → running database)

```bash
# 1. Clone the repo
git clone <repo-url>
cd "product_analytics_lrngs/data engg proj (MCP)"

# 2. Start the container
docker run -d \
  --name pg-local \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=analytics \
  -p 5432:5432 \
  postgres:16

# 3. Configure user and schema
docker exec -i pg-local psql -U postgres -d analytics <<'SQL'
CREATE USER app WITH PASSWORD 'app';
GRANT ALL PRIVILEGES ON DATABASE analytics TO app;
CREATE SCHEMA app AUTHORIZATION app;
GRANT ALL ON SCHEMA app TO app;
SQL

# 4. Load the data
docker exec -i pg-local psql -U postgres -d analytics < demo_data.sql

# 5. Connect and query
docker exec -it pg-local psql -U postgres -d analytics
```

That's it — you'll have 43,000 rows across 4 tables ready to query.

---

## Prerequisites

- Docker Desktop installed and running
- PostgreSQL client (`psql`) optional — you can exec into the container instead

---

## Setup

### 1. Create the PostgreSQL Container

```bash
docker run -d \
  --name pg-local \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=analytics \
  -p 5432:5432 \
  postgres:16
```

Verify it's running:

```bash
docker ps --filter name=pg-local
```

---

### 2. Configure the App User and Schema

Connect into the container and run:

```bash
docker exec -it pg-local psql -U postgres -d analytics
```

Then execute:

```sql
CREATE USER app WITH PASSWORD 'app';
GRANT ALL PRIVILEGES ON DATABASE analytics TO app;
CREATE SCHEMA app AUTHORIZATION app;
GRANT ALL ON SCHEMA app TO app;
```

---

### 3. Load the Demo Data

From the project folder:

```bash
docker exec -i pg-local psql -U postgres -d analytics < demo_data.sql
```

This creates 4 tables and inserts 43,000 rows:

| Table | Rows |
|---|---|
| `app.customers` | 2,000 |
| `app.products` | 1,000 |
| `app.orders` | 10,000 |
| `app.order_items` | 30,000 |

---

## Database Structure

```
analytics (database)
└── app (schema, owner: app)
    ├── customers
    ├── products
    ├── orders
    └── order_items
```

See `schema_diagram.mmd` for the full ER diagram with column types and sample values.

---

## Connecting

### Via Docker exec (no local psql needed)

```bash
docker exec -it pg-local psql -U postgres -d analytics
```

### Via local psql

```bash
psql postgresql://postgres:password@localhost:5432/analytics
```

### Connection string (for MCP / app config)

```
postgresql://postgres:password@localhost:5432/analytics
```

Set the default schema to avoid prefixing every query:

```sql
SET search_path TO app;
```

---

## Useful psql Commands

| Command | What it does |
|---|---|
| `\dt app.*` | List tables in the app schema |
| `\d app.orders` | Describe a table |
| `SELECT * FROM app.orders LIMIT 5;` | Preview rows |
| `\q` | Quit |

---

## Start / Stop the Container

```bash
docker start pg-local   # start
docker stop pg-local    # stop
docker rm -f pg-local   # remove entirely
```

To rebuild from scratch, repeat from Step 1.
