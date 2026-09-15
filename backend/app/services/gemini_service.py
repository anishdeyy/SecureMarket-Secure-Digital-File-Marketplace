import json
import logging
import re
import time
from typing import Optional, Dict, Any
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "Programming", "Design", "Education", "Business", "Marketing",
    "Finance", "Documents", "Templates", "Photography", "Graphics",
    "Data", "Ebooks", "Other"
]
VALID_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced", "Not Applicable", "Unknown"]

# The official SecureMarket Gemini prompt
SECUREMARKET_GEMINI_PROMPT = """You are the metadata generation engine for SecureMarket, a secure Web2 digital file marketplace.

Your task is to analyze the uploaded digital file and generate accurate, useful marketplace metadata.

IMPORTANT RULES:

1. Only use information that is actually present in the uploaded file or reliably inferable from it.
2. NEVER invent facts, features, authors, companies, dates, page counts, technologies, or claims.
3. If information cannot be determined, return null or "Unknown".
4. The metadata must be suitable for displaying to both the seller and buyer.
5. Keep descriptions professional, concise, and easy to understand.
6. Do not include marketing hype or unsupported claims.
7. Do not generate prices.
8. Do not generate security information.
9. Do not generate SHA-256 hashes.
10. Do not determine malware status.
11. Do not modify technical file properties supplied by the backend.
12. Return ONLY valid JSON. Do not include markdown, explanations, or code fences.

Generate the following fields:

{
  "title": "A clear and concise product title",
  "short_description": "A concise marketplace description in 1-2 sentences",
  "summary": "A useful summary of the file's content",
  "category": "Best matching marketplace category",
  "subcategory": "Best matching subcategory",
  "tags": ["3-10 relevant tags"],
  "keywords": ["5-15 useful search keywords"],
  "language": "Detected language",
  "difficulty": "Beginner | Intermediate | Advanced | Not Applicable | Unknown",
  "content_type": "Type of digital content",
  "target_audience": "Who would benefit most from this file",
  "key_topics": ["Main topics covered in the file"]
}

CATEGORY OPTIONS:
- Programming
- Design
- Education
- Business
- Marketing
- Finance
- Documents
- Templates
- Photography
- Graphics
- Data
- Ebooks
- Other

DIFFICULTY RULES:
Use: Beginner, Intermediate, Advanced, Not Applicable, Unknown
Only assign a difficulty level when the file content supports that classification.

TAG RULES:
- Generate 3-10 tags.
- Tags must be directly relevant to the content.
- Avoid duplicate tags.
- Prefer specific terms over generic terms.

KEYWORD RULES:
- Generate 5-15 search-friendly keywords.
- Include important concepts, technologies, subjects, or topics actually present.
- Do not add unrelated popular keywords just to improve search ranking.

TITLE RULES:
- Maximum 80 characters.
- Clear and professional.
- Do not use excessive capitalization.
- Do not add words such as "BEST", "PREMIUM", "ULTIMATE", or "100%".
- Do not invent a brand or author.

DESCRIPTION RULES:
- 1-2 sentences.
- Explain what the file contains and what it is useful for.
- Do not make unsupported claims.

SUMMARY RULES:
- Summarize the actual content.
- Do not advertise the product.
- Do not mention information that is not present in the file.

TARGET AUDIENCE:
Identify the likely intended audience based only on the content.

CONTENT TYPE examples:
- PDF Guide, Ebook, Course Material, Resume Template, Design Template,
  Source Code, Spreadsheet, Presentation, Dataset, Image Pack, Document, ZIP Package, Other

If the file cannot be analyzed sufficiently, still return valid JSON and use "Unknown" where necessary.
"""


def build_analysis_prompt(filename: str, mime_type: str, file_size: int, content_sample: str) -> str:
    """Build the final AI prompt safely without str.format() brace collision."""
    return (
        f"{SECUREMARKET_GEMINI_PROMPT}\n\n"
        f"FILE INFORMATION:\n"
        f"Filename: {filename}\n"
        f"MIME Type: {mime_type}\n"
        f"File Size: {file_size} bytes\n\n"
        f"FILE CONTENT SAMPLE:\n"
        f"---\n"
        f"{content_sample}\n"
        f"---\n"
    )


def extract_text_from_file(file_content: bytes, filename: str, mime_type: str) -> str:
    """Extract readable text from uploaded file for AI analysis."""
    ext = Path(filename).suffix.lower()
    max_chars = 7000

    try:
        if ext == ".pdf":
            return _extract_pdf_text(file_content, max_chars)
        elif ext in [".docx", ".doc"]:
            return _extract_docx_text(file_content, max_chars)
        elif ext in [".txt", ".md", ".csv"]:
            return _extract_plain_text(file_content, max_chars)
        elif ext in [".py", ".js", ".ts", ".html", ".css", ".java", ".go", ".rs", ".cpp", ".c"]:
            return _extract_code_text(file_content, max_chars)
        elif ext == ".json":
            return _extract_json_sample(file_content, max_chars)
        elif ext in [".xlsx", ".xls"]:
            return "[Spreadsheet file — cannot extract text preview]"
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]:
            return "[Image file — visual content, no text extraction]"
        elif ext in [".zip", ".rar", ".7z"]:
            return "[Archive file — compressed content]"
        elif ext in [".mp3", ".mp4", ".mov", ".avi"]:
            return "[Media file — audio/video content]"
        else:
            return f"[Binary file: {filename}, type: {mime_type}]"
    except Exception as e:
        logger.warning(f"Text extraction failed for {filename}: {e}")
        return f"[Extraction failed for: {filename}]"


def _extract_pdf_text(content: bytes, max_chars: int) -> str:
    try:
        import io
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for i, page in enumerate(reader.pages[:12]):
            text += page.extract_text() or ""
            if len(text) >= max_chars:
                break
        return text[:max_chars] if text.strip() else "[PDF: no extractable text]"
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def _extract_docx_text(content: bytes, max_chars: int) -> str:
    try:
        import io
        from docx import Document
        doc = Document(io.BytesIO(content))
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text[:max_chars]
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"


def _extract_plain_text(content: bytes, max_chars: int) -> str:
    try:
        text = content.decode("utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return "[Text extraction failed]"


def _extract_code_text(content: bytes, max_chars: int) -> str:
    try:
        text = content.decode("utf-8", errors="replace")
        return f"[Source Code]\n{text[:max_chars]}"
    except Exception:
        return "[Code extraction failed]"


def _extract_json_sample(content: bytes, max_chars: int) -> str:
    try:
        text = content.decode("utf-8", errors="replace")
        return f"[JSON Data]\n{text[:max_chars]}"
    except Exception:
        return "[JSON extraction failed]"


def generate_metadata_ollama(file_content: bytes, filename: str, mime_type: str) -> Optional[Dict[str, Any]]:
    """Generate AI metadata using local Ollama model with guaranteed JSON output."""
    try:
        extracted_text = extract_text_from_file(file_content, filename, mime_type)
        file_size = len(file_content)

        prompt = build_analysis_prompt(filename, mime_type, file_size, extracted_text[:4000])

        ollama_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2
            }
        }
        logger.info(f"Querying local Ollama ({settings.OLLAMA_MODEL}) for metadata: {filename}")
        import requests
        resp = requests.post(ollama_url, json=payload, timeout=75)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data.get("response", "").strip()
            raw_text = re.sub(r"```json\s*", "", raw_text)
            raw_text = re.sub(r"```\s*", "", raw_text)
            raw_text = raw_text.strip()
            metadata = json.loads(raw_text)
            validated = _validate_and_sanitize(metadata)
            validated["_ai_provider"] = "ollama"
            logger.info(f"Ollama ({settings.OLLAMA_MODEL}) metadata generated successfully for: {filename}")
            return validated
        else:
            logger.warning(f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        logger.warning(f"Ollama generation failed: {e}")
        return None


def generate_metadata_gemini(file_content: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
    """Generate AI metadata using Gemini with automatic fallback to Ollama."""
    if settings.AI_MODE == "mock":
        logger.info("AI_MODE=mock — returning mock metadata")
        return _mock_metadata(filename)

    if settings.AI_MODE == "ollama":
        logger.info("AI_MODE=ollama — calling Ollama directly")
        ollama_res = generate_metadata_ollama(file_content, filename, mime_type)
        if ollama_res:
            return ollama_res
        return _mock_metadata(filename)

    # If Gemini API key is provided, try Gemini first
    if settings.GEMINI_API_KEY:
        extracted_text = extract_text_from_file(file_content, filename, mime_type)
        file_size = len(file_content)

        prompt = build_analysis_prompt(filename, mime_type, file_size, extracted_text[:6000])

        max_retries = 2
        for attempt in range(max_retries):
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # Try preferred model, then alternatives
                model_name = "gemini-3.6-flash" if attempt == 0 else "gemini-flash-latest"
                model = genai.GenerativeModel(model_name)

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=3000,
                        response_mime_type="application/json"
                    )
                )

                raw_text = response.text.strip()
                raw_text = re.sub(r"```json\s*", "", raw_text)
                raw_text = re.sub(r"```\s*", "", raw_text)
                raw_text = raw_text.strip()

                # Extract JSON block if surrounded by other characters
                json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
                target_json = json_match.group(1) if json_match else raw_text
                metadata = json.loads(target_json)
                validated = _validate_and_sanitize(metadata)
                validated["_ai_provider"] = "gemini"
                logger.info(f"Gemini metadata generated successfully for: {filename}")
                return validated

            except json.JSONDecodeError as e:
                logger.warning(f"Gemini JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)

        logger.info("Gemini was unavailable or encountered an error. Falling back to local Ollama...")

    # Fallback to Ollama if Gemini failed or no Gemini API key
    ollama_res = generate_metadata_ollama(file_content, filename, mime_type)
    if ollama_res:
        return ollama_res

    logger.warning("Both Gemini and Ollama unavailable, using fallback mock metadata")
    return _mock_metadata(filename)


def _validate_and_sanitize(metadata: dict) -> dict:
    """Validate Gemini output — strip any invented security/payment data."""
    result = {}
    result["title"] = str(metadata.get("title") or "Digital Product")[:80]
    result["short_description"] = str(metadata.get("short_description") or "")[:250]
    result["summary"] = str(metadata.get("summary") or "")[:1500]

    cat = metadata.get("category", "Other")
    result["category"] = cat if cat in VALID_CATEGORIES else "Other"
    result["subcategory"] = str(metadata.get("subcategory") or "")[:60]

    tags = metadata.get("tags") or []
    result["tags"] = [str(t).lower()[:50] for t in tags[:10] if isinstance(t, str) and t.strip()]

    kw = metadata.get("keywords") or []
    result["keywords"] = [str(k).lower()[:60] for k in kw[:15] if isinstance(k, str) and k.strip()]

    result["language"] = str(metadata.get("language") or "English")[:60]

    diff = metadata.get("difficulty", "Unknown")
    result["difficulty"] = diff if diff in VALID_DIFFICULTIES else "Unknown"

    result["content_type"] = str(metadata.get("content_type") or "Document")[:80]
    result["target_audience"] = str(metadata.get("target_audience") or "")[:200]

    kt = metadata.get("key_topics") or []
    result["key_topics"] = [str(t)[:80] for t in kt[:10] if isinstance(t, str) and t.strip()]

    if "_ai_provider" in metadata:
        result["_ai_provider"] = metadata["_ai_provider"]

    return result


def _mock_metadata(filename: str) -> Dict[str, Any]:
    """Fallback mock metadata for development / API failure."""
    name = Path(filename).stem.replace("-", " ").replace("_", " ").title()
    ext = Path(filename).suffix.lower().lstrip(".")
    content_type_map = {
        "pdf": "PDF Guide", "docx": "Document", "doc": "Document",
        "xlsx": "Spreadsheet", "xls": "Spreadsheet", "pptx": "Presentation",
        "zip": "ZIP Package", "py": "Source Code", "js": "Source Code",
        "ts": "Source Code", "png": "Image", "jpg": "Image",
        "mp4": "Video", "mp3": "Audio", "epub": "Ebook",
    }
    return {
        "title": name[:80],
        "short_description": f"A digital {content_type_map.get(ext, 'file')}: {name}. Please update this description.",
        "summary": f"This product contains {name}. Please add a detailed description for buyers.",
        "category": "Documents",
        "subcategory": "General",
        "tags": ["digital", "resource", ext if ext else "file"],
        "keywords": ["digital", "resource", name.lower()],
        "language": "English",
        "difficulty": "Unknown",
        "content_type": content_type_map.get(ext, "Document"),
        "target_audience": "General audience",
        "key_topics": [name],
        "_is_mock": True,
        "_ai_provider": "mock"
    }
