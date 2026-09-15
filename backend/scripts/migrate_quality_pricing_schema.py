"""
migrate_quality_pricing_schema.py
Safely adds new columns to SQLite database for quality assessment and dynamic pricing.
"""

import sqlite3
import os

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (does not exist)")
        return
        
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. product_quality_analyses
    qa_cols = [c[1] for c in cur.execute("PRAGMA table_info(product_quality_analyses)").fetchall()]
    new_qa_cols = [
        ("detected_content_type", "VARCHAR(50) DEFAULT 'Document'"),
        ("methodology_depth", "INTEGER DEFAULT 70"),
        ("evidence_results", "INTEGER DEFAULT 70"),
        ("risk_reasons", "TEXT DEFAULT '[]'"),
        ("positive_checks", "TEXT DEFAULT '[]'"),
    ]
    for col_name, col_type in new_qa_cols:
        if col_name not in qa_cols:
            print(f"  Adding {col_name} to product_quality_analyses")
            cur.execute(f"ALTER TABLE product_quality_analyses ADD COLUMN {col_name} {col_type}")

    # 2. products
    p_cols = [c[1] for c in cur.execute("PRAGMA table_info(products)").fetchall()]
    new_p_cols = [
        ("price_risk_level", "VARCHAR(20) DEFAULT 'low'"),
        ("pricing_rule_version", "VARCHAR(20) DEFAULT 'PRICING_V3'"),
    ]
    for col_name, col_type in new_p_cols:
        if col_name not in p_cols:
            print(f"  Adding {col_name} to products")
            cur.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print(f"Migration completed for {db_path}")

if __name__ == "__main__":
    migrate_db("securemarket.db")
    migrate_db("../securemarket.db")
    migrate_db("backend/securemarket.db")
