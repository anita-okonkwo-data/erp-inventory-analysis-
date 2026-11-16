# ERP-Style Inventory and Purchasing Analysis

**Tools:** Python (pandas, matplotlib), SQL (SQLite), Excel
**Data:** Simulated. Station names, prices and quantities are invented for practice. No real company data is used.
This is a practice project built with ERP-style data (stock, purchases, suppliers). It is not experience with a live ERP system.

## The business problem

An ERP system keeps stock, purchasing and sales records in one place. A fuel-retail chain with 12 stations needs to know
where stock runs low, where physical stock does not match the system balance, and which supplier gives the best price.

## What I did

1. Built a simulated monthly stock ledger: 12 stations x 4 products x 12 months = 576 rows (`erp_inventory_analysis.py`).
2. Compared the **book balance** (opening + purchases - sales) with the **physical count** to measure stock loss.
3. Wrote 4 SQL queries (`queries_erp.sql`): reorder-level alerts, stock variance ranking (`RANK`), supplier cost comparison, loss by product.
4. Produced a chart and an Excel report (`inventory_report.xlsx`).

## Results (simulated)

- 13 station-product-months closed below their reorder level.
- Largest stock variance: PMS (Petrol) at Port Harcourt, 2.23% of sales lost between book balance and physical count.
- Total stock loss across the year: about NGN 76,398,219.
- For petrol, Supplier D charged about 7.3% more per litre on average than Supplier C.

These patterns come from how the data was generated, so treat them as a demonstration of method, not real findings.

## How to run

```
python erp_inventory_analysis.py
```

## Files

`erp_inventory_analysis.py` · `stock_ledger.csv` · `queries_erp.sql` · `inventory_report.xlsx` · `chart_stock_variance.png`
