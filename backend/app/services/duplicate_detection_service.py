import hashlib
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session

from app.config import settings
from app.models.duplicate import ProductFileFingerprint, ProductDuplicateCheck
from app.models.product import Product
from app.prompts.quality_metadata_prompt import DUPLICATE_SEMANTIC_CHECK_PROMPT

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your"
}

def normalize_text_for_comparison(text: str) -> str:
    """Normalizes text by lowercasing, stripping punctuation, and removing excess whitespace."""
    if not text:
        return ""
    # Lowercase
    t = text.lower()
    # Strip markdown syntax and punctuation, keeping alphanumeric
    t = re.sub(r"[^\w\s]", " ", t)
    tokens = [w for w in t.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(tokens)

def compute_normalized_content_hash(text: str) -> str:
    norm = normalize_text_for_comparison(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def compute_jaccard_similarity(text1: str, text2: str) -> float:
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return float(len(intersection)) / float(len(union))

def check_semantic_duplicate_gemini(text_a: str, text_b: str, title_a: str, title_b: str) -> Tuple[bool, float, str]:
    """Uses Gemini to evaluate borderline duplicate candidates."""
    if not settings.GEMINI_API_KEY:
        return False, 0.0, "Gemini key not configured for semantic check"

    prompt = f"""{DUPLICATE_SEMANTIC_CHECK_PROMPT}

FILE A:
Title: {title_a}
Content Excerpt:
{text_a[:2000]}

---

FILE B:
Title: {title_b}
Content Excerpt:
{text_b[:2000]}
"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.6-flash")
        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=500,
                response_mime_type="application/json"
            )
        )
        raw = resp.text.strip()
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)
        data = json.loads(raw)
        is_dup = bool(data.get("is_duplicate", False))
        sim = float(data.get("similarity_score", 0.0))
        reason = str(data.get("explanation", ""))
        return is_dup, sim, reason
    except Exception as e:
        logger.warning(f"Semantic duplicate check failed: {e}")
        return False, 0.0, f"Error: {e}"

def run_duplicate_check_pipeline(
    db: Session,
    product_id: str,
    exact_sha256: str,
    extracted_text: str,
    title: str = ""
) -> Dict[str, Any]:
    """
    Multi-level duplicate content detection hierarchy:
    Level 1: Exact SHA-256 Hash
    Level 2: Normalized Content Hash
    Level 3: Token / Shingle Content Similarity (>= 0.90)
    Level 4: Gemini Semantic Check (for candidates 0.80 - 0.89)
    """
    normalized_text = normalize_text_for_comparison(extracted_text)
    norm_hash = compute_normalized_content_hash(extracted_text)
    tokens = normalized_text.split()
    token_count = len(tokens)

    # -------------------------------------------------------------
    # LEVEL 1: Exact SHA-256 Match
    # -------------------------------------------------------------
    exact_match_product = db.query(Product).filter(
        Product.sha256_hash == exact_sha256,
        Product.id != product_id
    ).first()

    if exact_match_product:
        result = {
            "status": "DUPLICATE_DETECTED",
            "matched_product_id": exact_match_product.id,
            "matched_product_title": exact_match_product.title,
            "match_level": "LEVEL_1_EXACT_SHA256",
            "similarity_score": 1.0,
            "details": {
                "reason": "Exact byte-for-byte SHA-256 hash match with an existing file in the marketplace.",
                "hash": exact_sha256
            }
        }
        _record_duplicate_check(db, product_id, result, exact_sha256, norm_hash, extracted_text, token_count)
        return result

    # -------------------------------------------------------------
    # LEVEL 2: Normalized Content Hash
    # -------------------------------------------------------------
    if len(normalized_text) > 40:
        norm_match = db.query(ProductFileFingerprint).filter(
            ProductFileFingerprint.normalized_content_hash == norm_hash,
            ProductFileFingerprint.product_id != product_id
        ).first()

        if norm_match:
            matched_prod = db.query(Product).filter(Product.id == norm_match.product_id).first()
            result = {
                "status": "DUPLICATE_DETECTED",
                "matched_product_id": norm_match.product_id,
                "matched_product_title": matched_prod.title if matched_prod else "Existing Product",
                "match_level": "LEVEL_2_NORMALIZED_HASH",
                "similarity_score": 0.98,
                "details": {
                    "reason": "Normalized text hash matches existing content after stripping minor formatting differences.",
                    "normalized_hash": norm_hash
                }
            }
            _record_duplicate_check(db, product_id, result, exact_sha256, norm_hash, extracted_text, token_count)
            return result

    # -------------------------------------------------------------
    # LEVEL 3: Token / Shingle Content Similarity
    # -------------------------------------------------------------
    if len(tokens) >= 15:
        existing_fingerprints = db.query(ProductFileFingerprint).filter(
            ProductFileFingerprint.product_id != product_id
        ).all()

        highest_sim = 0.0
        best_candidate = None

        for fp in existing_fingerprints:
            if not fp.extracted_text_snippet:
                continue
            fp_norm = normalize_text_for_comparison(fp.extracted_text_snippet)
            sim = compute_jaccard_similarity(normalized_text, fp_norm)
            if sim > highest_sim:
                highest_sim = sim
                best_candidate = fp

        if highest_sim >= 0.90 and best_candidate:
            matched_prod = db.query(Product).filter(Product.id == best_candidate.product_id).first()
            result = {
                "status": "DUPLICATE_DETECTED",
                "matched_product_id": best_candidate.product_id,
                "matched_product_title": matched_prod.title if matched_prod else "Existing Product",
                "match_level": "LEVEL_3_TOKEN_SIMILARITY",
                "similarity_score": round(highest_sim, 3),
                "details": {
                    "reason": f"Content similarity score is {highest_sim:.1%}, exceeding the 90% threshold for original content.",
                    "token_overlap": round(highest_sim, 3)
                }
            }
            _record_duplicate_check(db, product_id, result, exact_sha256, norm_hash, extracted_text, token_count)
            return result

        # -------------------------------------------------------------
        # LEVEL 4: Gemini Semantic Check (for candidates 0.80 - 0.89)
        # -------------------------------------------------------------
        if highest_sim >= 0.80 and best_candidate:
            matched_prod = db.query(Product).filter(Product.id == best_candidate.product_id).first()
            matched_title = matched_prod.title if matched_prod else ""
            is_dup, sem_sim, reason = check_semantic_duplicate_gemini(
                extracted_text, best_candidate.extracted_text_snippet, title, matched_title
            )
            if is_dup and sem_sim >= 0.85:
                result = {
                    "status": "DUPLICATE_DETECTED",
                    "matched_product_id": best_candidate.product_id,
                    "matched_product_title": matched_title,
                    "match_level": "LEVEL_4_SEMANTIC_MATCH",
                    "similarity_score": round(sem_sim, 3),
                    "details": {
                        "reason": f"AI Semantic Analysis determined file is substantially identical: {reason}",
                        "semantic_similarity": round(sem_sim, 3)
                    }
                }
                _record_duplicate_check(db, product_id, result, exact_sha256, norm_hash, extracted_text, token_count)
                return result

    # All checks passed: File is unique
    clear_result = {
        "status": "CLEAR",
        "matched_product_id": None,
        "matched_product_title": None,
        "match_level": None,
        "similarity_score": 0.0,
        "details": {
            "reason": "File verified as unique across all detection levels."
        }
    }
    _record_duplicate_check(db, product_id, clear_result, exact_sha256, norm_hash, extracted_text, token_count)
    return clear_result

def _record_duplicate_check(
    db: Session,
    product_id: str,
    result: Dict[str, Any],
    exact_sha256: str,
    norm_hash: str,
    extracted_text: str,
    token_count: int
):
    """Saves or updates fingerprint and duplicate check records and updates product status."""
    # Update or insert fingerprint
    fp = db.query(ProductFileFingerprint).filter(ProductFileFingerprint.product_id == product_id).first()
    if not fp:
        fp = ProductFileFingerprint(
            product_id=product_id,
            exact_sha256=exact_sha256,
            normalized_content_hash=norm_hash,
            extracted_text_snippet=extracted_text[:10000],
            token_count=token_count
        )
        db.add(fp)
    else:
        fp.exact_sha256 = exact_sha256
        fp.normalized_content_hash = norm_hash
        fp.extracted_text_snippet = extracted_text[:10000]
        fp.token_count = token_count

    # Add duplicate check history
    chk = ProductDuplicateCheck(
        product_id=product_id,
        status=result["status"],
        matched_product_id=result.get("matched_product_id"),
        match_level=result.get("match_level"),
        similarity_score=result.get("similarity_score", 0.0),
        details=json.dumps(result.get("details", {}))
    )
    db.add(chk)

    # Update product status
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.duplicate_status = result["status"]
        if result["status"] == "DUPLICATE_DETECTED" and product.status == "published":
            product.status = "rejected"

    db.commit()
