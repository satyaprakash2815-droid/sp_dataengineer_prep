"""Q14: pytest unit tests - revenue, missing values, duplicates (+ snapshot diff, ETL run)."""
import pytest
import etl_lib as lib
from etl_app import run
from snapshot_diff import compare_snapshots


# ---------- revenue calculation ----------
def test_item_revenue_uses_item_price():
    assert lib.item_revenue({"quantity": "2", "unit_price": "2500"}) == 5000


def test_item_revenue_rejects_non_numeric():
    with pytest.raises(ValueError):
        lib.item_revenue({"quantity": "two", "unit_price": "2500"})


@pytest.mark.parametrize("qty,price,expected", [(1, 75000, 75000), (3, 1200, 3600), (0, 500, 0)])
def test_item_revenue_parametrized(qty, price, expected):
    assert lib.item_revenue({"quantity": qty, "unit_price": price}) == expected


# ---------- missing / invalid values ----------
def test_missing_customer_id_is_flagged():
    row = {"customer_id": "", "order_date": "2025-03-26", "order_status": "Pending"}
    assert "missing customer_id" in lib.validate_order(row)


def test_invalid_date_is_flagged():
    row = {"customer_id": "101", "order_date": "invalid_date", "order_status": "Delivered"}
    assert any("invalid order_date" in e for e in lib.validate_order(row))


def test_valid_order_has_no_errors():
    row = {"customer_id": "101", "order_date": "2025-01-05", "order_status": "Delivered"}
    assert lib.validate_order(row) == []


def test_negative_quantity_and_bad_price_are_flagged():
    errs = lib.validate_item({"quantity": "-1", "unit_price": "abc"})
    assert "non-positive quantity" in errs and "unit_price not a number" in errs


# ---------- duplicate detection ----------
ROWS = [
    {"order_id": "1002", "updated_at": "2025-01-08 12:00:00", "order_status": "Pending"},
    {"order_id": "1002", "updated_at": "2025-01-09 09:00:00", "order_status": "Delivered"},
    {"order_id": "1003", "updated_at": "2025-01-10 08:00:00", "order_status": "Cancelled"},
]


def test_find_duplicates():
    assert lib.find_duplicates(ROWS, "order_id") == {"1002"}


def test_dedupe_keeps_latest_updated_at():
    result = {r["order_id"]: r for r in lib.dedupe_latest(ROWS)}
    assert len(result) == 2
    assert result["1002"]["order_status"] == "Delivered"


def test_dedupe_tie_keeps_first_seen():
    tie = [{"order_id": "1", "updated_at": "x", "v": "first"},
           {"order_id": "1", "updated_at": "x", "v": "second"}]
    assert lib.dedupe_latest(tie)[0]["v"] == "first"


# ---------- snapshot compare ----------
def test_compare_snapshots():
    old = [{"order_id": "1", "s": "A"}, {"order_id": "2", "s": "A"}, {"order_id": "3", "s": "A"}]
    new = [{"order_id": "1", "s": "A"}, {"order_id": "2", "s": "B"}, {"order_id": "4", "s": "A"}]
    d = compare_snapshots(old, new)
    assert [r["order_id"] for r in d["inserted"]] == ["4"]
    assert [r["order_id"] for r in d["deleted"]] == ["3"]
    assert d["updated"][0]["changes"] == {"s": ("A", "B")}


# ---------- end-to-end (uses the real sample files) ----------
def test_etl_end_to_end(tmp_path):
    import logging
    clean, errors, summary = run("data", tmp_path, logging.getLogger("test"))
    assert summary["completed_sales_revenue"] == 367400          # Delivered only
    assert {e["record_id"] for e in errors if e["severity"] == "ERROR"} == {"1017", "1019"}
    assert (tmp_path / "clean_orders.csv").exists()
    assert (tmp_path / "error_report.csv").exists()
