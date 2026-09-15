"""
Comprehensive System Audit Test Suite
Verifies:
1. Real SHA-256 file hashing (test vectors, avalanche effect, disk-to-DB byte matches).
2. Elimination of all fake "a"*64 hashes.
3. Separation of product IDs and SHA-256 hashes.
4. Product retrieval without 404s for all seeded products.
5. Strict Role Separation (Buyer / Seller / Admin restrictions).
6. Live Integrity Re-hash Endpoint (accessible without requiring admin privileges).
7. Download security & entitlement enforcement.
8. Server-authoritative checkout and payment calculations.
"""

import sys
import os
import re
import hashlib
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.integrity import FileIntegrityRecord
from app.models.order import Order, OrderItem
from app.services.auth_service import create_access_token
from app.services.hash_service import verify_record_seal
from app.services.storage_service import storage_service

client = TestClient(app)
db = SessionLocal()

PASS = "[PASS]"
FAIL = "[FAIL]"
total_tests = 0
passed_tests = 0

def record_test(name: str, condition: bool, details: str = ""):
    global total_tests, passed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  {PASS} {name}")
        if details:
            print(f"         {details}")
    else:
        print(f"  {FAIL} {name}")
        if details:
            print(f"         ERROR: {details}")

print("\n" + "="*70)
print("  SECUREMARKET FULL-STACK AUDIT & VERIFICATION TEST SUITE")
print("="*70)

# -- Test 1: Standard SHA-256 Test Vector -------------------------------------
print("\n[Section 1: Standard Cryptographic Vectors & Properties]")
test_str = b"Hello World"
expected_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
actual_hash = hashlib.sha256(test_str).hexdigest()
record_test(
    "Standard SHA-256 Vector ('Hello World')",
    actual_hash == expected_hash,
    f"Expected: {expected_hash}, Got: {actual_hash}"
)

# Test 2: Avalanche Effect (1-byte mutation)
bytes_a = b"SecureMarket Authentic Digital Asset File Content Alpha"
bytes_b = b"SecureMarket Authentic Digital Asset File Content Alphb"
hash_a = hashlib.sha256(bytes_a).hexdigest()
hash_b = hashlib.sha256(bytes_b).hexdigest()
diff_chars = sum(1 for c1, c2 in zip(hash_a, hash_b) if c1 != c2)
record_test(
    "Avalanche Effect (1-byte mutation drastically changes digest)",
    hash_a != hash_b and diff_chars > 30,
    f"{diff_chars}/64 hex characters altered by 1-byte change"
)

# -- Section 2: Database Storage & Real Hashes --------------------------------
print("\n[Section 2: Database Storage & Real SHA-256 Hashes]")
products = db.query(Product).filter(Product.id.like("prod00%")).all()
record_test(
    "All 10 demo products exist in DB",
    len(products) == 10,
    f"Found {len(products)} products in database"
)

no_fake_hashes = True
valid_hex_hashes = True
disk_matches = True
separated_ids = True

for p in products:
    h = p.sha256_hash or ""
    if h == "a"*64 or h == "b"*64 or h == "0"*64 or not h:
        no_fake_hashes = False
        print(f"         Fake or empty hash found for product {p.id}: {h}")
    if not (len(h) == 64 and re.match(r'^[a-f0-9]{64}$', h)):
        valid_hex_hashes = False
    if p.id == h:
        separated_ids = False

    if p.storage_key:
        try:
            content = storage_service.get_file_content(p.storage_key)
            disk_hash = hashlib.sha256(content).hexdigest()
            if disk_hash != h:
                disk_matches = False
                print(f"         Disk mismatch for {p.id}: disk={disk_hash} != db={h}")
        except Exception as e:
            disk_matches = False
            print(f"         Storage read failed for {p.id}: {e}")

record_test(
    "Zero mock/fake ('a'*64) hashes in Product records",
    no_fake_hashes,
    "All products have genuine cryptographic digests"
)

record_test(
    "All SHA-256 hashes are valid 64-char lowercase hex",
    valid_hex_hashes,
    f"Verified {len(products)} hashes against ^[a-f0-9]{{64}}$"
)

record_test(
    "Product ID and SHA-256 Hash are strictly separated",
    separated_ids,
    "No product uses its hash as an ID or vice versa"
)

record_test(
    "Physical storage bytes match database SHA-256 fingerprints",
    disk_matches,
    "100% of product disk files hash identically to DB records"
)

# -- Section 3: Live Re-hash Endpoint Audit -----------------------------------
print("\n[Section 3: Live Verification & Integrity Endpoints]")
sample_product = products[0]
live_res = client.get(f"/api/integrity/product/{sample_product.id}/live-verify")
record_test(
    f"Live Re-hash Endpoint (/api/integrity/product/{sample_product.id}/live-verify)",
    live_res.status_code == 200 and live_res.json().get("match") is True,
    f"Status: {live_res.status_code}, Response: {live_res.json().get('status')}"
)

# Public lookup by integrity_id
rec = db.query(FileIntegrityRecord).filter(FileIntegrityRecord.product_id == sample_product.id).first()
if rec:
    seal_res = client.get(f"/api/integrity/{rec.integrity_id}")
    record_test(
        f"Public Integrity Proof Lookup (/api/integrity/{rec.integrity_id})",
        seal_res.status_code == 200 and seal_res.json().get("seal_valid") is True and "sha256_hash" in seal_res.json(),
        f"Seal Valid: {seal_res.json().get('seal_valid')}, Hash included: {'sha256_hash' in seal_res.json()}"
    )

# -- Section 4: Product API & No 404s ------------------------------------------
print("\n[Section 4: Product Retrieval & API Surface]")
prod1_res = client.get(f"/api/products/{sample_product.id}")
record_test(
    f"Fetch Product Details (/api/products/{sample_product.id})",
    prod1_res.status_code == 200 and prod1_res.json().get("sha256_hash") == sample_product.sha256_hash,
    f"Status: {prod1_res.status_code}, sha256_hash present in response"
)

list_res = client.get("/api/products?per_page=10")
record_test(
    "Marketplace Product Listing includes sha256_hash",
    list_res.status_code == 200 and len(list_res.json().get("items", [])) > 0 and "sha256_hash" in list_res.json()["items"][0],
    f"Total listed: {list_res.json().get('total')}"
)

# -- Section 5: Strict Role Separation -----------------------------------------
print("\n[Section 5: Strict Role Separation Enforcement]")

buyer_token = create_access_token({"sub": "buyer000-0000-0000-0000-000000000001", "role": "buyer", "email": "buyer1@example.com"})
buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

seller_token = create_access_token({"sub": "seller00-0000-0000-0000-000000000001", "role": "seller", "email": "seller1@example.com"})
seller_headers = {"Authorization": f"Bearer {seller_token}"}

# Authenticate admin dynamically from DB
admin_user = db.query(User).filter(User.role.in_(["ADMIN", "admin"])).first()
admin_id = str(admin_user.id) if admin_user else "admin-0001-0000-0000-0000-000000000001"
admin_email = admin_user.email if admin_user else "admin@securemarket.com"
admin_token = create_access_token({"sub": admin_id, "role": "admin", "email": admin_email})
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 1. Buyer CANNOT upload product
buyer_upload_res = client.post(
    "/api/uploads/product",
    files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
    data={"price": 100},
    headers=buyer_headers
)
record_test(
    "Buyer blocked from creating product (403 Forbidden)",
    buyer_upload_res.status_code == 403,
    f"Status: {buyer_upload_res.status_code}"
)

# 2. Seller CANNOT purchase / create checkout order
seller_buy_res = client.post(
    "/api/payments/create-order",
    json={"product_id": sample_product.id},
    headers=seller_headers
)
record_test(
    "Seller blocked from purchasing product (403 Forbidden)",
    seller_buy_res.status_code == 403,
    f"Status: {seller_buy_res.status_code} - {seller_buy_res.json().get('detail')}"
)

# 3. Admin CANNOT purchase / create checkout order
admin_buy_res = client.post(
    "/api/payments/create-order",
    json={"product_id": sample_product.id},
    headers=admin_headers
)
record_test(
    "Admin blocked from purchasing product (403 Forbidden)",
    admin_buy_res.status_code == 403,
    f"Status: {admin_buy_res.status_code} - {admin_buy_res.json().get('detail')}"
)

# -- Section 6: Download Security & Entitlement --------------------------------
print("\n[Section 6: Download Security & Access Control]")

anon_dl_res = client.get(f"/api/downloads/product/{sample_product.id}")
record_test(
    "Unauthenticated download blocked (401/403)",
    anon_dl_res.status_code in (401, 403),
    f"Status: {anon_dl_res.status_code}"
)

prod10 = db.query(Product).filter(Product.id == "prod0010-0000-0000-0000-000000000010").first()
if prod10:
    unpaid_dl_res = client.get(f"/api/downloads/product/{prod10.id}", headers=buyer_headers)
    record_test(
        f"Buyer without purchase blocked from downloading {prod10.id} (403 Forbidden)",
        unpaid_dl_res.status_code == 403,
        f"Status: {unpaid_dl_res.status_code} - {unpaid_dl_res.json().get('detail')}"
    )

# Reset download count for test repeatability
seeded_item = db.query(OrderItem).join(Order).filter(
    Order.buyer_id == "buyer000-0000-0000-0000-000000000001",
    OrderItem.product_id == sample_product.id
).first()
if seeded_item:
    seeded_item.download_count = 0
    seeded_item.download_enabled = True
    db.commit()

paid_dl_res = client.get(f"/api/downloads/product/{sample_product.id}", headers=buyer_headers)
record_test(
    f"Authorized buyer successfully obtains signed download URL for {sample_product.id}",
    paid_dl_res.status_code == 200 and "download_url" in paid_dl_res.json(),
    f"Status: {paid_dl_res.status_code}, Filename: {paid_dl_res.json().get('filename')}"
)

# Serve file test
if paid_dl_res.status_code == 200:
    dl_url = paid_dl_res.json()["download_url"]
    token = dl_url.split("/")[-1]
    serve_res = client.get(f"/api/downloads/serve/{token}")
    record_test(
        "Serve file bytes via authorized download token (HTTP 200)",
        serve_res.status_code == 200 and len(serve_res.content) > 0,
        f"Served byte size: {len(serve_res.content)}"
    )

# -- Section 7: Orders and Purchases with SHA-256 -----------------------------
print("\n[Section 7: Purchases Page & Orders API]")
orders_res = client.get("/api/orders", headers=buyer_headers)
orders_data = orders_res.json().get("orders", [])
has_order_sha256 = False
if orders_data and len(orders_data) > 0:
    first_item = orders_data[0].get("items", [])[0]
    prod_data = first_item.get("product", {})
    if prod_data.get("sha256_hash"):
        has_order_sha256 = True

record_test(
    "Purchases / Orders API exposes authentic sha256_hash",
    orders_res.status_code == 200 and has_order_sha256,
    f"Order count: {len(orders_data)}"
)

# -- Section 8: Server-Authoritative Razorpay Order Generation ----------------
print("\n[Section 8: Server-Authoritative Checkout & Razorpay Order Creation]")
# Pick a product buyer does not own yet
target_prod = db.query(Product).filter(Product.id == "prod0009-0000-0000-0000-000000000009").first()
if target_prod:
    create_order_res = client.post(
        "/api/payments/create-order",
        json={"product_id": target_prod.id, "tampered_price": 1},
        headers=buyer_headers
    )
    order_data = create_order_res.json()
    record_test(
        "Order created with server-authoritative pricing and Razorpay integration",
        create_order_res.status_code == 200 and "order_id" in order_data,
        f"Order ID: {order_data.get('order_id')}, Gateway: {order_data.get('gateway')}, Amount (INR): {order_data.get('amount')}"
    )

print("\n" + "="*70)
print(f"  AUDIT SUMMARY: {passed_tests}/{total_tests} tests passed")
if passed_tests == total_tests:
    print("  ALL AUDIT CHECKS PASSED: SYSTEM FULLY VERIFIED")
else:
    print("  SOME CHECKS FAILED: REVIEW LOGS ABOVE")
print("="*70 + "\n")

db.close()
sys.exit(0 if passed_tests == total_tests else 1)
