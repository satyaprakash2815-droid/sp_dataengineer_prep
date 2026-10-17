# """Section C - Python practical, Q1-Q7 (pure Python, no pandas)."""
import csv
from collections import defaultdict
from datetime import datetime, date
from itertools import islice
from pathlib import Path

DATA_DIR = Path("data")


def read_csv(name):
    # """Return a list of dict rows for a CSV file."""
    with open(DATA_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------- Q1: row counts and column names ----------
def q1():
    for name in ["customer.csv", "product.csv", "orders.csv", "order_items.csv"]:
        with open(DATA_DIR / name, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
            print(f"{name}: {count} rows, columns={reader.fieldnames}")


# ---------- Q2: customers dictionary ----------
def q2():
    customers = {int(r["customer_id"]): r for r in read_csv("customer.csv")}
    print(customers[101])
    return customers


# ---------- Q3: revenue by product ----------
def q3():
    revenue = defaultdict(int)
    for r in read_csv("order_items.csv"):
        revenue[r["product_id"]] += int(r["quantity"]) * int(r["unit_price"])
    for pid, total in sorted(revenue.items(), key=lambda x: x[1], reverse=True):
        print(pid, total)
    return dict(revenue)


# ---------- Q4: parse dates ----------
def parse_date(text):
    """Return a date, or None when the text is not a valid YYYY-MM-DD date."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def q4():
    for r in read_csv("orders.csv")[:3]:
        d = parse_date(r["order_date"])
        print(r["order_id"], d, d.year, d.month, d.day)


# ---------- Q5: data-quality checks ----------
def q5():
    issues = []
    for fname in ["orders.csv", "orders_incremental.csv"]:
        for r in read_csv(fname):
            if not (r["customer_id"] or "").strip():
                issues.append((fname, r["order_id"], "missing customer_id"))
            if parse_date(r["order_date"]) is None:
                issues.append((fname, r["order_id"], f"invalid date: {r['order_date']!r}"))
    for r in read_csv("order_items.csv"):
        try:
            if int(r["quantity"]) <= 0:
                issues.append(("order_items.csv", r["order_item_id"], "non-positive quantity"))
        except ValueError:
            issues.append(("order_items.csv", r["order_item_id"], "quantity not a number"))
        try:
            if float(r["unit_price"]) <= 0:
                issues.append(("order_items.csv", r["order_item_id"], "invalid price"))
        except ValueError:
            issues.append(("order_items.csv", r["order_item_id"], "price not a number"))
    for i in issues:
        print(i)
    return issues


# ---------- Q6: dedupe incremental ----------
# Business key: order_id. Rule: keep the row with the latest updated_at;
# on a tie keep the first one seen (deterministic).
def q6():
    best = {}
    for r in read_csv("orders_incremental.csv"):
        key = r["order_id"]
        if key not in best or r["updated_at"] > best[key]["updated_at"]:
            best[key] = r
    deduped = list(best.values())
    print(f"before={len(read_csv('orders_incremental.csv'))}, after={len(deduped)}")
    return deduped


# ---------- Q7: chunked read ----------
def read_in_chunks(path, chunk_size=100_000):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        while chunk := list(islice(reader, chunk_size)):
            yield chunk


def q7(path=DATA_DIR / "order_items.csv", chunk_size=100_000):
    total = 0
    for chunk in read_in_chunks(path, chunk_size):
        total += sum(int(r["quantity"]) * int(r["unit_price"]) for r in chunk)
    print("total revenue:", total)
    return total


if __name__ == "__main__":
    for fn in (q1, q2, q3, q4, q5, q6):
        print(f"\n--- {fn.__name__} ---")
        fn()
    print("\n--- q7 (chunk_size=5) ---")
    q7(chunk_size=5)
