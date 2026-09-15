"""
run_role_and_payment_tests.py — Automated verification test suite for SecureMarket.
Tests:
1. Strict registration (BUYER, SELLER, rejecting ADMIN)
2. Role restriction & permission matrix:
   - BUYER -> cannot upload (403), cannot access seller dashboard (403), cannot access admin (403).
   - SELLER -> cannot buy/checkout (403), cannot access buyer orders (403), cannot access admin (403).
   - ADMIN -> cannot buy/checkout (403), cannot upload/sell (403), can manage and delete products.
3. Fee & tax calculation engine (paise arithmetic, 5% platform fee, 18% GST, 95% seller payout).
4. Admin soft-deletion of products.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.payout import Payout
from app.services.auth_service import hash_password, create_access_token
from app.services.fee_service import calculate_order_financials

client = TestClient(app)

def print_header(title: str):
    print(f"\n{'='*70}\n[TEST] {title}\n{'='*70}")

def run_tests():
    db = SessionLocal()
    passed = 0
    failed = 0

    def assert_test(cond, desc):
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {desc}")
            failed += 1

    # -------------------------------------------------------------
    # TEST 1: Server Financial Calculation Engine
    # -------------------------------------------------------------
    print_header("Marketplace Financial Calculation Engine (Paise Arithmetic)")
    fin = calculate_order_financials(price_inr=1000.0)
    assert_test(fin["subtotal"] == 1000.0, "Subtotal is ₹1,000.00")
    assert_test(fin["platform_fee"] == 50.0, "5% Platform fee is ₹50.00")
    assert_test(fin["tax"] == 189.0, "18% GST on (1000+50) is ₹189.00")
    assert_test(fin["total"] == 1239.0, "Total payable is ₹1,239.00")
    assert_test(fin["buyer_total_paise"] == 123900, "Paise exact: 123,900 paise")
    assert_test(fin["seller_payout"] == 950.0, "Seller Net Payout (95%) is ₹950.00")

    # -------------------------------------------------------------
    # TEST 2: Registration Validation
    # -------------------------------------------------------------
    print_header("Strict Account Registration & Anti-Escalation")
    uid = uuid.uuid4().hex[:6]
    
    # Try self-registering as ADMIN
    res = client.post("/api/auth/register", json={
        "email": f"hacker_{uid}@test.com",
        "username": f"hacker_{uid}",
        "password": "Password123!",
        "full_name": "Hacker",
        "role": "ADMIN"
    })
    assert_test(res.status_code in (400, 422), f"Self-registering as ADMIN is rejected (status {res.status_code})")

    # Register valid Buyer
    b_res = client.post("/api/auth/register", json={
        "email": f"buyer_test_{uid}@test.com",
        "username": f"buyer_{uid}",
        "password": "Password123!",
        "full_name": "Test Buyer",
        "role": "BUYER"
    })
    assert_test(b_res.status_code == 201, "Buyer registration succeeds (201)")
    buyer_token = b_res.json()["access_token"]
    buyer_user_id = b_res.json()["user"]["id"]

    # Register valid Seller
    s_res = client.post("/api/auth/register", json={
        "email": f"seller_test_{uid}@test.com",
        "username": f"seller_{uid}",
        "password": "Password123!",
        "full_name": "Test Seller",
        "role": "SELLER"
    })
    assert_test(s_res.status_code == 201, "Seller registration succeeds (201)")
    seller_token = s_res.json()["access_token"]
    seller_user_id = s_res.json()["user"]["id"]

    # Create test Admin
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            email=f"admin_{uid}@test.com",
            username=f"admin_{uid}",
            hashed_password=hash_password("Admin123!"),
            full_name="Platform Admin",
            role="ADMIN",
            roles="ADMIN"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
    admin_token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email})

    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # -------------------------------------------------------------
    # TEST 3: Dynamic Role Hopping Block
    # -------------------------------------------------------------
    print_header("Dynamic Role Hopping (/become-seller) Protection")
    hop_res = client.post("/api/auth/become-seller", headers=buyer_headers)
    assert_test(hop_res.status_code == 400, "Buyer cannot hop to seller via /become-seller (400 Forbidden)")

    # -------------------------------------------------------------
    # TEST 4: Strict Role Separation Permissions Matrix
    # -------------------------------------------------------------
    print_header("Strict Role Separation Permission Matrix")

    # A. Buyer restrictions
    b_seller_dash = client.get("/api/seller/dashboard", headers=buyer_headers)
    assert_test(b_seller_dash.status_code == 403, f"Buyer blocked from /api/seller/dashboard ({b_seller_dash.status_code})")

    b_admin_dash = client.get("/api/admin/products", headers=buyer_headers)
    assert_test(b_admin_dash.status_code == 403, f"Buyer blocked from /api/admin/products ({b_admin_dash.status_code})")

    # B. Seller restrictions
    s_orders = client.get("/api/orders", headers=seller_headers)
    assert_test(s_orders.status_code == 403, f"Seller blocked from /api/orders ({s_orders.status_code})")

    s_admin = client.get("/api/admin/stats", headers=seller_headers)
    assert_test(s_admin.status_code == 403, f"Seller blocked from /api/admin/stats ({s_admin.status_code})")

    # C. Admin restrictions
    a_upload = client.post("/api/uploads/product", headers=admin_headers)
    assert_test(a_upload.status_code == 403, f"Admin blocked from selling/uploading files ({a_upload.status_code})")

    # -------------------------------------------------------------
    # TEST 5: Pre-purchase Checkout Calculation Endpoint
    # -------------------------------------------------------------
    print_header("Pre-Purchase Checkout Breakdown API (/calculate-checkout)")
    # Get or create a sample published product
    test_prod = db.query(Product).filter(Product.status == "published", Product.is_active == True).first()
    if not test_prod:
        test_prod = Product(
            seller_id=str(seller_user_id),
            title="Secure Python SDK Framework",
            short_description="Enterprise grade secure toolkit",
            price=499.0,
            status="published",
            is_active=True,
            scan_status="clean"
        )
        db.add(test_prod)
        db.commit()
        db.refresh(test_prod)

    calc_res = client.get(f"/api/payments/calculate-checkout?product_id={test_prod.id}")
    assert_test(calc_res.status_code == 200, "Calculate-checkout endpoint returns 200")
    cdata = calc_res.json()
    assert_test(cdata["subtotal"] == float(test_prod.price), f"Subtotal matches product price ₹{test_prod.price}")
    assert_test(cdata["platform_fee"] == round(test_prod.price * 0.05, 2), "Platform fee is exactly 5%")
    assert_test(cdata["total_amount"] > test_prod.price, "Total includes platform fee and GST")

    # -------------------------------------------------------------
    # TEST 6: Purchase Flow Strict Role Enforcement
    # -------------------------------------------------------------
    print_header("Purchase Flow Strict Role Enforcement")

    # Seller trying to buy product
    s_buy_res = client.post("/api/payments/create-order", json={"product_id": str(test_prod.id)}, headers=seller_headers)
    assert_test(s_buy_res.status_code == 403, f"Seller blocked from purchasing product ({s_buy_res.status_code})")

    # Admin trying to buy product
    a_buy_res = client.post("/api/payments/create-order", json={"product_id": str(test_prod.id)}, headers=admin_headers)
    assert_test(a_buy_res.status_code == 403, f"Admin blocked from purchasing product ({a_buy_res.status_code})")

    # Buyer buying product
    b_buy_res = client.post("/api/payments/create-order", json={"product_id": str(test_prod.id)}, headers=buyer_headers)
    assert_test(b_buy_res.status_code == 200, f"Buyer successfully created purchase order ({b_buy_res.status_code})")
    order_data = b_buy_res.json()
    order_id = order_data["order_id"]

    # Verify Payout ledger entry was created
    payout_entry = db.query(Payout).filter(Payout.order_id == order_id).first()
    assert_test(payout_entry is not None, "Seller payout ledger record was automatically generated")
    if payout_entry:
        assert_test(payout_entry.gross_amount == test_prod.price, f"Payout gross is ₹{test_prod.price}")
        assert_test(payout_entry.seller_payout == round(test_prod.price * 0.95, 2), "Seller net royalty is 95%")

    # -------------------------------------------------------------
    # TEST 7: Admin Soft-Delete of Product
    # -------------------------------------------------------------
    print_header("Admin Product Soft-Deletion")
    del_res = client.delete(f"/api/admin/products/{test_prod.id}?reason=Test+Compliance+Removal", headers=admin_headers)
    assert_test(del_res.status_code == 200, f"Admin soft-delete returns 200: {del_res.json().get('message')}")

    db.refresh(test_prod)
    assert_test(test_prod.status == "REMOVED_BY_ADMIN", f"Product status is now 'REMOVED_BY_ADMIN' (got '{test_prod.status}')")
    assert_test(test_prod.is_active == False, "Product is_active is now False")

    # Verify delisted from public marketplace
    market_res = client.get("/api/products")
    market_items = market_res.json()["items"]
    is_in_market = any(item["id"] == str(test_prod.id) for item in market_items)
    assert_test(not is_in_market, "Soft-deleted product is hidden from marketplace catalog")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print(f"\n{'='*70}")
    print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
    print(f"{'='*70}\n")
    db.close()
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
