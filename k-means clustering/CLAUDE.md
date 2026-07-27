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

use IBM dseign language to design plots : https://www.ibm.com/design/language/

use the colors from here : https://www.ibm.com/design/language/color
