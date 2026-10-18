import csv

DATA_DIR = Path(__file__).resolve().parent / "data"


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

