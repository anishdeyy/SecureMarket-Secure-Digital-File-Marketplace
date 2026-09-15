import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import engine, Base
import app.models

# Create any missing tables defined in models (e.g. product_quality_analyses, product_file_fingerprints, product_duplicate_checks)
Base.metadata.create_all(bind=engine)

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'securemarket.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cols = [row[1] for row in cur.execute('PRAGMA table_info(products)').fetchall()]
if 'duplicate_status' not in cols:
    cur.execute("ALTER TABLE products ADD COLUMN duplicate_status VARCHAR(30) DEFAULT 'CLEAR'")
    conn.commit()
    print("Added duplicate_status column to products table")
else:
    print("duplicate_status column already exists")

# Recalculate true reviews and ratings for all products
cur.execute("""
    UPDATE products
    SET review_count = (
        SELECT COUNT(*) FROM reviews WHERE reviews.product_id = products.id
    ),
    avg_rating = COALESCE((
        SELECT AVG(rating) FROM reviews WHERE reviews.product_id = products.id
    ), 0.0)
""")
conn.commit()
print("Recalculated true reviews and ratings for all products in database")

# Verify
products = cur.execute("SELECT id, title, avg_rating, review_count, duplicate_status FROM products").fetchall()
for p in products:
    print(f"Product: {p[0][:8]}... | {p[1][:25]} | Rating: {p[2]:.1f} | Reviews: {p[3]} | Duplicate: {p[4]}")
conn.close()
