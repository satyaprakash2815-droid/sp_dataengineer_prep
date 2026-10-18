"""Reusable ETL building blocks (Q9) + structured logging (Q11)."""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path

VALID_STATUSES = {"Delivered", "Cancelled", "Returned", "Pending"}


# ---------------- Q11: structured (JSON) logging ----------------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "step": record.name,
            "msg": record.getMessage(),
        }
        payload.update(getattr(record, "ctx", {}))   # extra structured fields
        return json.dumps(payload)


def get_logger(name="etl", log_file=None):
    logger = logging.getLogger(name)
    if logger.handlers:                      # avoid duplicate handlers on re-import
        return logger
    logger.setLevel(logging.INFO)
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    for h in handlers:
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
    return logger


# ---------------- Q9: read ----------------
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------- Q9: validate ----------------
def parse_date(text):
    try:
        return datetime.strptime((text or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_order(row):
    """Return a list of error strings (empty list = valid)."""
    errors = []
    if not (row.get("customer_id") or "").strip():
        errors.append("missing customer_id")
    if parse_date(row.get("order_date")) is None:
        errors.append(f"invalid order_date: {row.get('order_date')!r}")
    if row.get("order_status") not in VALID_STATUSES:
        errors.append(f"invalid order_status: {row.get('order_status')!r}")
    return errors


def validate_item(row):
    errors = []
    try:
        if int(row["quantity"]) <= 0:
            errors.append("non-positive quantity")
    except (ValueError, TypeError, KeyError):
        errors.append("quantity not a number")
    try:
        if float(row["unit_price"]) <= 0:
            errors.append("invalid unit_price")
    except (ValueError, TypeError, KeyError):
        errors.append("unit_price not a number")
    return errors


# ---------------- Q9: transform ----------------
def item_revenue(item):
    """Revenue = quantity x the unit price paid on the order item."""
    return int(item["quantity"]) * int(item["unit_price"])


def find_duplicates(rows, key):
    """Return the key values that appear more than once."""
    seen, dups = set(), set()
    for r in rows:
        k = r[key]
        (dups if k in seen else seen).add(k)
    return dups


def dedupe_latest(rows, key="order_id", order_col="updated_at"):
    """Keep one row per business key: the latest order_col; ties keep the first seen."""
    best = {}
    for r in rows:
        k = r[key]
        if k not in best or (r.get(order_col) or "") > (best[k].get(order_col) or ""):
            best[k] = r
    return list(best.values())


# ---------------- Q9: write ----------------
def write_csv(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
