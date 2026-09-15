# SHA-256 File Integrity System

## Overview

Every file uploaded to SecureMarket gets a **unique Integrity ID** (format: `FI-XXXXXXXX`).

## How it works

1. **SHA-256 hash** is computed from raw file bytes at upload time
2. A **unique Integrity ID** (e.g. `FI-A3B4C5D6`) is generated
3. An **HMAC-SHA256 seal** is computed over `integrity_id:sha256_hash` using the app secret
4. The record is stored in `file_integrity_records` with all three values
5. The `integrity_id` is also stored in `products.integrity_id` (cross-check)

## Tamper Detection

| Check | What it detects |
|-------|----------------|
| HMAC seal | DB record was altered after creation |
| Cross-check | `products.integrity_id` was changed to point elsewhere |
| File re-hash | The stored file differs from the original |

## API Endpoints

```
GET  /api/integrity/{integrity_id}           — public proof lookup
GET  /api/integrity/product/{product_id}    — by product (auth required)
GET  /api/integrity/admin/all               — admin: list all records
POST /api/integrity/admin/{id}/verify       — admin: re-run full check
GET  /api/integrity/admin/tampered          — admin: flagged records
```

## Viewing in the Backend

```bash
# SQLite (local dev)
sqlite3 backend/securemarket.db \
  "SELECT integrity_id, sha256_hash, original_filename, is_verified FROM file_integrity_records"

# API (admin)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/integrity/admin/all | python3 -m json.tool
```

## Frontend

- Product detail page shows the Integrity ID with a link to the proof page
- Purchases page shows SHA-256 hash and links to `/integrity/{id}`
- Admin dashboard has a full **Integrity Records** tab with live verify button
