
from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "output" / "products.csv"
DB_FILE = BASE_DIR / "output" / "products.db"

csv_df = pd.read_csv(CSV_FILE)

with sqlite3.connect(DB_FILE) as conn:
    db_df = pd.read_sql_query(
        "SELECT * FROM products", conn
    )

print("CSV records:", len(csv_df))
print("SQLite records:", len(db_df))

print("Duplicate URLs:",
      csv_df["product_url"].duplicated().sum())

print("Missing values:")
print(csv_df.isna().sum())

assert len(csv_df) == len(db_df), "Record count mismatch"
assert len(csv_df) == 60, "Expected 60 products"
assert csv_df["product_url"].is_unique, "Duplicate URLs"

pd.testing.assert_frame_equal(
    csv_df.reset_index(drop=True),
    db_df.reset_index(drop=True),
    check_dtype=False
)

print("\nPASS: CSV and SQLite data match.")
