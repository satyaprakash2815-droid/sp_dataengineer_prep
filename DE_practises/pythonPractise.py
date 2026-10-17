# import csv


# # def read_csv_files(directory):
# # 	"""Read every CSV file in a directory and return rows keyed by filename."""
# # 	from pathlib import Path

# # 	csv_files = {}
# # 	for file_path in Path(directory).glob("*.csv"):
# # 		with file_path.open(mode="r", newline="", encoding="utf-8-sig") as csv_file:
# # 			csv_files[file_path.name] = list(csv.DictReader(csv_file))
# # 	return csv_files
# # DATA_DIR = Path("data")


# def read_csv(name):
#     # """Return a list of dict rows for a CSV file."""
#     with open(DATA_DIR / name, newline="", encoding="utf-8") as f:
#         return list(csv.DictReader(f))


# read_csv_files = read_csv_files("C:\\Users\\user\\DE_wrkspc\\sp_dataengineer_prep\\DE_practises\\data")



# ---------- Q1: row counts and column names ----------
def q1():
    for name in ["customer.csv", "product.csv", "orders.csv", "order_items.csv"]:
        with open(DATA_DIR / name, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = sum(1 for _ in reader)
            print(f"{name}: {count} rows, columns={reader.fieldnames}")