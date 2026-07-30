# Cohort Retention Analysis — Explainer

This walks through how `retention_analytics.ipynb` builds a time-based cohort
retention table from the Online Retail II transaction data.

The analysis is framed as if performed on **1 Jan 2012**, using the
`Year 2010-2011` sheet from `k-means clustering/online_retail_II.xlsx`.

## 1. Cleaning

Before any cohort logic, the raw transaction data is cleaned:

- Drop rows with a null or `0` `Customer ID` — can't attribute a cohort to an
  unknown customer.
- Filter to `Quantity > 0` and `Price > 0` — removes returns/cancellations and
  bad rows.
- Drop exact duplicate rows.

## 2. Time-based cohorts

There are several ways to define a cohort (time-based, size-based,
segment-based). This analysis uses **time-based cohorts**: a customer's
cohort is the calendar month of their _first purchase_.

```python
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['year'] = df['InvoiceDate'].dt.year
df['month'] = df['InvoiceDate'].dt.month
```

### First purchase date

```python
df['first_purchase_date'] = df.groupby('Customer ID')['InvoiceDate'].transform('min')
```

`transform('min')` computes each customer's earliest `InvoiceDate` and
broadcasts it back onto every row belonging to that customer (no merge
needed).

### Cohort date

The cohort is the customer's first-purchase month, truncated to the 1st of
that month:

```python
df['cohort_date'] = pd.to_datetime(dict(
    year=df['first_purchase_date'].dt.year,
    month=df['first_purchase_date'].dt.month,
    day=1
))
```

`cohort_year` / `cohort_month` are then pulled directly from
`first_purchase_date` (not re-derived from `cohort_date`) — same result,
one less step:

```python
df['cohort_year'] = df['first_purchase_date'].dt.year
df['cohort_month'] = df['first_purchase_date'].dt.month
```

## 3. Cohort index

The **cohort index** is a relative time counter: how many months have
elapsed since a customer's first purchase, rather than an absolute calendar
month. It's what makes cohorts from different acquisition months
comparable — "% still active in month 3" means the same thing for every
cohort, regardless of when they started.

```python
df['cohort_index'] = (df['year'] - df['cohort_year']) * 12 + (df['month'] - df['cohort_month']) + 1
```

- `+ 1` makes the first active month index `1` instead of `0`.
- The formula converts both dates to a continuous "month number" timeline
  (`year * 12 + month`), so it holds across multi-year spans without any
  special-casing at year boundaries — e.g. invoice `2015-06` vs cohort
  `2010-03` gives `(2015-2010)*12 + (6-3) + 1 = 64`, correctly 64 months in.

## 4. Building the retention pivot

Count **distinct customers** active per cohort per cohort index:

```python
cohort_pivot_dataset = retention_dataset.groupby(['cohort_date', 'cohort_index'])['Customer ID'].nunique().reset_index()

cohort_pivot = cohort_pivot_dataset.pivot(
    index='cohort_date', columns='cohort_index', values='Customer ID'
)
```

This produces the retention "triangle":

- **Rows** = `cohort_date` — the acquisition month.
- **Columns** = `cohort_index` — months since acquisition (1, 2, 3, ...).
- **Cells** = number of distinct customers from that cohort active at that
  index.

Column index `1` is each cohort's size (everyone acquired that month, by
definition active in their own first month).

The staircase of `NaN`s in the upper-right isn't missing data — it's
structural. A cohort acquired in `2011-12-01` can't have a "month 2" value
yet if the dataset ends in December 2011; there's no future data to measure
it. Cohorts further back have had more calendar time to accumulate higher
indices.

## 5. Retention percentage

Normalize each row by its own cohort size (column `1`) to make cohorts of
different sizes comparable:

```python
cohort_size = cohort_pivot.iloc[:, 0]
retention_pct = cohort_pivot.divide(cohort_size, axis=0) * 100
```

Each cell now reads as "% of the original cohort still active in month N."

## 6. Combined count + percentage display

For a display table that shows both the raw count and the percentage
(count on top, percentage in parentheses below):

```python
combined = (
    cohort_pivot.astype('Int64').astype(str)
    + '\n('
    + retention_pct.round(0).astype('Int64').astype(str)
    + '%)'
)
combined = combined.where(cohort_pivot.notna(), '')
```

`.where(cohort_pivot.notna(), '')` blanks out cells that were `NaN` in the
original pivot, instead of rendering the literal string `"<NA> (<NA>%)"`.

## 7. Heatmap

`retention_pct` drives the cell **color** (sequential magnitude — one hue,
light→dark, per the repo's `dataviz` skill conventions); `combined` supplies
the **annotation text** in each cell.

```python
from matplotlib.colors import LinearSegmentedColormap

blue_ramp = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
    "#256abf", "#184f95", "#0d366b"
]
cmap = LinearSegmentedColormap.from_list("sequential_blue", blue_ramp)

plt.figure(figsize=(14, 8))
sns.heatmap(
    retention_pct,
    annot=combined.values,
    fmt='',
    cmap=cmap,
    linewidths=2,
    linecolor="#fcfcfb",
    annot_kws={'size': 9},
    yticklabels=retention_pct.index.strftime('%Y-%m-%d'),
    cbar_kws={'label': 'Retention %'}
)
plt.title('Cohort Retention Heatmap')
plt.xlabel('Cohort Index (months since first purchase)')
plt.ylabel('Cohort Date')
plt.tight_layout()
plt.show()
```

Notes:

- `fmt=''` is required whenever `annot` is passed as an array of pre-formatted
  strings rather than left to seaborn to format numerically.
- `yticklabels=retention_pct.index.strftime('%Y-%m-%d')` formats the
  `cohort_date` row labels as plain dates instead of full timestamps (the
  index is a `DatetimeIndex`).
- `linecolor="#fcfcfb"` matches the palette's light chart-surface token, so
  the gap between cells reads as a surface gap rather than an arbitrary
  white line.
