"""
run_quality_pricing_payment_tests.py
Comprehensive automated test suite for SecureMarket Quality & Risk Assessment,
Product-Specific Dynamic Pricing Ceilings, and Transparent Checkout Architecture.
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
from app.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payout import Payout
from app.models.refund import Refund
from app.services.auth_service import hash_password, create_access_token
from app.services.quality_service import (
    determine_quality_level,
    calculate_weighted_quality_score,
    detect_content_type,
    compute_listing_risk,
    clean_audience_description,
    _heuristic_quality_assessment
)
from app.services.pricing_service import (
    extract_content_metrics,
    calculate_product_value_score,
    calculate_product_pricing,
    validate_price_limit,
    GLOBAL_PLATFORM_MAX_PRICE_INR
)
from app.services.fee_service import (
    calculate_order_financials,
    record_seller_payout,
    complete_seller_payout
)

client = TestClient(app)

def print_header(title: str):
    print(f"\n{'='*75}\n[TEST] {title}\n{'='*75}")

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
    # 1. QUALITY LABELS AND THRESHOLDS
    # -------------------------------------------------------------
    print_header("1. Quality Tiers & Exact Label Mapping")
    assert_test(determine_quality_level(95) == "Excellent", "Score 95/100 maps to 'Excellent'")
    assert_test(determine_quality_level(90) == "Excellent", "Score 90/100 maps to 'Excellent'")
    assert_test(determine_quality_level(88) == "Good", "Score 88/100 maps to 'Good'")
    assert_test(determine_quality_level(79) == "Good", "Score 79/100 maps to 'Good' (NOT 'Medium')")
    assert_test(determine_quality_level(75) == "Good", "Score 75/100 maps to 'Good'")
    assert_test(determine_quality_level(74) == "Fair", "Score 74/100 maps to 'Fair'")
    assert_test(determine_quality_level(60) == "Fair", "Score 60/100 maps to 'Fair'")
    assert_test(determine_quality_level(59) == "Low", "Score 59/100 maps to 'Low'")
    assert_test(determine_quality_level(40) == "Low", "Score 40/100 maps to 'Low'")
    assert_test(determine_quality_level(39) == "Very Low", "Score 39/100 maps to 'Very Low'")
    assert_test(determine_quality_level(15) == "Very Low", "Score 15/100 maps to 'Very Low'")

    # -------------------------------------------------------------
    # 2. CONTENT TYPE DETECTION & RUBRICS
    # -------------------------------------------------------------
    print_header("2. Content-Type Aware Detection & Rubrics")
    
    # Research Paper
    academic_text = (
        "Abstract: In this paper, we propose a decentralized architecture for crowdsensed data streams. "
        "Introduction: Mobile crowdsensing faces critical challenges in privacy and truth discovery. "
        "Methodology: We formulate an additive secret sharing scheme over Ethereum smart contracts. "
        "References: [1] IEEE Trans. Mobile Comput., 2024. [2] ACM CCS, 2023."
    )
    c_type_paper = detect_content_type(academic_text, "paper.pdf", "application/pdf")
    assert_test(c_type_paper == "Research Paper", f"Academic paper detected as '{c_type_paper}'")

    # Source Code
    code_text = "import os\nimport sys\ndef compute_metrics(x: int) -> float:\n    return float(x * 1.5)\nclass ServiceRunner:\n    pass"
    c_type_code = detect_content_type(code_text, "service.py", "text/x-python")
    assert_test(c_type_code == "Source Code", f"Python file detected as '{c_type_code}'")

    # Presentation
    pres_text = "Slide 1: Phishing Security Overview\nAgenda:\n- Email threat landscape\nSlide 2: Social engineering vectors"
    c_type_pres = detect_content_type(pres_text, "phishing.pptx", "application/vnd.ms-powerpoint")
    assert_test(c_type_pres == "Presentation", f"Slide deck detected as '{c_type_pres}'")

    # Simple TXT
    c_type_txt = detect_content_type("DKM Details.", "DKM Details.txt", "text/plain")
    assert_test(c_type_txt in {"Document", "Other"}, "Small text file classified appropriately")

    # Clean audience description (No raw filenames)
    raw_desc = "Buyers looking for structured resources related to Building_a_Secure_Knowledge_Marketplace_Over_Crowdsensed_Data_Streams.pdf"
    cleaned = clean_audience_description(raw_desc, filename="paper.pdf", title="Building a Secure Knowledge Marketplace")
    assert_test(".pdf" not in cleaned and "_" not in cleaned, f"Cleaned audience: '{cleaned}' (no raw filename or extension)")

    # -------------------------------------------------------------
    # 3. LISTING RISK (DECOUPLED FROM QUALITY)
    # -------------------------------------------------------------
    print_header("3. Listing Risk Decoupled From Quality Score")
    
    # Research paper: Quality 79, Price ₹3,000, Suggested ₹2,499, Max ₹7,050
    risk_paper = compute_listing_risk(
        price=3000.0,
        quality_score=79,
        suggested_price=2499.0,
        maximum_allowed_price=7050.0,
        content_type="Research Paper",
        is_unique=True,
        malware_clean=True,
        word_count=978
    )
    assert_test(risk_paper["risk_level"] in {"low", "medium"}, f"₹3,000 Research Paper has {risk_paper['risk_level']} risk (NOT high)")
    assert_test(risk_paper["risk_score"] < 50, f"Risk score is {risk_paper['risk_score']} (< 50)")
    assert_test(len(risk_paper["positive_checks"]) >= 2, "Positive checks included")

    # Low Quality (25) with high price (₹10,000) -> High / Critical Risk
    risk_junk = compute_listing_risk(
        price=10000.0,
        quality_score=25,
        suggested_price=50.0,
        maximum_allowed_price=100.0,
        content_type="Simple TXT",
        is_unique=True,
        malware_clean=True,
        word_count=10
    )
    assert_test(risk_junk["risk_level"] in {"high", "critical"}, f"Low quality + huge price receives {risk_junk['risk_level']} risk")
    assert_test(len(risk_junk["risk_reasons"]) > 0, "Risk reasons clearly explained")

    # -------------------------------------------------------------
    # 4. PRODUCT-SPECIFIC PRICING CEILINGS
    # -------------------------------------------------------------
    print_header("4. Product-Specific Dynamic Pricing Ceilings")
    
    # Mock product helper
    class MockProduct:
        def __init__(self, title, category, ext, file_size, words, loc=0, pages=1, desc=""):
            self.title = title
            self.category = category
            self.file_extension = ext
            self.file_size_bytes = file_size
            self.description = desc or (("word " * words) if words else "")
            self.short_description = ""
            self.summary = ""
            self.num_pages = pages
            self.original_filename = f"{title}.{ext}"

    # 1. 12-byte TXT
    p_txt = MockProduct("DKM Details", "Documents", "txt", 12, words=2)
    calc_txt = calculate_product_pricing(p_txt, extracted_text="DKM Details.")
    assert_test(calc_txt["maximum_allowed_price"] <= 100.0, f"12-byte TXT maximum is ₹{calc_txt['maximum_allowed_price']} (<= ₹100)")
    assert_test(calc_txt["suggested_price"] <= 49.0, f"12-byte TXT suggested is ₹{calc_txt['suggested_price']} (<= ₹49)")

    # 2. 978-word Research Paper (Quality 79)
    class MockQA:
        def __init__(self, score, c_type):
            self.overall_score = score
            self.detected_content_type = c_type
            
    p_paper = MockProduct("Secure Knowledge Marketplace", "Documents", "pdf", 2300000, words=978, pages=12)
    calc_paper = calculate_product_pricing(p_paper, extracted_text=academic_text + (" word" * 900), quality_analysis=MockQA(79, "Research Paper"))
    assert_test(calc_paper["maximum_allowed_price"] >= 3500.0, f"978-word Paper max is ₹{calc_paper['maximum_allowed_price']} (>= ₹3,500, not hardcoded ₹3,000)")
    assert_test(calc_paper["suggested_price"] >= 800.0, f"978-word Paper suggested is ₹{calc_paper['suggested_price']} (>= ₹800)")

    # 3. 120-page Comprehensive Research Paper (Quality 92)
    p_thesis = MockProduct("Comprehensive Distributed Systems Thesis", "Documents", "pdf", 15000000, words=35000, pages=120)
    calc_thesis = calculate_product_pricing(p_thesis, extracted_text=academic_text + (" word" * 34000), quality_analysis=MockQA(92, "Research Paper"))
    assert_test(calc_thesis["maximum_allowed_price"] >= 7000.0, f"120-page Paper max is ₹{calc_thesis['maximum_allowed_price']} (>= ₹7,000)")

    # 4. 8,000-line Source Code Project (Quality 91)
    p_code = MockProduct("Autonomous Trading Engine", "Programming", "py", 350000, words=8000, loc=8000)
    calc_code = calculate_product_pricing(p_code, extracted_text=code_text * 500, quality_analysis=MockQA(91, "Source Code"))
    assert_test(calc_code["maximum_allowed_price"] >= 10000.0, f"Source code max is ₹{calc_code['maximum_allowed_price']} (>= ₹10,000)")

    # 5. Simple 8-slide presentation (Quality 55)
    p_pres = MockProduct("Introductory Team Presentation", "Documents", "pptx", 45000, words=200)
    calc_pres = calculate_product_pricing(p_pres, extracted_text=pres_text, quality_analysis=MockQA(55, "Presentation"))
    assert_test(calc_pres["maximum_allowed_price"] <= 1000.0, f"Brief presentation max is ₹{calc_pres['maximum_allowed_price']} (<= ₹1,000)")

    # -------------------------------------------------------------
    # 5. CHECKOUT AND FEE ACCOUNTING
    # -------------------------------------------------------------
    print_header("5. Transparent Checkout, Fees, and Seller Payouts")
    
    fin = calculate_order_financials(price_inr=3000.0)
    assert_test(fin["subtotal"] == 3000.0, "Subtotal is ₹3,000.00")
    assert_test(fin["platform_fee"] == 150.0, "5% Platform fee is ₹150.00")
    assert_test(fin["tax"] == 567.0, "18% GST on (3000+150) is ₹567.00")
    assert_test(fin["total"] == 3717.0, "Buyer total payable is ₹3,717.00")
    assert_test(fin["buyer_total_paise"] == 371700, "Paise exact: 371,700 paise")
    
    # Seller payout: must exclude buyer tax!
    assert_test(fin["seller_gross"] == 3000.0, "Seller gross sale is ₹3,000.00")
    assert_test(fin["seller_fee"] == 150.0, "Seller marketplace fee is ₹150.00")
    assert_test(fin["seller_payout"] == 2850.0, "Seller net payout is ₹2,850.00 (95% of subtotal, NOT including tax)")

    # Active fee lines: verify no royalty or waived row
    labels = [line["label"] for line in fin["fee_lines"]]
    assert_test(any("Product price" in l for l in labels), "Includes 'Product price'")
    assert_test(any("Platform fee" in l for l in labels), "Includes 'Platform fee'")
    assert_test(any("Tax" in l for l in labels), "Includes 'Applicable Tax'")
    assert_test(not any("Royalty" in l or "Waived" in l for l in labels), "NO 'Royalty' or 'Waived' lines in checkout!")

    # -------------------------------------------------------------
    # 6. PRICE CEILING VALIDATION AT CHECKOUT
    # -------------------------------------------------------------
    print_header("6. Price Ceiling Validation at Checkout")
    
    # Create test buyer & seller
    uid = uuid.uuid4().hex[:6]
    buyer = User(
        email=f"buyer_checkout_{uid}@test.com",
        username=f"buyer_checkout_{uid}",
        hashed_password=hash_password("Password123!"),
        role="BUYER",
        roles="BUYER"
    )
    seller = User(
        email=f"seller_checkout_{uid}@test.com",
        username=f"seller_checkout_{uid}",
        hashed_password=hash_password("Password123!"),
        role="SELLER",
        roles="SELLER"
    )
    db.add(buyer)
    db.add(seller)
    db.commit()

    # Product with price exceeding ceiling
    p_exceeded = Product(
        title=f"Overpriced Text File {uid}",
        seller_id=str(seller.id),
        price=5000.0,
        maximum_allowed_price=100.0,
        suggested_price=25.0,
        status="published",
        is_active=True
    )
    db.add(p_exceeded)
    db.commit()

    buyer_token = create_access_token({"sub": str(buyer.id), "role": "BUYER"})
    headers = {"Authorization": f"Bearer {buyer_token}"}

    # Attempt checkout on overpriced product -> should fail with 400
    res_over = client.get(f"/api/payments/calculate-checkout?product_id={p_exceeded.id}")
    assert_test(res_over.status_code == 400, f"Calculate-checkout rejects overpriced product (status {res_over.status_code})")
    assert_test("exceeds marketplace limits" in res_over.json().get("detail", ""), "Clear ceiling rejection message returned")

    res_buy_over = client.post("/api/payments/create-order", json={"product_id": str(p_exceeded.id)}, headers=headers)
    assert_test(res_buy_over.status_code == 400, f"Create-order rejects overpriced product (status {res_buy_over.status_code})")

    # Clean up test records
    db.delete(p_exceeded)
    db.delete(buyer)
    db.delete(seller)
    db.commit()
    db.close()

    print_header("Summary")
    print(f"Total Tests: {passed + failed} | Passed: {passed} | Failed: {failed}")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
