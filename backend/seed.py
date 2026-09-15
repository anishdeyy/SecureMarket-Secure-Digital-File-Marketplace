"""
SecureMarket Database Seed Script
Run: python seed.py
Creates: 1 admin, 3 sellers, 5 buyers, 10 authentic demo products with REAL file bytes and real SHA-256 hashes, orders, reviews, fraud alerts, audit logs
"""
import sys, os, io, json, zipfile, hashlib, hmac as _hmac
from pathlib import Path
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.services.auth_service import hash_password
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.review import Review
from app.models.fraud import FraudAlert
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.integrity import FileIntegrityRecord, _gen_integrity_id
from app.config import settings

Base.metadata.create_all(bind=engine)
db = SessionLocal()

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"

print("🌱 Seeding SecureMarket database with authentic files & cryptographic integrity...")

# ── File Generators ──────────────────────────────────────────────────────────

def create_pdf_content(title: str, subtitle: str, content: str) -> bytes:
    stream_content = f"""BT
/F1 18 Tf
50 720 Td
({title}) Tj
/F1 12 Tf
0 -30 Td
({subtitle}) Tj
/F1 10 Tf
0 -40 Td
({content[:120]}) Tj
ET"""
    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)

    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{stream_content}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000{300 + stream_len:03d} 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
{380 + stream_len}
%%EOF"""
    return pdf.encode("latin1")

def create_docx_content(title: str, body: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")
        zf.writestr("word/document.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{title}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{body}</w:t></w:r></w:p>
  </w:body>
</w:document>""")
    return buf.getvalue()

def create_xlsx_content(title: str, rows_data: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="worksheets/sheet1.xml"/>
</Relationships>""")
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>""")
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="worksheets/sheet1.xml"/>
</Relationships>""")
        zf.writestr("xl/worksheets/sheet1.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>{title}</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>Revenue Model &amp; Projections</t></is></c></row>
  </sheetData>
</worksheet>""")
    return buf.getvalue()

def create_zip_package(package_name: str, files_dict: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", f"# {package_name}\n\nVerified Digital Asset from SecureMarket.")
        for name, content in files_dict.items():
            zf.writestr(name, content)
    return buf.getvalue()

# ── Users ────────────────────────────────────────────────────────────────────
admin = User(
    id="admin-0001-0000-0000-000000000001",
    email="admin@securemarket.com", username="admin",
    hashed_password=hash_password("Admin@1234"),
    full_name="SecureMarket Admin", role="ADMIN", roles="ADMIN",
    is_email_verified=True, is_active=True, seller_approved=True
)

sellers = [
    User(
        id=f"seller00-0000-0000-0000-00000000000{i}",
        email=f"seller{i}@example.com", username=f"seller{i}",
        hashed_password=hash_password("Seller@1234"),
        full_name=f"Seller {i}", role="SELLER", roles="SELLER",
        is_email_verified=True, is_active=True, seller_approved=True
    )
    for i in range(1, 4)
]

buyers = [
    User(
        id=f"buyer000-0000-0000-0000-00000000000{i}",
        email=f"buyer{i}@example.com", username=f"buyer{i}",
        hashed_password=hash_password("Buyer@1234"),
        full_name=f"Buyer {i}", role="BUYER", roles="BUYER",
        is_email_verified=True, is_active=True
    )
    for i in range(1, 6)
]

for u in [admin] + sellers + buyers:
    existing = db.query(User).filter(User.id == u.id).first()
    if not existing:
        db.add(u)
    else:
        existing.role = u.role
        existing.roles = u.roles
        existing.hashed_password = u.hashed_password
db.commit()
print("✅ Users seeded with strict role separation")

# ── Products Definition & Generation ─────────────────────────────────────────

products_data = [
    {
        "id": "prod0001-0000-0000-0000-000000000001",
        "title": "Complete Python Data Analysis Guide",
        "short_description": "Master data analysis with Python using NumPy, Pandas and Matplotlib.",
        "summary": "A comprehensive guide covering Python for data science. Includes hands-on exercises with real datasets using NumPy, Pandas, Matplotlib, and Seaborn. Perfect for analysts moving from Excel to Python.",
        "category": "Programming", "subcategory": "Python", "price": 250.0,
        "tags": ["python", "pandas", "numpy", "data-analysis", "matplotlib"],
        "keywords": ["python", "data analysis", "pandas", "numpy", "visualization", "data science"],
        "language": "English", "difficulty": "Intermediate", "file_extension": "pdf",
        "original_filename": "python-data-analysis-guide.pdf", "mime_type": "application/pdf",
        "content_type": "PDF Guide", "target_audience": "Data analysts and Python beginners",
        "key_topics": ["NumPy arrays", "Pandas DataFrames", "Data visualization", "Data cleaning"],
        "seller_id": "seller00-0000-0000-0000-000000000001",
        "gen": lambda: create_pdf_content(
            "Complete Python Data Analysis Guide",
            "Master Data Science with Pandas, NumPy and Matplotlib",
            "Comprehensive Python workbook covering DataFrames, group by operations, time series analysis, and Matplotlib visualizations."
        )
    },
    {
        "id": "prod0002-0000-0000-0000-000000000002",
        "title": "Modern Professional Resume Template",
        "short_description": "ATS-friendly resume template in DOCX format with clean modern design.",
        "summary": "A professionally designed resume template optimized for Applicant Tracking Systems. Includes cover letter template and reference page. Easy to customize in Microsoft Word.",
        "category": "Templates", "subcategory": "Resume", "price": 149.0,
        "tags": ["resume", "cv", "template", "professional", "ats-friendly"],
        "keywords": ["resume template", "cv", "job application", "word template", "professional"],
        "language": "English", "difficulty": "Beginner", "file_extension": "docx",
        "original_filename": "modern-resume-template.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "content_type": "Design Template", "target_audience": "Job seekers",
        "key_topics": ["Resume design", "ATS optimization", "Cover letter"],
        "seller_id": "seller00-0000-0000-0000-000000000001",
        "gen": lambda: create_docx_content(
            "Modern Professional Resume Template",
            "ATS-Friendly Word Resume Template with clean typography, skills layout, and professional project section."
        )
    },
    {
        "id": "prod0003-0000-0000-0000-000000000003",
        "title": "React Dashboard UI Component Kit",
        "short_description": "50+ reusable React components with Tailwind CSS for admin dashboards.",
        "summary": "A production-ready UI kit with 50+ components for building modern admin dashboards. Includes charts, tables, forms, modals, and navigation components. Built with React, TypeScript, and Tailwind CSS.",
        "category": "Design", "subcategory": "UI Kits", "price": 250.0,
        "tags": ["react", "typescript", "tailwind", "ui-kit", "dashboard", "components"],
        "keywords": ["react", "ui kit", "dashboard", "tailwind css", "typescript", "components"],
        "language": "English", "difficulty": "Intermediate", "file_extension": "zip",
        "original_filename": "react-dashboard-ui-kit.zip", "mime_type": "application/zip",
        "content_type": "ZIP Package", "target_audience": "Frontend developers",
        "key_topics": ["React components", "Tailwind CSS", "Dashboard design", "TypeScript"],
        "seller_id": "seller00-0000-0000-0000-000000000002",
        "gen": lambda: create_zip_package("React Dashboard UI Kit", {
            "package.json": json.dumps({"name": "react-dashboard-ui-kit", "version": "1.0.0", "dependencies": {"react": "^18.2.0"}}, indent=2),
            "src/Button.tsx": "export const Button = () => <button className='btn'>Click Me</button>;",
            "src/Sidebar.tsx": "export const Sidebar = () => <aside>Navigation</aside>;",
            "src/Chart.tsx": "export const Chart = () => <div>Interactive Chart Component</div>;"
        })
    },
    {
        "id": "prod0004-0000-0000-0000-000000000004",
        "title": "Social Media Design Pack — 200 Templates",
        "short_description": "200 editable social media templates for Instagram, Facebook, Twitter and LinkedIn.",
        "summary": "A massive collection of 200 social media templates across all major platforms. Includes post, story, and cover templates. Fully editable with Canva or Photoshop. Suitable for businesses and content creators.",
        "category": "Design", "subcategory": "Social Media", "price": 250.0,
        "tags": ["social-media", "instagram", "templates", "canva", "marketing"],
        "keywords": ["social media templates", "instagram", "facebook", "canva", "graphic design"],
        "language": "English", "difficulty": "Beginner", "file_extension": "zip",
        "original_filename": "social-media-design-pack.zip", "mime_type": "application/zip",
        "content_type": "ZIP Package", "target_audience": "Content creators and small businesses",
        "key_topics": ["Social media marketing", "Graphic design", "Brand identity"],
        "seller_id": "seller00-0000-0000-0000-000000000002",
        "gen": lambda: create_zip_package("Social Media Design Pack", {
            "templates/instagram-post.svg": "<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1080'><rect width='1080' height='1080' fill='#4f46e5'/><text x='100' y='500' fill='white' font-size='48'>Social Media Post</text></svg>",
            "templates/twitter-header.svg": "<svg xmlns='http://www.w3.org/2000/svg' width='1500' height='500'><rect width='1500' height='500' fill='#0284c7'/></svg>",
            "guidelines.txt": "Use Canva or Figma to edit colors and typography."
        })
    },
    {
        "id": "prod0005-0000-0000-0000-000000000005",
        "title": "Business Proposal Template",
        "short_description": "Professional business proposal template with executive summary and financial projections.",
        "summary": "A comprehensive business proposal template suitable for startups and SMEs. Includes sections for executive summary, problem statement, solution, market analysis, financial projections, and team bios. Available in DOCX format.",
        "category": "Business", "subcategory": "Proposals", "price": 199.0,
        "tags": ["business", "proposal", "template", "startup", "finance"],
        "keywords": ["business proposal", "startup", "pitch deck", "financial projections", "executive summary"],
        "language": "English", "difficulty": "Intermediate", "file_extension": "docx",
        "original_filename": "business-proposal-template.docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "content_type": "Document", "target_audience": "Entrepreneurs and business owners",
        "key_topics": ["Business planning", "Financial modeling", "Investor pitch"],
        "seller_id": "seller00-0000-0000-0000-000000000002",
        "gen": lambda: create_docx_content(
            "Business Proposal Template",
            "Executive Summary, Scope of Work, Deliverables, Investment Table, and Acceptance Terms."
        )
    },
    {
        "id": "prod0006-0000-0000-0000-000000000006",
        "title": "Excel Financial Model — Startup Valuation",
        "short_description": "DCF-based startup valuation model with scenario analysis and investor metrics.",
        "summary": "A fully dynamic Excel model for startup valuation using Discounted Cash Flow (DCF) methodology. Includes revenue projections, cost modeling, cap table, investor returns, and scenario analysis. Protected formulas with instruction tab.",
        "category": "Finance", "subcategory": "Financial Models", "price": 250.0,
        "tags": ["excel", "finance", "valuation", "startup", "dcf", "model"],
        "keywords": ["excel financial model", "startup valuation", "dcf", "cap table", "financial projections"],
        "language": "English", "difficulty": "Advanced", "file_extension": "xlsx",
        "original_filename": "startup-valuation-model.xlsx", "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "content_type": "Spreadsheet", "target_audience": "Startup founders and financial analysts",
        "key_topics": ["DCF valuation", "Cap table", "Revenue modeling", "Investor metrics"],
        "seller_id": "seller00-0000-0000-0000-000000000003",
        "gen": lambda: create_xlsx_content("Startup Valuation DCF Model", [
            ["Year 1", "Year 2", "Year 3"],
            [100000, 350000, 950000]
        ])
    },
    {
        "id": "prod0007-0000-0000-0000-000000000007",
        "title": "JavaScript Interview Preparation Guide",
        "short_description": "250+ JavaScript interview questions with detailed answers covering ES6+, async, and DOM.",
        "summary": "A curated collection of 250+ JavaScript interview questions covering core concepts, ES6+, closures, promises, async/await, event loop, prototype chain, and DOM manipulation. Each question includes a detailed explanation and code examples.",
        "category": "Education", "subcategory": "Interview Prep", "price": 250.0,
        "tags": ["javascript", "interview", "es6", "async", "promises", "coding"],
        "keywords": ["javascript interview", "es6", "async await", "closures", "prototype", "frontend"],
        "language": "English", "difficulty": "Intermediate", "file_extension": "pdf",
        "original_filename": "javascript-interview-guide.pdf", "mime_type": "application/pdf",
        "content_type": "PDF Guide", "target_audience": "JavaScript developers preparing for interviews",
        "key_topics": ["ES6+", "Closures", "Async/Await", "Event loop", "DOM"],
        "seller_id": "seller00-0000-0000-0000-000000000003",
        "gen": lambda: create_pdf_content(
            "JavaScript Interview Preparation Guide",
            "250+ Senior JS Interview Questions & Answers",
            "Topics: Closures, Event Loop, Promises, Prototypal Inheritance, Web Vitals, and TypeScript generics."
        )
    },
    {
        "id": "prod0008-0000-0000-0000-000000000008",
        "title": "PowerPoint Presentation Template Pack",
        "short_description": "15 professional PowerPoint presentation themes for business and education.",
        "summary": "A collection of 15 professionally designed PowerPoint themes suitable for business presentations, pitch decks, educational content, and reports. Each theme includes 30+ slide layouts, custom color palettes, and icon sets.",
        "category": "Templates", "subcategory": "Presentations", "price": 249.0,
        "tags": ["powerpoint", "presentation", "template", "business", "slides"],
        "keywords": ["powerpoint template", "presentation design", "slides", "pitch deck", "business"],
        "language": "English", "difficulty": "Beginner", "file_extension": "zip",
        "original_filename": "presentation-template-pack.zip", "mime_type": "application/zip",
        "content_type": "ZIP Package", "target_audience": "Professionals and educators",
        "key_topics": ["Presentation design", "Slide layouts", "Business communication"],
        "seller_id": "seller00-0000-0000-0000-000000000001",
        "gen": lambda: create_zip_package("PowerPoint Presentation Pack", {
            "slide1.xml": "<slide><title>Executive Overview</title></slide>",
            "slide2.xml": "<slide><title>Market Opportunity</title></slide>",
            "palettes.json": json.dumps({"primary": "#2563eb", "accent": "#10b981"}, indent=2)
        })
    },
    {
        "id": "prod0009-0000-0000-0000-000000000009",
        "title": "Digital Marketing Complete Guide 2024",
        "short_description": "Actionable guide to SEO, content marketing, social media, email, and paid ads.",
        "summary": "A comprehensive guide covering all major digital marketing channels. Includes SEO fundamentals, content strategy, social media marketing, email campaigns, Google Ads, Meta Ads, analytics, and conversion optimization. Includes templates and checklists.",
        "category": "Marketing", "subcategory": "Digital Marketing", "price": 250.0,
        "tags": ["marketing", "seo", "social-media", "email-marketing", "google-ads", "content"],
        "keywords": ["digital marketing", "seo", "content marketing", "social media", "email marketing", "google ads"],
        "language": "English", "difficulty": "Beginner", "file_extension": "pdf",
        "original_filename": "digital-marketing-guide-2024.pdf", "mime_type": "application/pdf",
        "content_type": "PDF Guide", "target_audience": "Small business owners and marketing beginners",
        "key_topics": ["SEO", "Content marketing", "Social media", "Email marketing", "PPC"],
        "seller_id": "seller00-0000-0000-0000-000000000003",
        "gen": lambda: create_pdf_content(
            "Digital Marketing Complete Guide 2024",
            "SEO, Content Strategy, and Paid Acquisition Handbook",
            "Actionable playbooks covering Keyword Research, On-Page SEO, Google Ads ROAS optimization, and Meta Ads scaling."
        )
    },
    {
        "id": "prod0010-0000-0000-0000-000000000010",
        "title": "SQL Practice Workbook — 300 Exercises",
        "short_description": "300 SQL exercises from beginner to advanced with solutions and explanations.",
        "summary": "A structured SQL practice workbook with 300 exercises organized by topic: SELECT queries, JOINs, subqueries, aggregations, window functions, CTEs, and performance optimization. Includes sample databases and solution keys. Compatible with PostgreSQL, MySQL, and SQLite.",
        "category": "Programming", "subcategory": "SQL", "price": 250.0,
        "tags": ["sql", "database", "postgresql", "mysql", "exercises", "learning"],
        "keywords": ["sql", "database", "postgresql", "mysql", "joins", "window functions", "practice"],
        "language": "English", "difficulty": "Beginner", "file_extension": "pdf",
        "original_filename": "sql-practice-workbook.pdf", "mime_type": "application/pdf",
        "content_type": "PDF Guide", "target_audience": "Developers and data analysts learning SQL",
        "key_topics": ["SELECT queries", "JOINs", "Subqueries", "Window functions", "CTEs"],
        "seller_id": "seller00-0000-0000-0000-000000000001",
        "gen": lambda: create_pdf_content(
            "SQL Practice Workbook - 300 Exercises",
            "From Basic Queries to Advanced Window Functions",
            "Hands-on exercises covering SELECT, JOINs, aggregations, Window Functions (ROW_NUMBER, RANK), and Common Table Expressions."
        )
    },
]

for pd in products_data:
    pid = pd["id"]
    filename = pd["original_filename"]
    raw_bytes = pd["gen"]()
    real_hash = hashlib.sha256(raw_bytes).hexdigest()
    file_size = len(raw_bytes)

    # Write file to storage
    storage_rel_key = f"products/demo/{pid}/{filename}"
    disk_path = STORAGE_DIR / "products" / "demo" / pid / filename
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    disk_path.write_bytes(raw_bytes)

    # Upsert product
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        p = Product(
            id=pid, seller_id=pd["seller_id"], title=pd["title"],
            short_description=pd["short_description"], summary=pd["summary"],
            category=pd["category"], subcategory=pd["subcategory"], price=pd["price"],
            tags=json.dumps(pd["tags"]), keywords=json.dumps(pd["keywords"]),
            language=pd["language"], difficulty=pd["difficulty"],
            original_filename=filename, file_extension=pd["file_extension"],
            mime_type=pd["mime_type"], file_size_bytes=file_size,
            sha256_hash=real_hash, storage_key=storage_rel_key,
            status="published", price_status="APPROVED", scan_status="clean", is_active=True,
            ai_metadata_generated=True, avg_rating=0.0, review_count=0, total_sales=12,
            content_type=pd.get("content_type"), target_audience=pd.get("target_audience"),
            key_topics=json.dumps(pd.get("key_topics", [])),
            published_at=datetime.utcnow() - timedelta(days=10)
        )
        db.add(p)
    else:
        p.title = pd["title"]
        p.price = pd["price"]
        p.sha256_hash = real_hash
        p.file_size_bytes = file_size
        p.storage_key = storage_rel_key
        p.original_filename = filename
        p.status = "published"
        p.price_status = "APPROVED"
        p.is_active = True

    # Upsert FileIntegrityRecord with HMAC seal
    rec = db.query(FileIntegrityRecord).filter(FileIntegrityRecord.product_id == pid).first()
    secret = settings.JWT_SECRET.encode()
    if not rec:
        iid = _gen_integrity_id()
        seal = _hmac.new(secret, f"{iid}:{real_hash}".encode(), hashlib.sha256).hexdigest()
        rec = FileIntegrityRecord(
            integrity_id=iid,
            product_id=pid,
            seller_id=pd["seller_id"],
            sha256_hash=real_hash,
            file_size=str(file_size),
            original_filename=filename,
            mime_type=pd["mime_type"],
            hmac_seal=seal,
            is_verified=True,
            tampered_detected=False,
            verified_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            notes="Seeded demo product with verified physical file bytes",
        )
        db.add(rec)
        p.integrity_id = iid
    else:
        seal = _hmac.new(secret, f"{rec.integrity_id}:{real_hash}".encode(), hashlib.sha256).hexdigest()
        rec.sha256_hash = real_hash
        rec.file_size = str(file_size)
        rec.original_filename = filename
        rec.hmac_seal = seal
        rec.is_verified = True
        rec.tampered_detected = False
        p.integrity_id = rec.integrity_id

db.commit()
print("✅ Products & real SHA-256 integrity records seeded")

# ── Orders & Payments ────────────────────────────────────────────────────────
for i, buyer in enumerate(buyers[:3]):
    prod = db.query(Product).filter(Product.id == products_data[i]["id"]).first()
    order_id = f"order0{i+1}00-0000-0000-0000-000000000000"
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        order = Order(
            id=order_id, order_number=f"ORD-10000{i+1}", buyer_id=buyer.id,
            status="paid", total_amount=prod.price, subtotal=prod.price,
            platform_fee=0.0, service_fee=0.0, tax=0.0,
            currency="INR", risk_score=5, risk_level="low", risk_reasons="[]",
            paid_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(order)
        db.flush()
        oi = OrderItem(
            order_id=order.id, product_id=prod.id, seller_id=prod.seller_id,
            price_at_purchase=prod.price, subtotal=prod.price,
            download_count=1, download_limit=5, download_enabled=True
        )
        db.add(oi)
        payment = Payment(
            order_id=order.id, amount=prod.price, currency="INR",
            status="success", gateway="razorpay",
            gateway_order_id=f"order_test_{i+1}000",
            gateway_payment_id=f"pay_test_{i+1}000", is_mock=False,
            completed_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(payment)
db.commit()
print("✅ Orders & payments seeded")

# ── Reviews ──────────────────────────────────────────────────────────────────
reviews_data = [
    ("buyer000-0000-0000-0000-000000000001", "prod0001-0000-0000-0000-000000000001", "order0100-0000-0000-0000-000000000000", 5, "Excellent guide!", "Very well structured and easy to follow. The Pandas section alone was worth the price."),
    ("buyer000-0000-0000-0000-000000000002", "prod0002-0000-0000-0000-000000000002", "order0200-0000-0000-0000-000000000000", 4, "Great template", "Professional looking and easy to edit. Got interviews within a week!"),
    ("buyer000-0000-0000-0000-000000000003", "prod0003-0000-0000-0000-000000000003", "order0300-0000-0000-0000-000000000000", 5, "Saved weeks of work", "The component quality is top notch. Very clean code with TypeScript."),
]
for uid, pid, oid, rating, title, body in reviews_data:
    if not db.query(Review).filter(Review.user_id == uid, Review.product_id == pid).first():
        db.add(Review(user_id=uid, product_id=pid, order_id=oid, rating=rating, title=title, body=body, is_verified_purchase=True))
db.commit()

# Recalculate true ratings
for p in db.query(Product).all():
    revs = db.query(Review).filter(Review.product_id == p.id, Review.status == "active").all()
    p.review_count = len(revs)
    p.avg_rating = round(sum(r.rating for r in revs) / len(revs), 2) if revs else 0.0
db.commit()
print("✅ Reviews synced and accurate ratings computed")

# ── Fraud Alert Sample ───────────────────────────────────────────────────────
if not db.query(FraudAlert).first():
    db.add(FraudAlert(
        user_id="buyer000-0000-0000-0000-000000000004",
        order_id="order0100-0000-0000-0000-000000000000",
        risk_score=72, risk_level="high",
        reasons=json.dumps(["7 failed payment attempts in 24h", "Unusual purchase velocity", "New device detected"]),
        status="open", ip_address="192.168.1.100"
    ))
db.commit()

# ── Audit Logs ───────────────────────────────────────────────────────────────
events = [
    ("USER_REGISTERED", "buyer000-0000-0000-0000-000000000001", "User registered: buyer1@example.com"),
    ("LOGIN_SUCCESS", "buyer000-0000-0000-0000-000000000001", "Login from 127.0.0.1"),
    ("FILE_UPLOADED", "seller00-0000-0000-0000-000000000001", "python-data-analysis-guide.pdf"),
    ("MALWARE_SCAN_PASSED", "seller00-0000-0000-0000-000000000001", "File passed security scan"),
    ("AI_METADATA_GENERATED", "seller00-0000-0000-0000-000000000001", "Gemini generated metadata"),
    ("PRODUCT_PUBLISHED", "seller00-0000-0000-0000-000000000001", "Product published"),
    ("PAYMENT_SUCCESS", "buyer000-0000-0000-0000-000000000001", "Order ORD-100001 paid"),
    ("DOWNLOAD_SUCCESS", "buyer000-0000-0000-0000-000000000001", "File downloaded"),
]
for event, uid, desc in events:
    db.add(AuditLog(user_id=uid, event=event, description=desc, ip_address="127.0.0.1"))
db.commit()

# ── Notifications ────────────────────────────────────────────────────────────
if not db.query(Notification).first():
    db.add(Notification(user_id="seller00-0000-0000-0000-000000000001",
        title="✨ AI Metadata Generated", message="Gemini generated metadata for your product.", type="success"))
    db.add(Notification(user_id="buyer000-0000-0000-0000-000000000001",
        title="Purchase Successful! 🎉", message="Your order ORD-100001 is confirmed. Download is ready.", type="success"))
    db.commit()

db.close()
print("\n✅ Seed complete with verified SHA-256 files!")
