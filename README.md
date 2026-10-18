Outputs in output/:

clean_orders.csv: customer name and country, parsed dates, revenue, and a category column (Completed sale, Cancelled, Returned, Pending)
error_report.csv: source, record id, severity and issue. It has 2 ERROR rows (1017, 1019), 2 INFO rows (duplicate orders 1001 and 1002) and 2 WARNING rows (orders 1016 and 1018 have no order items, so revenue is 0).
summary.json: orders and value per status (Delivered 367,400, Cancelled 1,500, Returned 2,500, Pending 10,500), shown separately as the rules require
etl.log: the structured log
Why: it applies every business rule. Item prices are used for revenue, only Delivered orders count as sales, invalid dates and missing IDs are reported, and the dedupe rule is written in the code.
Say aloud: “It extracts the CSVs, deduplicates on order_id, validates, calculates revenue from item prices, then writes a clean file, an error report and a summary, with structured logs throughout.”
Follow-up: Why not drop bad rows silently? 
--> The rules require them to be reported, and silent drops hide data problems.
Follow-up: How would you make it idempotent? 
--> Running it twice gives the same output, because it rebuilds the output from the inputs and doesn’t append.
Follow-up: How would you scale it? 
--> Move the same logic to PySpark/Databricks, which is the same pipeline with DataFrames.
