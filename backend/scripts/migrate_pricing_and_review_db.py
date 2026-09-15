import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "securemarket.db")

def migrate():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Update reviews table
    cursor.execute("PRAGMA table_info(reviews)")
    review_cols = [row[1] for row in cursor.fetchall()]
    print("Existing review columns:", review_cols)

    if "status" not in review_cols:
        print("Adding 'status' column to reviews table...")
        cursor.execute("ALTER TABLE reviews ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_reviews_status ON reviews (status)")

    # 2. Update products table
    cursor.execute("PRAGMA table_info(products)")
    prod_cols = [row[1] for row in cursor.fetchall()]
    print("Existing product columns:", prod_cols)

    new_prod_cols = [
        ("suggested_price", "FLOAT"),
        ("suggested_price_min", "FLOAT"),
        ("suggested_price_max", "FLOAT"),
        ("maximum_allowed_price", "FLOAT"),
        ("value_score", "FLOAT"),
        ("price_status", "VARCHAR(30) DEFAULT 'APPROVED'")
    ]

    for col_name, col_type in new_prod_cols:
        if col_name not in prod_cols:
            print(f"Adding '{col_name}' ({col_type}) to products table...")
            cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
