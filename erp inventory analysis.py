"""
ERP-style inventory and purchasing analysis (SIMULATED DATA).

An ERP (enterprise resource planning) system keeps stock, purchasing and sales records in one place.
This project builds a simulated monthly stock ledger for 12 fuel stations and 4 products, then uses SQL
to answer questions a Data & Reporting Analyst would be asked:
  - Which stations and products keep falling below their reorder level?
  - Where does physical stock differ from the book (system) balance?
  - Which supplier is cheapest for each product?

All names, prices and quantities are invented for practice. No real company data is used.
"""
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl.utils import get_column_letter

rng = np.random.default_rng(7)

STATIONS = {
    "ST01": "Ikeja", "ST02": "Lekki", "ST03": "Surulere", "ST04": "Ibadan Ring Rd",
    "ST05": "Abeokuta", "ST06": "Benin City", "ST07": "Port Harcourt", "ST08": "Enugu",
    "ST09": "Abuja Wuse", "ST10": "Kano", "ST11": "Kaduna", "ST12": "Ilorin",
}
STATION_WEIGHT = dict(zip(STATIONS, np.array([1.4, 1.5, 1.1, 1, 0.9, 1, 1.2, 0.9, 1.3, 0.9, 0.8, 0.8]) / 1.1))
# product: (unit, average monthly sales per station, base unit cost in NGN)
PRODUCTS = {
    "PMS (Petrol)": ("litre", 60000, 780),
    "AGO (Diesel)": ("litre", 25000, 950),
    "LPG (Cooking gas)": ("kg", 4000, 1150),
    "Engine oil": ("unit", 250, 7800),
}
SUPPLIERS = {"Supplier A": 1.00, "Supplier B": 1.03, "Supplier C": 0.98, "Supplier D": 1.06}
# Deliberate problem spots so the analysis has something real to find
EXTRA_LOSS = {("ST07", "PMS (Petrol)"): 0.015, ("ST03", "AGO (Diesel)"): 0.012}

rows = []
for sid, sname in STATIONS.items():
    for product, (unit, base_sales, base_cost) in PRODUCTS.items():
        avg = base_sales * STATION_WEIGHT[sid]
        reorder = round(avg * 0.9, 1)
        opening = round(avg * 1.3, 1)
        for month in range(1, 13):
            sales = round(avg * rng.normal(1, 0.08), 1)
            purchases = round(sales * rng.uniform(0.88, 1.12), 1)
            supplier = rng.choice(list(SUPPLIERS))
            unit_cost = round(base_cost * (1 + 0.012 * month) * SUPPLIERS[supplier] * rng.normal(1, 0.01), 0)
            book_close = round(opening + purchases - sales, 1)
            shrink = max(rng.normal(0.004, 0.002), 0) + EXTRA_LOSS.get((sid, product), 0)
            physical = round(book_close * (1 - shrink), 1)
            rows.append({
                "month": f"2025-{month:02d}", "station_id": sid, "station_name": sname, "product": product,
                "unit": unit, "opening_stock": opening, "purchases_qty": purchases, "sales_qty": sales,
                "supplier": supplier, "unit_cost": unit_cost, "purchase_cost": round(purchases * unit_cost),
                "book_closing": book_close, "physical_closing": physical,
                "loss_qty": round(book_close - physical, 1), "loss_value": round((book_close - physical) * unit_cost),
                "reorder_level": reorder,
            })
            opening = physical  # next month starts from the physical count

ledger = pd.DataFrame(rows)
ledger.to_csv("stock_ledger.csv", index=False)

con = sqlite3.connect("erp_inventory.db")
ledger.to_sql("ledger", con, if_exists="replace", index=False)

QUERIES = {
    "Below reorder level": """
        SELECT station_name, product, COUNT(*) AS months_below_reorder
        FROM ledger WHERE physical_closing < reorder_level
        GROUP BY station_name, product
        ORDER BY months_below_reorder DESC, station_name LIMIT 10""",
    "Stock variance": """
        SELECT station_name, product,
               ROUND(100.0 * SUM(loss_qty) / SUM(sales_qty), 2) AS loss_pct_of_sales,
               ROUND(SUM(loss_value)) AS loss_value_ngn,
               RANK() OVER (ORDER BY SUM(loss_qty) * 1.0 / SUM(sales_qty) DESC) AS variance_rank
        FROM ledger
        GROUP BY station_name, product
        ORDER BY variance_rank LIMIT 10""",
    "Supplier cost": """
        SELECT product, supplier, ROUND(AVG(unit_cost)) AS avg_unit_cost_ngn,
               ROUND(SUM(purchase_cost)) AS spend_ngn
        FROM ledger GROUP BY product, supplier
        ORDER BY product, avg_unit_cost_ngn""",
    "Loss by product": """
        SELECT product, ROUND(SUM(loss_value)) AS loss_value_ngn,
               ROUND(100.0 * SUM(loss_qty) / SUM(sales_qty), 2) AS loss_pct_of_sales
        FROM ledger GROUP BY product ORDER BY loss_value_ngn DESC""",
}
with open("queries_erp.sql", "w") as f:
    f.write("-- ERP-style inventory analysis (simulated data). SQLite, table: ledger\n\n")
    for name, q in QUERIES.items():
        f.write(f"-- {name}\n" + "\n".join(l[8:] if l.startswith("        ") else l for l in q.strip().splitlines()) + ";\n\n")

results = {n: pd.read_sql_query(q, con) for n, q in QUERIES.items()}
for n, d in results.items():
    print(f"\n=== {n} ===\n{d.to_string(index=False)}")

# chart: top stock variances
v = results["Stock variance"].head(8).iloc[::-1]
labels = v["station_name"] + " - " + v["product"].str.replace(r" \(.*\)", "", regex=True)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(labels, v["loss_pct_of_sales"], color=["#1f5fa8" if x > 1 else "#9aa5b1" for x in v["loss_pct_of_sales"]])
ax.set_xlabel("Stock lost as % of sales (book vs physical count)")
ax.set_title("Largest stock variances, 2025 (simulated data)", loc="left", fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("chart_stock_variance.png", dpi=150); plt.close(fig)

# Excel report
with pd.ExcelWriter("inventory_report.xlsx", engine="openpyxl") as xw:
    for n, d in results.items():
        d.to_excel(xw, sheet_name=n[:31], index=False)
    ledger.to_excel(xw, sheet_name="Stock ledger", index=False)
    for ws in xw.book.worksheets:
        for i, col in enumerate(ws.columns, 1):
            ws.column_dimensions[get_column_letter(i)].width = min(max(len(str(c.value or "")) for c in col) + 3, 40)
        ws.freeze_panes = "A2"

# README built from the computed results so the numbers always match
top = results["Stock variance"].iloc[0]
flags = int((ledger["physical_closing"] < ledger["reorder_level"]).sum())
total_loss = int(ledger["loss_value"].sum())
pms = results["Supplier cost"].query("product == 'PMS (Petrol)'")
cheap, dear = pms.iloc[0], pms.iloc[-1]
gap = (dear["avg_unit_cost_ngn"] / cheap["avg_unit_cost_ngn"] - 1) * 100
readme = f"""# ERP-Style Inventory and Purchasing Analysis

**Tools:** Python (pandas, matplotlib), SQL (SQLite), Excel
**Data:** Simulated. Station names, prices and quantities are invented for practice. No real company data is used.
This is a practice project built with ERP-style data (stock, purchases, suppliers). It is not experience with a live ERP system.

## The business problem

An ERP system keeps stock, purchasing and sales records in one place. A fuel-retail chain with 12 stations needs to know
where stock runs low, where physical stock does not match the system balance, and which supplier gives the best price.

## What I did

1. Built a simulated monthly stock ledger: 12 stations x 4 products x 12 months = {len(ledger):,} rows (`erp_inventory_analysis.py`).
2. Compared the **book balance** (opening + purchases - sales) with the **physical count** to measure stock loss.
3. Wrote 4 SQL queries (`queries_erp.sql`): reorder-level alerts, stock variance ranking (`RANK`), supplier cost comparison, loss by product.
4. Produced a chart and an Excel report (`inventory_report.xlsx`).

## Results (simulated)

- {flags} station-product-months closed below their reorder level.
- Largest stock variance: {top['product']} at {top['station_name']}, {top['loss_pct_of_sales']}% of sales lost between book balance and physical count.
- Total stock loss across the year: about NGN {total_loss:,}.
- For petrol, {dear['supplier']} charged about {gap:.1f}% more per litre on average than {cheap['supplier']}.

These patterns come from how the data was generated, so treat them as a demonstration of method, not real findings.

## How to run

```
python erp_inventory_analysis.py
```

## Files

`erp_inventory_analysis.py` · `stock_ledger.csv` · `queries_erp.sql` · `inventory_report.xlsx` · `chart_stock_variance.png`
"""
with open("README.md", "w") as f:
    f.write(readme)
print("\nDone.")
