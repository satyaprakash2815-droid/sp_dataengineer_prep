"""Q12 + Q15: configurable end-to-end ETL.
Usage: python etl_app.py --input-dir data --output-dir output
Outputs: clean_orders.csv, error_report.csv, summary.json, etl.log
"""
import argparse
from collections import defaultdict
from pathlib import Path

import etl_lib as lib

SALES_CATEGORY = {"Delivered": "Completed sale", "Cancelled": "Cancelled",
                  "Returned": "Returned", "Pending": "Pending (not a sale)"}
CLEAN_COLS = ["order_id", "customer_id", "customer_name", "country", "order_date",
              "order_status", "payment_method", "revenue", "category"]
ERROR_COLS = ["source", "record_id", "severity", "issue"]


def run(input_dir, output_dir, log):
    inp, out = Path(input_dir), Path(output_dir)
    errors = []

    def report(source, rec_id, severity, issue):
        errors.append({"source": source, "record_id": rec_id, "severity": severity, "issue": issue})

    # ---- extract ----
    customers = {c["customer_id"]: c for c in lib.read_csv(inp / "customer.csv")}
    items = lib.read_csv(inp / "order_items.csv")
    orders = [{**o, "updated_at": "", "_source": "orders.csv"}
              for o in lib.read_csv(inp / "orders.csv")]
    inc_path = inp / "orders_incremental.csv"
    if inc_path.exists():
        orders += [{**o, "_source": "orders_incremental.csv"} for o in lib.read_csv(inc_path)]
    log.info("extract done", extra={"ctx": {"customers": len(customers), "orders_rows": len(orders),
                                             "items": len(items)}})

    # ---- dedupe: business key = order_id, keep latest updated_at, tie -> first seen ----
    for k in sorted(lib.find_duplicates(orders, "order_id")):
        n = sum(1 for o in orders if o["order_id"] == k)
        report("orders", k, "INFO", f"duplicate order_id ({n} copies); kept latest updated_at")
    merged = lib.dedupe_latest(orders, "order_id", "updated_at")
    log.info("dedupe done", extra={"ctx": {"before": len(orders), "after": len(merged)}})

    # ---- validate orders ----
    valid_orders = []
    for o in merged:
        problems = lib.validate_order(o)
        if not problems and o["customer_id"] not in customers:
            problems.append(f"unknown customer_id: {o['customer_id']}")
        for p in problems:
            report(o["_source"], o["order_id"], "ERROR", p)
        if not problems:
            valid_orders.append(o)

    # ---- validate items, then revenue per order (item price, not product price) ----
    revenue = defaultdict(int)
    for it in items:
        problems = lib.validate_item(it)
        for p in problems:
            report("order_items.csv", it["order_item_id"], "ERROR", p)
        if not problems:
            revenue[it["order_id"]] += lib.item_revenue(it)

    # ---- transform ----
    clean = []
    for o in valid_orders:
        if o["order_id"] not in revenue:
            report(o["_source"], o["order_id"], "WARNING", "no order items; revenue set to 0")
        c = customers[o["customer_id"]]
        clean.append({
            "order_id": o["order_id"], "customer_id": o["customer_id"],
            "customer_name": c["customer_name"], "country": c["country"],
            "order_date": lib.parse_date(o["order_date"]).isoformat(),
            "order_status": o["order_status"], "payment_method": o["payment_method"],
            "revenue": revenue.get(o["order_id"], 0), "category": SALES_CATEGORY[o["order_status"]],
        })
    clean.sort(key=lambda r: int(r["order_id"]))

    # ---- summary: statuses reported separately; only Delivered counts as sales ----
    by_status = defaultdict(lambda: {"orders": 0, "value": 0})
    for r in clean:
        by_status[r["order_status"]]["orders"] += 1
        by_status[r["order_status"]]["value"] += r["revenue"]
    summary = {
        "completed_sales_revenue": by_status["Delivered"]["value"],
        "by_status": dict(by_status),
        "clean_orders": len(clean),
        "rejected_orders": sum(1 for e in errors if e["severity"] == "ERROR" and e["source"] != "order_items.csv"),
        "error_report_rows": len(errors),
    }

    # ---- load ----
    lib.write_csv(out / "clean_orders.csv", clean, CLEAN_COLS)
    lib.write_csv(out / "error_report.csv", errors, ERROR_COLS)
    lib.write_json(out / "summary.json", summary)
    log.info("load done", extra={"ctx": summary})
    return clean, errors, summary


def main():
    p = argparse.ArgumentParser(description="Orders ETL")
    p.add_argument("--input-dir", required=True, help="folder holding the source CSV files")
    p.add_argument("--output-dir", default="output", help="folder for clean file + error report")
    a = p.parse_args()
    Path(a.output_dir).mkdir(parents=True, exist_ok=True)
    log = lib.get_logger("etl", Path(a.output_dir) / "etl.log")
    try:
        run(a.input_dir, a.output_dir, log)
    except FileNotFoundError as e:
        log.error("missing input file", extra={"ctx": {"error": str(e)}})
        raise SystemExit(1)


if __name__ == "__main__":
    main()
