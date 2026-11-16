-- ERP-style inventory analysis (simulated data). SQLite, table: ledger

-- Below reorder level
SELECT station_name, product, COUNT(*) AS months_below_reorder
FROM ledger WHERE physical_closing < reorder_level
GROUP BY station_name, product
ORDER BY months_below_reorder DESC, station_name LIMIT 10;

-- Stock variance
SELECT station_name, product,
       ROUND(100.0 * SUM(loss_qty) / SUM(sales_qty), 2) AS loss_pct_of_sales,
       ROUND(SUM(loss_value)) AS loss_value_ngn,
       RANK() OVER (ORDER BY SUM(loss_qty) * 1.0 / SUM(sales_qty) DESC) AS variance_rank
FROM ledger
GROUP BY station_name, product
ORDER BY variance_rank LIMIT 10;

-- Supplier cost
SELECT product, supplier, ROUND(AVG(unit_cost)) AS avg_unit_cost_ngn,
       ROUND(SUM(purchase_cost)) AS spend_ngn
FROM ledger GROUP BY product, supplier
ORDER BY product, avg_unit_cost_ngn;

-- Loss by product
SELECT product, ROUND(SUM(loss_value)) AS loss_value_ngn,
       ROUND(100.0 * SUM(loss_qty) / SUM(sales_qty), 2) AS loss_pct_of_sales
FROM ledger GROUP BY product ORDER BY loss_value_ngn DESC;

