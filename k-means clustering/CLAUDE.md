# K-Means Clustering — Context

## Dataset

**Online Retail II** — transactional data for a UK-based retail chain.
File: `online_retail_II.xlsx`, sheet: `Year 2009-2010`.

## Columns

| Column        | Description                                            |
| ------------- | ------------------------------------------------------ |
| `Invoice`     | Invoice number. Prefix `C` = cancellation              |
| `StockCode`   | Product code                                           |
| `Description` | Product name                                           |
| `Quantity`    | Units per transaction (negative = return/cancellation) |
| `InvoiceDate` | Date and time of transaction                           |
| `Price`       | Unit price in GBP                                      |
| `Customer ID` | Unique customer identifier (nullable)                  |
| `Country`     | Country of the customer                                |

InvoiceNo: Invoice number. Nominal. A 6-digit integral number uniquely assigned to each transaction. If this code starts with the letter 'c', it indicates a cancellation

StockCode: Product (item) code. Nominal. A 5-digit integral number uniquely assigned to each distinct product.

Description: Product (item) name. Nominal

Quantity: The quantities of each product (item) per transaction. Numeric

InvoiceDate: Invice date and time. Numeric. The day and time when a transaction was generated.

UnitPrice: Unit price. Numeric. Product price per unit in sterling (Â£)

CustomerID: Customer number. Nominal. A 5-digit integral number uniquely assigned to each customer

Country: Country name. Nominal. The name of the country where a customer resides

Use [IBM Design Language](https://www.ibm.com/design/language/) to design plots.

Use the colors from [IBM Design Language — Color](https://www.ibm.com/design/language/color).

## Preprocessing & Clustering Notes

**Read `rfm_preprocessing_explainer.md` for the full pipeline** (cleaning → RFM aggregation →
log-transform → scaling → elbow/silhouette → K selection). Summary:

- Cleaning: drop cancelled invoices (`Invoice` starting with `C`), non-standard `StockCode`
  values (not 5-digit numeric + optional single letter), null `Customer ID`, non-positive
  `Price`.
- RFM aggregated to `customer_df` (one row per `Customer ID`): `monetary_value` (sum of
  `Quantity * Price`), `frequency` (count of distinct `Invoice`), `recency` (days since last
  purchase, relative to max date + 1).
- Before scaling, extreme outliers are split off by IQR on `monetary_value` into
  `whale_customers_df` and `low_val_cust_df`; only the remaining `customer_df` is
  log-transformed/scaled/clustered (whales and low-value customers are re-joined into
  `all_combined` after clustering, but don't influence the centroids).
- `monetary_value`, `frequency`, and `recency` are all heavily right-skewed — log-transform
  (`np.log1p`) all three before `StandardScaler`, never scale raw skewed values directly.
- Scaled features live in `customer_df_scaled` (`monetary_value_scaled`,
  `frequency_scaled`, `recency_scaled`), with `Customer ID` carried over separately since
  `StandardScaler` output doesn't retain it.
- **K=4** was chosen via elbow method + silhouette score (see
  `elbow_silhouette_k4.png` and `rfm_preprocessing_explainer.md` for the reasoning) —
  `KMeans(n_clusters=4, n_init=10, random_state=42)`.

## Business Interpretation

**Read `cluster_interpretation_explainer.md` for the business interpretation of the fitted clusters** —
segment names (Champions, Dormant, Growth, Occasional/New), revenue share per cluster, and
business actions per segment.

`recency` is **raw days since last purchase**, not an inverted RFM score — low recency = bought
recently = good. Don't flip this when reasoning about which cluster is "best."
