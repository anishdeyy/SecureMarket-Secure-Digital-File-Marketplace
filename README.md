======
# SecureMarket — Secure Digital Asset Marketplace

SecureMarket is a production-grade, secure digital file marketplace designed for high-integrity file distribution, strict role separation, server-authoritative payments via Razorpay, and end-to-end cryptographic verification.

---

## Key Features & Architecture

### 1. Real SHA-256 Cryptographic File Integrity
- **Raw Byte Hashing**: Every product uploaded or seeded is hashed directly from its physical storage bytes using SHA-256 (`hashlib.sha256(content).hexdigest()`).
- **No Mock Hashes**: Zero placeholder or mock hashes (`"a"*64`) exist in the system.
- **Strict Separation**: Product IDs (UUID/slug) and SHA-256 digests (64-character lowercase hex) are strictly decoupled.
- **HMAC-SHA256 Integrity Seals**: Every file is registered with a unique Integrity ID (e.g., `FI-C577A9B4`) and sealed server-side using an internal HMAC key.
- **Live Server Re-hash Audit**: The `/api/integrity/product/{id}/live-verify` endpoint recalculates the SHA-256 digest from raw storage disk bytes in real-time and verifies it against the stored fingerprint (`MATCH: File integrity verified`).
- **User Interface**: Monospace SHA-256 fingerprint display with 1-click clipboard copy and live verification audit buttons across marketplace product pages and buyer purchase receipts.

### 2. Strict Role Separation
- **BUYER**:
  - Can browse products, view details, calculate checkout fees, and purchase digital assets.
  - Accesses Buyer Library / My Purchases and authorized downloads.
  - Strictly blocked from uploading products or accessing seller dashboards (`403 Forbidden`).
- **SELLER**:
  - Can upload files, configure pricing within AI ceilings, publish/unpublish products, and monitor sales metrics.
  - Strictly blocked from purchasing marketplace products (`403 Forbidden`).
- **ADMIN**:
  - Accesses platform oversight, audits, fraud alerts, and user account management.
  - Can delete or suspend marketplace listings.
  - Strictly blocked from purchasing products (`403 Forbidden`).

### 3. Server-Authoritative Razorpay Checkout
- **Server Price Authority**: Financial calculations (subtotal, platform fees, GST tax, and total) are strictly computed on the backend from database records. Client-side price tampering is completely disregarded.
- **Integer Paise Arithmetic**: Order totals are converted to integer paise (`round(total * 100)`) preventing floating-point rounding errors.
- **HMAC-SHA256 Signature Verification**: On checkout completion, the backend validates `razorpay_signature` against `razorpay_order_id|razorpay_payment_id` using `RAZORPAY_KEY_SECRET`.
- **Pre-Payment Checkout Modal**: Shows a full transparent breakdown of subtotal, platform fee, GST tax, and total before launching the Razorpay modal.

### 4. Download Security & Entitlement Protection
- **No Direct Storage Exposure**: Storage paths on disk or S3 are never exposed to clients.
- **Paid Entitlement Verification**: File downloads require an active paid order containing the item.
- **Download Quotas**: Limits downloads per purchase (e.g., 5 downloads per license) with live usage tracking (`x/5 downloads used`).
- **Short-Lived Signed Tokens**: Generates temporary, single-use download URLs expiring in 5 minutes.

### 5. Content-Aware AI Quality & Risk Rubrics
- **Gemini 1.5 Analysis**: Automatically analyzes content structure, methodology, depth, and organization.
- **Evidence-Based Scoring Tiers**:
  - `90 - 100`: **Excellent**
  - `75 - 89`: **Good**
  - `60 - 74`: **Fair**
  - `40 - 59`: **Low**
  - `0 - 39`: **Very Low**
- Context-aware rubrics tailored to Research Papers, Technical Guides, Datasets, and Software.

---

## Demo Accounts & Credentials

| Role | Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@securemarket.com` | `Admin@1234` | System dashboard, fraud reviews, integrity audits, listing moderation |
| **Seller** | `seller1@example.com` | `Seller@1234` | Seller Studio, file uploads, product analytics, pricing adjustments |
| **Buyer** | `buyer1@example.com` | `Buyer@1234` | Marketplace purchases, checkout, library, file downloads, product reviews |

---

## Local Setup & Execution

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Windows Powershell / Command Prompt or Unix Shell

### 1. Backend (FastAPI on Port 8001)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows Powershell
# source venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Seed authentic files, real SHA-256 hashes, users, and orders
python seed.py

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

- Backend API: http://localhost:8001
- Interactive OpenAPI Docs: http://localhost:8001/docs

### 2. Frontend (Next.js on Port 3000)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

- Web Application: http://localhost:3000
- Marketplace: http://localhost:3000/marketplace
- My Purchases: http://localhost:3000/purchases

---

## Automated Verification & Test Suites

SecureMarket includes a comprehensive full-stack automated test suite verifying cryptographic hashing, role models, downloads, and Razorpay integration:

```bash
# Run the full system audit test suite
python backend/scripts/run_full_system_audit_tests.py
```

### Verified Checks:
1. Standard SHA-256 test vectors (`Hello World` -> `a591a6d4...`).
2. Avalanche effect (1-byte mutation drastically changes digest).
3. All 10 demo products exist in DB with authentic byte content and zero fake hashes.
4. All SHA-256 hashes are valid 64-character lowercase hex strings.
5. Product IDs and SHA-256 digests are strictly separate.
6. 100% of product disk files hash identically to DB records.
7. Live re-hash endpoint `/api/integrity/product/{id}/live-verify` returns `match: true`.
8. Public integrity proof lookup by Integrity ID returns valid HMAC seal.
9. Product details and marketplace listings include `sha256_hash` and load without 404s.
10. Strict Role Separation:
    - Buyer blocked from uploading product (403).
    - Seller blocked from purchasing product (403).
    - Admin blocked from purchasing product (403).
11. Download security & access control:
    - Unauthenticated downloads blocked (403).
    - Unpurchased products blocked (403).
    - Authorized buyers receive temporary signed download URLs.
    - Authorized tokens serve exact disk file bytes (HTTP 200).
12. Purchases API exposes authentic SHA-256 hashes.
13. Server-authoritative checkout and Razorpay order creation creates orders with server pricing.

---

## Technology Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide React, React Hot Toast
- **Backend**: FastAPI, Python 3.12, SQLAlchemy, Pydantic v2, Uvicorn
- **Database**: SQLite (local development) / PostgreSQL (production)
- **Payment Gateway**: Razorpay (Web2 UPI, Cards, Netbanking)
- **File Storage**: Local filesystem (dev) / AWS S3 + KMS (production)
- **AI Intelligence**: Google Gemini 1.5 Flash
- **Cryptographic Security**: SHA-256, HMAC-SHA256, PBKDF2-SHA256 (310,000 iterations), JWT (HS256)

>>>>>>> 25d803f (Add SecureMarket application)
