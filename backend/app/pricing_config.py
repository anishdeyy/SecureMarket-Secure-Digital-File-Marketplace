"""
Dynamic Pricing Configuration for SecureMarket
Configurable category limits, content-type profiles, value scoring weights, and global safety caps.
"""

from typing import Any

# ── Global Platform Constraints ──────────────────────────────────────────────
GLOBAL_MIN_PRICE_INR: float = 10.0
GLOBAL_PLATFORM_MAX_PRICE_INR: float = 100000.0  # Absolute emergency platform cap
GLOBAL_MAX_PRICE_INR: float = GLOBAL_PLATFORM_MAX_PRICE_INR

# ── Configurable Category Ceilings (in INR) ──────────────────────────────────
CATEGORY_CEILINGS_INR: dict[str, float] = {
    "Programming": 25000.0,
    "Code": 25000.0,
    "Software": 25000.0,
    "Design": 20000.0,
    "Graphics": 20000.0,
    "UI Kit": 20000.0,
    "Education": 20000.0,
    "Academic": 20000.0,
    "Business": 20000.0,
    "Marketing": 15000.0,
    "Finance": 20000.0,
    "Documents": 10000.0,
    "Document": 10000.0,
    "Templates": 15000.0,
    "Template": 15000.0,
    "Other": 5000.0,
}

DEFAULT_CATEGORY_CEILING_INR: float = 10000.0

# ── Content-Type Ceiling Multipliers / Caps ──────────────────────────────────
# Max proportion of category ceiling achievable for this content type
CONTENT_TYPE_PROFILES: dict[str, dict[str, Any]] = {
    "Simple TXT": {
        "max_ceiling_inr": 100.0,
        "suggested_default_inr": 25.0,
        "type_multiplier": 0.05,
    },
    "Research Paper": {
        "max_ceiling_inr": 8000.0,
        "suggested_default_inr": 999.0,
        "type_multiplier": 0.50,
    },
    "Academic Paper": {
        "max_ceiling_inr": 8000.0,
        "suggested_default_inr": 999.0,
        "type_multiplier": 0.50,
    },
    "Educational Course": {
        "max_ceiling_inr": 25000.0,
        "suggested_default_inr": 2499.0,
        "type_multiplier": 0.85,
    },
    "Ebook": {
        "max_ceiling_inr": 15000.0,
        "suggested_default_inr": 1499.0,
        "type_multiplier": 0.65,
    },
    "Source Code": {
        "max_ceiling_inr": 25000.0,
        "suggested_default_inr": 3499.0,
        "type_multiplier": 0.90,
    },
    "Design Template": {
        "max_ceiling_inr": 15000.0,
        "suggested_default_inr": 1299.0,
        "type_multiplier": 0.60,
    },
    "Asset Bundle": {
        "max_ceiling_inr": 25000.0,
        "suggested_default_inr": 2999.0,
        "type_multiplier": 0.80,
    },
    "Spreadsheet": {
        "max_ceiling_inr": 15000.0,
        "suggested_default_inr": 999.0,
        "type_multiplier": 0.55,
    },
    "Presentation": {
        "max_ceiling_inr": 8000.0,
        "suggested_default_inr": 499.0,
        "type_multiplier": 0.40,
    },
    "Report": {
        "max_ceiling_inr": 10000.0,
        "suggested_default_inr": 799.0,
        "type_multiplier": 0.45,
    },
    "Document": {
        "max_ceiling_inr": 10000.0,
        "suggested_default_inr": 499.0,
        "type_multiplier": 0.40,
    },
    "Other": {
        "max_ceiling_inr": 5000.0,
        "suggested_default_inr": 299.0,
        "type_multiplier": 0.30,
    },
}

# ── Value Score Weights (Total = 100%) ───────────────────────────────────────
PRODUCT_VALUE_SCORE_WEIGHTS = {
    "content_depth": 0.25,
    "quality_score": 0.20,
    "completeness": 0.15,
    "structure": 0.10,
    "usability": 0.10,
    "complexity": 0.10,
    "practical_value": 0.10,
}

PRICING_RULE_VERSION = "PRICING_V3"
