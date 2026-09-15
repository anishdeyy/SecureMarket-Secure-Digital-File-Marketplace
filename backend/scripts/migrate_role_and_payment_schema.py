"""
migrate_role_and_payment_schema.py
Applies schema updates for strict role separation, marketplace fee/tax architecture,
payouts table, refunds table, and normalizes user roles (buyer1 -> BUYER, seller1 -> SELLER, admin -> ADMIN).
"""

import os
import sqlite3

DB_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "securemarket.db"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "securemarket.db"),
]

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        print(f"[SKIP] DB does not exist: {db_path}")
        return

    print(f"\n[MIGRATE] Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    def get_columns(table_name: str):
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]

    # 1. Update users table
    user_cols = get_columns("users")
    if "role" not in user_cols:
        print("  Adding 'role' column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'BUYER'")
    if "roles" not in user_cols:
        print("  Adding 'roles' column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN roles VARCHAR(200) DEFAULT 'BUYER'")

    # 2. Update orders table
    order_cols = get_columns("orders")
    order_additions = [
        ("subtotal", "FLOAT DEFAULT 0.0"),
        ("platform_fee", "FLOAT DEFAULT 0.0"),
        ("service_fee", "FLOAT DEFAULT 0.0"),
        ("tax", "FLOAT DEFAULT 0.0"),
        ("tax_rate", "FLOAT DEFAULT 0.18"),
        ("platform_fee_percent", "FLOAT DEFAULT 0.05"),
        ("pricing_rule_version", "VARCHAR(50) DEFAULT 'PRICING_V1'"),
    ]
    for col_name, col_type in order_additions:
        if col_name not in order_cols:
            print(f"  Adding '{col_name}' column to orders table...")
            cur.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")

    # 3. Update order_items table
    item_cols = get_columns("order_items")
    item_additions = [
        ("seller_id", "VARCHAR(36)"),
        ("quantity", "INTEGER DEFAULT 1"),
        ("subtotal", "FLOAT DEFAULT 0.0"),
    ]
    for col_name, col_type in item_additions:
        if col_name not in item_cols:
            print(f"  Adding '{col_name}' column to order_items table...")
            cur.execute(f"ALTER TABLE order_items ADD COLUMN {col_name} {col_type}")

    # 4. Create payouts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payouts (
        id VARCHAR(36) PRIMARY KEY,
        order_id VARCHAR(36) NOT NULL,
        seller_id VARCHAR(36) NOT NULL,
        product_id VARCHAR(36),
        gross_amount FLOAT NOT NULL,
        platform_fee FLOAT NOT NULL DEFAULT 0.0,
        other_fee FLOAT NOT NULL DEFAULT 0.0,
        seller_payout FLOAT NOT NULL,
        royalty_rate FLOAT DEFAULT 0.95,
        currency VARCHAR(10) DEFAULT 'INR',
        status VARCHAR(50) DEFAULT 'pending_payout',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
    )
    """)
    print("  Ensured 'payouts' table exists.")

    # 5. Create refunds table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS refunds (
        id VARCHAR(36) PRIMARY KEY,
        order_id VARCHAR(36) NOT NULL,
        buyer_id VARCHAR(36) NOT NULL,
        amount FLOAT NOT NULL,
        currency VARCHAR(10) DEFAULT 'INR',
        reason TEXT,
        status VARCHAR(50) DEFAULT 'REFUND_REQUESTED',
        processed_by VARCHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("  Ensured 'refunds' table exists.")

    # 6. Normalize user roles strictly
    print("  Normalizing user roles...")
    cur.execute("UPDATE users SET role = 'ADMIN', roles = 'ADMIN' WHERE username = 'admin' OR email LIKE 'admin%' OR roles LIKE '%admin%'")
    cur.execute("""
    UPDATE users SET role = 'SELLER', roles = 'SELLER' 
    WHERE (username LIKE 'seller%' OR email LIKE 'seller%' OR roles LIKE '%seller%') 
      AND username != 'admin' AND role != 'ADMIN' AND username != 'buyer1'
    """)
    cur.execute("""
    UPDATE users SET role = 'BUYER', roles = 'BUYER' 
    WHERE username = 'buyer1' OR email LIKE 'buyer%' OR role IS NULL OR role = '' OR (role != 'ADMIN' AND role != 'SELLER')
    """)
    cur.execute("UPDATE users SET role = 'BUYER', roles = 'BUYER' WHERE username = 'buyer1'")
    
    conn.commit()

    cur.execute("SELECT id, username, email, role, roles FROM users")
    users = cur.fetchall()
    print("  Current users and roles:")
    for u in users:
        print(f"    - User: {u[1]:<12} | Role: {u[3]:<8} | Roles: {u[4]}")

    conn.close()
    print(f"[DONE] Migration completed for: {db_path}")

if __name__ == "__main__":
    for p in set(DB_PATHS):
        migrate_db(p)
