import json
import logging
import os
import re
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.prompts.quality_metadata_prompt import QUALITY_ANALYSIS_SYSTEM_PROMPT
from app.models.quality import ProductQualityAnalysis
from app.models.product import Product

logger = logging.getLogger(__name__)

PLACEHOLDER_PATTERNS = [
    r"\blorem\s+ipsum\b",
    r"\basdf\b",
    r"\btest\s+test\b",
    r"\bsample\s+text\b",
    r"\bfoo\s+bar\b",
    r"\bqwerty\b",
    r"\bplaceholder\b"
]

def _check_placeholders(text: str) -> bool:
    lower_text = text.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, lower_text):
            return True
    return False

def clean_audience_description(text: str, filename: str = "", title: str = "") -> str:
    """Ensure target audience / recommended application is clean, human-readable, and never includes raw filenames."""
    raw = (text or "").strip()
    
    # Check if raw text is the old template string with a filename
    match = re.search(r"Buyers looking for structured resources related to\s+([^\.]+)(?:\.[a-zA-Z0-9]+)?", raw, re.IGNORECASE)
    if match:
        raw_topic = match.group(1).replace("_", " ").replace("-", " ").strip()
        return f"Researchers, students, and professionals interested in {raw_topic.lower()}."
        
    # Strip any file extensions from raw text
    cleaned = re.sub(r"\b[\w\-]+\.(?:pdf|txt|docx|doc|pptx|xlsx|zip|py|js|ts|csv)\b", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("_", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) < 20 or cleaned.endswith("for") or "Buyers looking for" in cleaned:
        subject = title or filename
        subject = re.sub(r"\.[a-zA-Z0-9]+$", "", subject)
        subject = re.sub(r"[_\-\.]+", " ", subject).strip()
        return f"Researchers, students, and professionals interested in {subject.lower()}."
    return cleaned

def detect_content_type(text: str, filename: str, mime_type: str) -> str:
    """Classify the uploaded file into an appropriate content type."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    lower_text = (text or "").lower()[:10000]
    
    # 1. Code
    if ext in {"py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "cs", "go", "rs", "php", "rb", "sql", "html", "css"}:
        return "Source Code"
    if "import " in lower_text and ("def " in lower_text or "function " in lower_text or "class " in lower_text):
        return "Source Code"
        
    # 2. Spreadsheet
    if ext in {"xlsx", "xls", "csv"}:
        return "Spreadsheet"
        
    # 3. Presentation
    if ext in {"pptx", "ppt", "key"}:
        return "Presentation"
    if "slide " in lower_text or "agenda" in lower_text and "presentation" in lower_text:
        return "Presentation"

    # 4. Research / Academic Paper
    academic_keywords = [
        "abstract", "introduction", "methodology", "related work", "references", 
        "ieee", "acm", "arxiv", "doi:", "experimental evaluation", "in this paper",
        "academic paper", "research paper", "this paper presents", "the authors"
    ]
    academic_hits = sum(1 for kw in academic_keywords if kw in lower_text)
    if ("academic paper" in lower_text or "research paper" in lower_text or 
        academic_hits >= 2 or ("abstract" in lower_text and "references" in lower_text)):
        return "Research Paper"
        
    # 5. Templates
    template_keywords = ["resume", "curriculum vitae", "invoice", "receipt", "proposal template", "contract template"]
    if any(kw in lower_text for kw in template_keywords) or "template" in filename.lower():
        return "Template"
        
    # 6. Course Material
    course_keywords = ["course syllabus", "lecture", "module 1", "module 2", "assignment", "homework", "exam review"]
    if any(kw in lower_text for kw in course_keywords):
        return "Course Material"

    # 7. Datasets
    if ext in {"json", "parquet", "tsv"} or "dataset" in filename.lower():
        return "Dataset"

    # 8. Books / Reports
    if len(lower_text.split()) > 4000 or "table of contents" in lower_text:
        return "Book"
    if "executive summary" in lower_text or "report" in filename.lower():
        return "Report"

    return "Document"

def _heuristic_quality_assessment(text: str, filename: str, mime_type: str) -> Dict[str, Any]:
    """Fallback deterministic, content-type aware quality estimation."""
    clean_text = text.strip()
    char_len = len(clean_text)
    words = clean_text.split()
    word_count = len(words)
    c_type = detect_content_type(clean_text, filename, mime_type)

    # Sparse check (< 50 characters)
    if char_len < 50:
        return {
            "content_type": c_type,
            "content_quality": 20,
            "completeness": 15,
            "structure_organization": 25,
            "methodology_depth": 20,
            "evidence_results": 15,
            "usability_clarity": 20,
            "key_strengths": ["Clean file upload format"],
            "limitations": ["File has extremely sparse or empty readable content (< 50 characters)"],
            "target_use_case": "Requires substantive content revision by seller before commercial distribution.",
            "confidence_score": 0.95,
            "reasoning": "Deterministic check: File lacks substantive readable text or structure."
        }

    has_placeholders = _check_placeholders(clean_text)
    
    # Base scores conditioned on detected content type
    if c_type in {"Research Paper", "Academic Paper"}:
        # Structured research paper scoring
        is_theoretical = ("theoretical" in clean_text.lower() or "proof" in clean_text.lower() or 
                          not any(kw in clean_text.lower() for kw in ["dataset", "experiment", "benchmark", "accuracy", "simulation"]))
        
        if word_count >= 800:
            content_q = 82
            completeness = 80
            structure = 85
            methodology = 78
            evidence = 72 if is_theoretical else 80
            usability = 76
            strengths = [
                "Clear architectural problem formulation and motivation",
                "Structured academic framework with clear conceptual models",
                "Rigorous domain terminology and technical consistency"
            ]
            if is_theoretical:
                limitations = ["This paper appears primarily theoretical; experimental evaluation is limited."]
            else:
                limitations = ["Requires prior domain expertise in the subject area for implementation."]
        else:
            content_q = 74
            completeness = 70
            structure = 75
            methodology = 72
            evidence = 65
            usability = 70
            strengths = ["Structured introductory overview", "Clear statement of objectives"]
            limitations = ["Brief academic paper; full empirical results would enhance completeness."]
    elif c_type == "Source Code":
        content_q = 85
        completeness = 80
        structure = 85
        methodology = 85
        evidence = 75
        usability = 85
        strengths = ["Production-ready code syntax", "Modular function definitions"]
        limitations = ["Requires standard development environment and dependencies"]
    elif word_count > 1000:
        content_q = 85
        completeness = 85
        structure = 85
        methodology = 80
        evidence = 80
        usability = 82
        strengths = ["Comprehensive coverage with extensive detail", "Organized layout with distinct topic sections"]
        limitations = ["Broad scope; specific solutions may require focused reading"]
    elif word_count > 300:
        content_q = 78
        completeness = 76
        structure = 78
        methodology = 75
        evidence = 72
        usability = 76
        strengths = ["Clear and targeted structure", "Usable reference material"]
        limitations = ["Covers core topics; advanced edge cases may require supplementary reading"]
    else:
        content_q = 60
        completeness = 55
        structure = 65
        methodology = 55
        evidence = 50
        usability = 60
        strengths = ["Concise format", "Quick reference layout"]
        limitations = ["Brief document; could benefit from more detailed explanations"]

    if has_placeholders:
        content_q = max(20, content_q - 35)
        completeness = max(20, completeness - 35)
        limitations.append("Detected placeholder or boilerplate test text in content")

    clean_use_case = clean_audience_description("", filename=filename, title=filename)

    return {
        "content_type": c_type,
        "content_quality": content_q,
        "completeness": completeness,
        "structure_organization": structure,
        "methodology_depth": methodology,
        "evidence_results": evidence,
        "usability_clarity": usability,
        "key_strengths": strengths,
        "limitations": limitations,
        "target_use_case": clean_use_case,
        "confidence_score": 0.88,
        "reasoning": f"Analysis based on {word_count} words and detected {c_type.lower()} structure."
    }

def analyze_file_quality_with_gemini(text: str, filename: str, mime_type: str, file_size: int) -> Dict[str, Any]:
    """Analyze file quality using Gemini AI with fallback to heuristic evaluation."""
    clean_text = text.strip()
    
    # Deterministic sparse check before calling any AI
    if len(clean_text) < 50:
        return _heuristic_quality_assessment(clean_text, filename, mime_type)

    if not settings.GEMINI_API_KEY:
        return _heuristic_quality_assessment(clean_text, filename, mime_type)

    prompt = f"""{QUALITY_ANALYSIS_SYSTEM_PROMPT}

FILE TO ANALYZE:
Filename: {filename}
MIME Type: {mime_type}
File Size: {file_size} bytes
Content Excerpt (first {min(len(clean_text), 5000)} characters):
\"\"\"
{clean_text[:5000]}
\"\"\"
"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        raw = response.text.strip()
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)
        data = json.loads(raw)
        
        c_type = data.get("content_type") or detect_content_type(clean_text, filename, mime_type)
        raw_target = str(data.get("target_use_case", ""))
        cleaned_target = clean_audience_description(raw_target, filename=filename, title=filename)

        return {
            "content_type": c_type,
            "content_quality": int(max(0, min(100, data.get("content_quality", data.get("content_usefulness", 78))))),
            "completeness": int(max(0, min(100, data.get("completeness", 78)))),
            "structure_organization": int(max(0, min(100, data.get("structure_organization", 78)))),
            "methodology_depth": int(max(0, min(100, data.get("methodology_depth", data.get("technical_depth", 75))))),
            "evidence_results": int(max(0, min(100, data.get("evidence_results", 72)))),
            "usability_clarity": int(max(0, min(100, data.get("usability_clarity", data.get("practical_value", 75))))),
            "key_strengths": list(data.get("key_strengths", []))[:5],
            "limitations": list(data.get("limitations", []))[:5],
            "target_use_case": cleaned_target[:500],
            "confidence_score": float(max(0.0, min(1.0, data.get("confidence_score", 0.88)))),
            "reasoning": str(data.get("reasoning", ""))[:1000]
        }
    except Exception as e:
        logger.warning(f"Gemini quality evaluation failed ({e}); falling back to heuristic engine")
        return _heuristic_quality_assessment(clean_text, filename, mime_type)

def calculate_weighted_quality_score(metrics: Dict[str, Any]) -> int:
    """
    Authoritative quality score formula:
    Content quality: 20%
    Completeness: 20%
    Structure: 15%
    Methodology / technical depth: 20%
    Evidence / results: 15%
    Usability / clarity: 10%
    Total: 100%
    """
    cq = metrics.get("content_quality", metrics.get("content_usefulness", 75))
    comp = metrics.get("completeness", 75)
    struct = metrics.get("structure_organization", 75)
    meth = metrics.get("methodology_depth", metrics.get("technical_depth", 75))
    evid = metrics.get("evidence_results", 70)
    usab = metrics.get("usability_clarity", metrics.get("practical_value", 75))

    score = round(
        0.20 * cq +
        0.20 * comp +
        0.15 * struct +
        0.20 * meth +
        0.15 * evid +
        0.10 * usab
    )
    return max(0, min(100, score))

def determine_quality_level(score: int) -> str:
    """
    Quality Tiers:
    90-100 = Excellent
    75-89 = Good
    60-74 = Fair
    40-59 = Low
    0-39 = Very Low
    """
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Low"
    else:
        return "Very Low"

def compute_listing_risk(
    price: float,
    quality_score: int,
    suggested_price: Optional[float] = None,
    maximum_allowed_price: Optional[float] = None,
    content_type: str = "Document",
    is_unique: bool = True,
    malware_clean: bool = True,
    word_count: int = 500
) -> Dict[str, Any]:
    """
    Listing risk must be completely separate from quality score.
    Thresholds:
      0-24: LOW
      25-49: MEDIUM
      50-74: HIGH
      75-100: CRITICAL
      
    Considers:
      - price-to-suggested-price ratio
      - quality score
      - sparse content
      - malware scan result
      - price ceiling boundaries
      
    Rules:
      - Do NOT treat academic content, technical terminology, large file sizes, PDF formats, or complex topics as fraud indicators.
      - A ₹3,000 research paper with quality 79 should receive LOW or MEDIUM risk with explainable reasons (e.g. "Price is above the recommended range"), NOT HIGH RISK.
    """
    reasons = []
    positive_checks = []

    # 1. Base Security Checks
    if malware_clean:
        positive_checks.append("Malware scan passed")
    else:
        reasons.append("Malware scan failure detected")
        return {
            "risk_score": 95,
            "risk_level": "critical",
            "risk_reasons": reasons,
            "positive_checks": positive_checks
        }

    if is_unique:
        positive_checks.append("Unique file verified (no duplicate content detected)")
    else:
        reasons.append("Near-duplicate or copied content detected")

    if word_count >= 100:
        positive_checks.append("Content appears complete and substantive")

    # 2. Price Risk Analysis
    p = float(price or 0.0)
    sug = float(suggested_price or 49.0)
    max_p = float(maximum_allowed_price or 10000.0)

    risk_score = 10  # Baseline low risk for clean uploads

    # Content sparse penalty
    if word_count < 20:
        risk_score += 40
        reasons.append("File contains extremely brief or sparse text")

    # Low quality with high price penalty
    if quality_score < 40 and p > 1000:
        risk_score += 55
        reasons.append(f"Price (₹{p:,.0f}) is excessively high for a low quality score ({quality_score}/100)")
    elif quality_score < 40:
        risk_score += 20
        reasons.append("Content density or structure scored below standard marketplace thresholds")

    # Price ceiling checks
    if p > max_p:
        risk_score += 50
        reasons.append(f"Price (₹{p:,.0f}) exceeds the maximum allowed limit of ₹{max_p:,.0f} for this product")
    elif sug > 0 and p > sug * 2.5:
        # Above recommended range but within allowed ceiling -> Medium Review
        risk_score += 25
        reasons.append("Price is above the recommended range")
    elif sug > 0 and p > sug * 1.5:
        risk_score += 10
        reasons.append("Price is moderately higher than the algorithmic suggestion")

    # Normalize risk score 0 to 100
    risk_score = max(5, min(100, risk_score))

    # Map to 4 strict tiers
    if risk_score >= 75:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_reasons": reasons,
        "positive_checks": positive_checks
    }

def evaluate_and_save_product_quality(
    db: Session,
    product: Product,
    extracted_text: str,
    commit: bool = True
) -> ProductQualityAnalysis:
    """Evaluates product file quality, detects content type, and persists analysis record."""
    filename = product.original_filename or f"file.{product.file_extension or 'txt'}"
    mime = product.mime_type or "application/octet-stream"
    file_size = product.file_size_bytes or len(extracted_text)

    analysis_data = analyze_file_quality_with_gemini(extracted_text, filename, mime, file_size)
    overall_score = calculate_weighted_quality_score(analysis_data)
    quality_level = determine_quality_level(overall_score)
    
    word_count = len(extracted_text.split())
    risk_info = compute_listing_risk(
        price=product.price or 0.0,
        quality_score=overall_score,
        suggested_price=product.suggested_price,
        maximum_allowed_price=product.maximum_allowed_price,
        content_type=analysis_data.get("content_type", "Document"),
        is_unique=(product.duplicate_status != "DUPLICATE_DETECTED"),
        malware_clean=(product.scan_status == "clean"),
        word_count=word_count
    )

    existing = db.query(ProductQualityAnalysis).filter(
        ProductQualityAnalysis.product_id == product.id
    ).first()

    if not existing:
        existing = ProductQualityAnalysis(product_id=product.id)
        db.add(existing)

    existing.overall_score = overall_score
    existing.quality_level = quality_level
    existing.detected_content_type = analysis_data.get("content_type", "Document")
    existing.content_usefulness = analysis_data["content_quality"]
    existing.completeness = analysis_data["completeness"]
    existing.structure_organization = analysis_data["structure_organization"]
    existing.practical_value = analysis_data["usability_clarity"]
    existing.technical_depth = analysis_data["methodology_depth"]
    existing.methodology_depth = analysis_data["methodology_depth"]
    existing.evidence_results = analysis_data["evidence_results"]
    existing.confidence_score = analysis_data["confidence_score"]
    existing.key_strengths = json.dumps(analysis_data["key_strengths"])
    existing.limitations = json.dumps(analysis_data["limitations"])
    existing.target_use_case = analysis_data["target_use_case"]
    existing.reasoning = analysis_data["reasoning"]
    existing.risk_score = risk_info["risk_score"]
    existing.risk_level = risk_info["risk_level"]
    existing.risk_factors = json.dumps(risk_info["risk_reasons"])
    existing.risk_reasons = json.dumps(risk_info["risk_reasons"])
    existing.positive_checks = json.dumps(risk_info["positive_checks"])
    existing.evaluated_at = datetime.utcnow()
    existing.updated_at = datetime.utcnow()

    if commit:
        db.commit()
        db.refresh(existing)

    return existing
