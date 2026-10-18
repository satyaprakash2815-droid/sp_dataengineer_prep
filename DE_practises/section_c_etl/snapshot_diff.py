"""Q13: compare two order snapshots -> inserted / updated / deleted."""
import sys
from etl_lib import read_csv, write_csv


def compare_snapshots(old_rows, new_rows, key="order_id"):
    old = {r[key]: r for r in old_rows}
    new = {r[key]: r for r in new_rows}
    inserted = [new[k] for k in new.keys() - old.keys()]
    deleted = [old[k] for k in old.keys() - new.keys()]
    updated = []
    for k in old.keys() & new.keys():
        changes = {c: (old[k][c], new[k][c]) for c in old[k]
                   if c != key and old[k][c] != new[k].get(c)}
        if changes:
            updated.append({key: k, "changes": changes})
    sort_key = lambda r: int(r[key])
    return {"inserted": sorted(inserted, key=sort_key),
            "updated": sorted(updated, key=sort_key),
            "deleted": sorted(deleted, key=sort_key)}


if __name__ == "__main__":
    if len(sys.argv) == 3:
        old_rows, new_rows = read_csv(sys.argv[1]), read_csv(sys.argv[2])
    else:                                     # demo: build snapshot v2 from orders.csv
        old_rows = read_csv("data/orders.csv")
        new_rows = [dict(r) for r in old_rows if r["order_id"] != "1003"]       # 1003 deleted
        for r in new_rows:
            if r["order_id"] == "1006":
                r["order_status"] = "Delivered"                                  # 1006 updated
        new_rows.append({"order_id": "1016", "customer_id": "105", "order_date": "2025-03-25",
                         "order_status": "Delivered", "payment_method": "UPI"})  # 1016 inserted
    diff = compare_snapshots(old_rows, new_rows)
    for kind, rows in diff.items():
        print(f"{kind.upper()} ({len(rows)}):")
        for r in rows:
            print("  ", r)
