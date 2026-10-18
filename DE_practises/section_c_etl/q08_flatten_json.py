"""Q8: flatten nested order + customer JSON into a list of flat records."""
import json
from etl_lib import read_csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

def build_sample_json(path=DATA_DIR / "orders_nested.json"):
    """Create a nested JSON sample from the CSV files (for practice)."""
    customers = {c["customer_id"]: c for c in read_csv("DE_practises/section_c_etl/data/customer.csv")}
    items_by_order = {}
    for it in read_csv("DE_practises/section_c_etl/data/order_items.csv"):
        items_by_order.setdefault(it["order_id"], []).append(
            {"product_id": it["product_id"], "quantity": int(it["quantity"]),
             "unit_price": int(it["unit_price"])})
    orders = []
    for o in read_csv("DE_practises/section_c_etl/data/orders.csv"):
        c = customers[o["customer_id"]]
        orders.append({
            "order_id": int(o["order_id"]), "order_date": o["order_date"],
            "status": o["order_status"],
            "customer": {"customer_id": int(c["customer_id"]), "name": c["customer_name"],
                         "address": {"country": c["country"], "city": c["city"]}},
            "items": items_by_order.get(o["order_id"], []),
        })
    with open(path, "w") as f:
        json.dump({"orders": orders}, f, indent=2)


def flatten_dict(d, parent="", sep="_"):
    """Recursively flatten nested dicts: {'a': {'b': 1}} -> {'a_b': 1}."""
    flat = {}
    for k, v in d.items():
        key = f"{parent}{sep}{k}" if parent else k
        if isinstance(v, dict):
            flat.update(flatten_dict(v, key, sep))
        else:
            flat[key] = v
    return flat


def flatten_orders(data):
    """One flat record per order item (orders without items still produce one row)."""
    records = []
    for order in data["orders"]:
        items = order.get("items") or [{}]
        base = flatten_dict({k: v for k, v in order.items() if k != "items"})
        for item in items:
            records.append({**base, **{f"item_{k}": v for k, v in item.items()}})
    return records


if __name__ == "__main__":
    build_sample_json()
    with open("DE_practises/section_c_etl/data/orders_nested.json") as f:
        rows = flatten_orders(json.load(f))
    print(len(rows), "flat records")
    print(rows[0])
