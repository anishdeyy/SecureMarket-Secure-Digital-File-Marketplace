"""
Verification test suite for SecureMarket:
1. SHA-256 Hiding & Endpoint Sanitization (Part A)
2. Verified Buyer Review System (Part B)
3. Dynamic Price Ceiling Engine & Maximum-Price Protection (Part C)
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.models.integrity import FileIntegrityRecord
from app.services.auth_service import hash_password, create_access_token
from app.services.pricing_service import calculate_product_pricing

client = TestClient(app)

def run_tests():
    db = SessionLocal()
    print("==================================================")
    print("STARTING SECUREMARKET VERIFICATION TEST SUITE")
    print("==================================================")

    passed = 0
    total = 0

    def test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name} - {details}")

    test_prod = None
    seller_user = None
    buyer_user = None
    stranger_user = None
    try:
        # Set up test users: Admin, Seller, Buyer, Unrelated Buyer
        suffix = uuid.uuid4().hex[:6]
        admin_user = db.query(User).filter(User.roles.contains("admin")).first()
        if not admin_user:
            admin_user = User(
                id=str(uuid.uuid4()),
                email=f"admin_{suffix}@example.com",
                username=f"admin_{suffix}",
                hashed_password=hash_password("adminpass123"),
                roles="admin,seller,buyer",
                is_active=True
            )
            db.add(admin_user)
            db.commit()

        seller_user = User(
            id=str(uuid.uuid4()),
            email=f"seller_{suffix}@example.com",
            username=f"seller_{suffix}",
            hashed_password=hash_password("pass123"),
            roles="seller,buyer",
            seller_approved=True,
            is_active=True
        )
        db.add(seller_user)

        buyer_user = User(
            id=str(uuid.uuid4()),
            email=f"buyer_{suffix}@example.com",
            username=f"buyer_{suffix}",
            hashed_password=hash_password("pass123"),
            roles="buyer",
            is_active=True
        )
        db.add(buyer_user)

        stranger_user = User(
            id=str(uuid.uuid4()),
            email=f"stranger_{suffix}@example.com",
            username=f"stranger_{suffix}",
            hashed_password=hash_password("pass123"),
            roles="buyer",
            is_active=True
        )
        db.add(stranger_user)
        db.commit()

        # Auth tokens
        admin_token = create_access_token({"sub": str(admin_user.id)})
        seller_token = create_access_token({"sub": str(seller_user.id)})
        buyer_token = create_access_token({"sub": str(buyer_user.id)})
        stranger_token = create_access_token({"sub": str(stranger_user.id)})

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        seller_headers = {"Authorization": f"Bearer {seller_token}"}
        buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
        stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

        test_prod = Product(
            id=str(uuid.uuid4()),
            seller_id=str(seller_user.id),
            title="Tiny TXT Notes",
            description="12 bytes text test file",
            category="Documents",
            price=25.0,
            file_extension="txt",
            file_size_bytes=12,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            integrity_id=f"INT-TEST-{suffix}".upper(),
            storage_key="test/tiny.txt",
            status="published",
            scan_status="clean"
        )
        low_pricing = calculate_product_pricing(test_prod)
        test_prod.suggested_price = low_pricing["suggested_price"]
        test_prod.suggested_price_min = low_pricing["suggested_price_min"]
        test_prod.suggested_price_max = low_pricing["suggested_price_max"]
        test_prod.maximum_allowed_price = low_pricing["maximum_allowed_price"]
        test_prod.value_score = low_pricing["value_score"]
        test_prod.price = low_pricing["suggested_price"]
        test_prod.price_status = "ok"
        db.add(test_prod)

        # Integrity record with valid HMAC seal
        from app.services.hash_service import generate_integrity_record
        integ_rec = generate_integrity_record(
            db=db,
            product_id=test_prod.id,
            seller_id=seller_user.id,
            sha256_hash=test_prod.sha256_hash,
            file_size=12,
            original_filename="tiny.txt",
            mime_type="text/plain"
        )
        test_prod.integrity_id = integ_rec.integrity_id
        db.commit()

        print("\n--- PART A: SHA-256 HIDING & ACCESS CONTROL TESTS ---")
        # 1. Public Marketplace Product Detail hides sha256_hash & storage_key
        res = client.get(f"/api/products/{test_prod.id}")
        test("Public GET /api/products/{id} returns 200", res.status_code == 200)
        data = res.json()
        test("Public GET /api/products/{id} hides sha256_hash", "sha256_hash" not in data or data.get("sha256_hash") is None)
        test("Public GET /api/products/{id} hides storage_key", "storage_key" not in data or data.get("storage_key") is None)
        test("Public GET /api/products/{id} includes security_status trust cards", "security_status" in data and data["security_status"]["integrity_verified"] is True)

        # 2. Public /api/integrity/{id} hides raw sha256_hash
        res_int = client.get(f"/api/integrity/{test_prod.integrity_id}")
        test("Public GET /api/integrity/{id} returns 200", res_int.status_code == 200)
        int_data = res_int.json()
        test("Public GET /api/integrity/{id} hides raw sha256_hash", "sha256_hash" not in int_data)
        test("Public GET /api/integrity/{id} returns overall_ok", int_data.get("overall_ok") is True)

        # 3. Authenticated buyer /api/integrity/product/{id} hides raw sha256_hash
        res_b_int = client.get(f"/api/integrity/product/{test_prod.id}", headers=buyer_headers)
        test("Buyer GET /api/integrity/product/{id} returns 200", res_b_int.status_code == 200)
        test("Buyer GET /api/integrity/product/{id} hides raw sha256_hash", "sha256_hash" not in res_b_int.json())

        # 4. Non-admin GET /api/admin/products/{id}/security-details is blocked (403)
        res_non_admin = client.get(f"/api/admin/products/{test_prod.id}/security-details", headers=buyer_headers)
        test("Buyer GET /api/admin/products/{id}/security-details is 403 Forbidden", res_non_admin.status_code == 403)

        # 5. Admin GET /api/admin/products/{id}/security-details returns full diagnostic details
        res_admin = client.get(f"/api/admin/products/{test_prod.id}/security-details", headers=admin_headers)
        test("Admin GET /api/admin/products/{id}/security-details returns 200", res_admin.status_code == 200)
        admin_data = res_admin.json()
        test("Admin gets full sha256_hash", admin_data.get("sha256_hash") == test_prod.sha256_hash)
        test("Admin gets storage_key", admin_data.get("storage_key") == test_prod.storage_key)
        test("Admin gets integrity_record", "integrity_record" in admin_data)

        print("\n--- PART B: VERIFIED BUYER REVIEW SYSTEM TESTS ---")
        # 6. Unpurchased stranger cannot submit a review
        res_rev_stranger = client.post(
            f"/api/products/{test_prod.id}/reviews",
            json={"rating": 5, "comment": "Great product!"},
            headers=stranger_headers
        )
        test("Unpurchased user review blocked (403)", res_rev_stranger.status_code == 403)

        # 7. Seller cannot review their own product
        res_rev_seller = client.post(
            f"/api/products/{test_prod.id}/reviews",
            json={"rating": 5, "comment": "I made this, it is amazing!"},
            headers=seller_headers
        )
        test("Seller self-review blocked (403)", res_rev_seller.status_code == 403)

        # 8. Create a paid order for the buyer
        order = Order(
            id=str(uuid.uuid4()),
            order_number=f"ORD-TEST-{suffix}",
            buyer_id=str(buyer_user.id),
            status="paid",
            total_amount=test_prod.price,
            created_at=datetime.now(timezone.utc)
        )
        db.add(order)
        order_item = OrderItem(
            id=str(uuid.uuid4()),
            order_id=order.id,
            product_id=test_prod.id,
            price_at_purchase=test_prod.price,
            download_enabled=True,
            download_count=0,
            download_limit=10
        )
        db.add(order_item)
        db.commit()

        # 9. Paid buyer submits a review
        res_rev_paid = client.post(
            f"/api/products/{test_prod.id}/reviews",
            json={"rating": 5, "comment": "Verified buyer: Excellent digital notes!"},
            headers=buyer_headers
        )
        test("Paid buyer submit review succeeds (200)", res_rev_paid.status_code == 200)
        review_data = res_rev_paid.json()
        review_id = review_data.get("id")
        test("Review has is_verified_purchase flag", review_data.get("is_verified_purchase") is True)

        # 10. Duplicate review by same buyer is blocked
        res_rev_dup = client.post(
            f"/api/products/{test_prod.id}/reviews",
            json={"rating": 4, "comment": "Posting second review"},
            headers=buyer_headers
        )
        test("Duplicate review blocked (400)", res_rev_dup.status_code == 400)

        # 11. Product average rating recalculates
        db.refresh(test_prod)
        test("Product avg_rating updated in DB", test_prod.avg_rating == 5.0)
        test("Product review_count updated in DB", test_prod.review_count == 1)

        # 12. Buyer updates their review
        res_rev_edit = client.put(
            f"/api/reviews/{review_id}",
            json={"rating": 4, "comment": "Updated: Really good, 4 stars now."},
            headers=buyer_headers
        )
        test("Buyer edit review succeeds (200)", res_rev_edit.status_code == 200)
        db.refresh(test_prod)
        test("Product avg_rating updated to 4.0", test_prod.avg_rating == 4.0)

        # 13. GET /api/products/{id}/reviews returns can_review=False and user_review
        res_reviews_list = client.get(f"/api/products/{test_prod.id}/reviews", headers=buyer_headers)
        test("GET /api/products/{id}/reviews succeeds (200)", res_reviews_list.status_code == 200)
        list_data = res_reviews_list.json()
        test("GET /api/products/{id}/reviews reports can_review=False (already reviewed)", list_data.get("can_review") is False)
        test("GET /api/products/{id}/reviews returns user_review object", list_data.get("user_review") is not None)

        print("\n--- PART C: DYNAMIC PRICING ENGINE & MAXIMUM-PRICE PROTECTION TESTS ---")
        # 14. Low-content file ceiling is <= 100 INR
        test("12-byte TXT file ceiling <= 100 INR", test_prod.maximum_allowed_price <= 100.0)

        # 15. Attempt to update product price to INR 1,00,000 (exceeds ceiling) -> rejected 400
        res_price_high = client.put(
            f"/api/products/{test_prod.id}",
            json={"price": 100000.0, "title": "Tiny TXT Notes Overpriced"},
            headers=seller_headers
        )
        test("Updating price to INR 1,00,000 rejected (400 PRICE_EXCEEDS_PLATFORM_LIMIT)", res_price_high.status_code == 400)
        test("Rejection error message mentions maximum limit", "maximum" in res_price_high.text.lower() or "limit" in res_price_high.text.lower())

        # 16. Updating price within ceiling (e.g. INR 49) -> succeeds 200
        res_price_valid = client.put(
            f"/api/products/{test_prod.id}",
            json={"price": 49.0, "title": "Tiny TXT Notes Fair Price"},
            headers=seller_headers
        )
        test("Updating price within ceiling (INR 49) succeeds (200)", res_price_valid.status_code == 200)

        # 17. Clean up test review
        res_del_rev = client.delete(f"/api/reviews/{review_id}", headers=buyer_headers)
        test("Buyer delete review succeeds (200)", res_del_rev.status_code == 200)
        db.refresh(test_prod)
        test("Product review_count is now 0", test_prod.review_count == 0)

        print("\n==================================================")
        print(f"RESULTS: {passed}/{total} TESTS PASSED")
        print("==================================================")
        if passed == total:
            print(">>> ALL VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")
            return 0
        else:
            print(f">>> {total - passed} TEST(S) FAILED <<<")
            return 1

    finally:
        # Cleanup created test entities
        try:
            if test_prod:
                db.query(Review).filter(Review.product_id == test_prod.id).delete()
                db.query(OrderItem).filter(OrderItem.product_id == test_prod.id).delete()
                db.query(FileIntegrityRecord).filter(FileIntegrityRecord.product_id == test_prod.id).delete()
                db.query(Product).filter(Product.id == test_prod.id).delete()
            if buyer_user:
                db.query(Order).filter(Order.buyer_id == str(buyer_user.id)).delete()
            users_to_del = [u.id for u in [seller_user, buyer_user, stranger_user] if u]
            if users_to_del:
                db.query(User).filter(User.id.in_(users_to_del)).delete()
            db.commit()
        except Exception as e:
            print(f"Cleanup error (non-fatal): {e}")
        db.close()

if __name__ == "__main__":
    sys.exit(run_tests())
