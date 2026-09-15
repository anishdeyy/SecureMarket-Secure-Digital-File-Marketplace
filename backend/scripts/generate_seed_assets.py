"""
Generate authentic demo files on disk for all 10 predefined products,
calculate their exact SHA-256 hashes from raw bytes, and update the SQLite database.
"""
import os, sys, io, zipfile, hashlib, json, sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = BASE_DIR / "securemarket.db"

def create_pdf_content(title: str, subtitle: str, content: str) -> bytes:
    """Create a valid PDF-1.4 file with standard catalog, pages, and stream."""
    stream_content = f"""BT
/F1 18 Tf
50 720 Td
({title}) Tj
/F1 12 Tf
0 -30 Td
({subtitle}) Tj
/F1 10 Tf
0 -40 Td
({content[:100]}) Tj
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
    """Create a valid OpenXML DOCX archive."""
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
    """Create a valid OpenXML XLSX spreadsheet archive."""
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
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>""")
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""")
        zf.writestr("xl/worksheets/sheet1.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>{title}</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>Revenue Model &amp; Metrics</t></is></c></row>
  </sheetData>
</worksheet>""")
    return buf.getvalue()

def create_zip_package(package_name: str, files_dict: dict) -> bytes:
    """Create a ZIP archive with multiple project files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", f"# {package_name}\n\nVerified Digital Asset from SecureMarket.")
        for name, content in files_dict.items():
            zf.writestr(name, content)
    return buf.getvalue()

SEED_SPECS = [
    {
        "id": "prod0001-0000-0000-0000-000000000001",
        "filename": "python-data-analysis-guide.pdf",
        "type": "pdf",
        "gen": lambda: create_pdf_content(
            "Complete Python Data Analysis Guide",
            "Master Data Science with Pandas, NumPy and Matplotlib",
            "Comprehensive Python workbook covering DataFrames, group by operations, time series analysis, and Matplotlib visualizations."
        )
    },
    {
        "id": "prod0002-0000-0000-0000-000000000002",
        "filename": "modern-resume-template.docx",
        "type": "docx",
        "gen": lambda: create_docx_content(
            "Modern Professional Resume Template",
            "ATS-Friendly Word Resume Template with clean typography, skills layout, and professional project section."
        )
    },
    {
        "id": "prod0003-0000-0000-0000-000000000003",
        "filename": "react-dashboard-ui-kit.zip",
        "type": "zip",
        "gen": lambda: create_zip_package("React Dashboard UI Kit", {
            "package.json": json.dumps({"name": "react-dashboard-ui-kit", "version": "1.0.0", "dependencies": {"react": "^18.2.0"}}, indent=2),
            "src/Button.tsx": "export const Button = () => <button className='btn'>Click Me</button>;",
            "src/Sidebar.tsx": "export const Sidebar = () => <aside>Navigation</aside>;",
            "src/Chart.tsx": "export const Chart = () => <div>Interactive Chart Component</div>;"
        })
    },
    {
        "id": "prod0004-0000-0000-0000-000000000004",
        "filename": "social-media-design-pack.zip",
        "type": "zip",
        "gen": lambda: create_zip_package("Social Media Design Pack", {
            "templates/instagram-post.svg": "<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1080'><rect width='1080' height='1080' fill='#4f46e5'/><text x='100' y='500' fill='white' font-size='48'>Social Media Post</text></svg>",
            "templates/twitter-header.svg": "<svg xmlns='http://www.w3.org/2000/svg' width='1500' height='500'><rect width='1500' height='500' fill='#0284c7'/></svg>",
            "guidelines.txt": "Use Canva or Figma to edit colors and typography."
        })
    },
    {
        "id": "prod0005-0000-0000-0000-000000000005",
        "filename": "business-proposal-template.docx",
        "type": "docx",
        "gen": lambda: create_docx_content(
            "Business Proposal Template",
            "Executive Summary, Scope of Work, Deliverables, Investment Table, and Acceptance Terms."
        )
    },
    {
        "id": "prod0006-0000-0000-0000-000000000006",
        "filename": "startup-valuation-model.xlsx",
        "type": "xlsx",
        "gen": lambda: create_xlsx_content("Startup Valuation DCF Model", [
            ["Year 1", "Year 2", "Year 3"],
            [100000, 350000, 950000]
        ])
    },
    {
        "id": "prod0007-0000-0000-0000-000000000007",
        "filename": "javascript-interview-guide.pdf",
        "type": "pdf",
        "gen": lambda: create_pdf_content(
            "JavaScript Interview Preparation Guide",
            "250+ Senior JS Interview Questions & Answers",
            "Topics: Closures, Event Loop, Promises, Prototypal Inheritance, Web Vitals, and TypeScript generics."
        )
    },
    {
        "id": "prod0008-0000-0000-0000-000000000008",
        "filename": "presentation-template-pack.zip",
        "type": "zip",
        "gen": lambda: create_zip_package("PowerPoint Presentation Pack", {
            "slide1.xml": "<slide><title>Executive Overview</title></slide>",
            "slide2.xml": "<slide><title>Market Opportunity</title></slide>",
            "palettes.json": json.dumps({"primary": "#2563eb", "accent": "#10b981"}, indent=2)
        })
    },
    {
        "id": "prod0009-0000-0000-0000-000000000009",
        "filename": "digital-marketing-guide-2024.pdf",
        "type": "pdf",
        "gen": lambda: create_pdf_content(
            "Digital Marketing Complete Guide 2024",
            "SEO, Content Strategy, and Paid Acquisition Handbook",
            "Actionable playbooks covering Keyword Research, On-Page SEO, Google Ads ROAS optimization, and Meta Ads scaling."
        )
    },
    {
        "id": "prod0010-0000-0000-0000-000000000010",
        "filename": "sql-practice-workbook.pdf",
        "type": "pdf",
        "gen": lambda: create_pdf_content(
            "SQL Practice Workbook - 300 Exercises",
            "From Basic Queries to Advanced Window Functions",
            "Hands-on exercises covering SELECT, JOINs, aggregations, Window Functions (ROW_NUMBER, RANK), and Common Table Expressions."
        )
    }
]

def main():
    print("[*] Generating authentic demo files and calculating real SHA-256 fingerprints...")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    jwt_secret = "securemarket-jwt-secret-change-in-production-2026"
    import hmac

    for spec in SEED_SPECS:
        pid = spec["id"]
        filename = spec["filename"]
        raw_bytes = spec["gen"]()
        real_hash = hashlib.sha256(raw_bytes).hexdigest()
        file_size = len(raw_bytes)

        # Write to storage
        storage_rel_key = f"products/demo/{pid}/{filename}"
        disk_path = STORAGE_DIR / "products" / "demo" / pid / filename
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        disk_path.write_bytes(raw_bytes)

        print(f"  [+] {filename}")
        print(f"      Path:    {storage_rel_key}")
        print(f"      Size:    {file_size} bytes")
        print(f"      SHA-256: {real_hash}")

        # Update product in database
        cur.execute("""
            UPDATE products 
            SET sha256_hash = ?, file_size_bytes = ?, storage_key = ?, original_filename = ?
            WHERE id = ?
        """, (real_hash, file_size, storage_rel_key, filename, pid))

        # Check existing integrity record
        cur.execute("SELECT integrity_id FROM file_integrity_records WHERE product_id = ?", (pid,))
        row = cur.fetchone()
        if row:
            iid = row[0]
            seal = hmac.new(jwt_secret.encode(), f"{iid}:{real_hash}".encode(), hashlib.sha256).hexdigest()
            cur.execute("""
                UPDATE file_integrity_records
                SET sha256_hash = ?, file_size = ?, hmac_seal = ?, original_filename = ?, is_verified = 1, tampered_detected = 0
                WHERE product_id = ?
            """, (real_hash, str(file_size), seal, filename, pid))
            print(f"      Integrity: {iid} (HMAC updated)")
        else:
            # Generate new integrity record
            import random, string
            rand_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            iid = f"FI-{rand_code}"
            seal = hmac.new(jwt_secret.encode(), f"{iid}:{real_hash}".encode(), hashlib.sha256).hexdigest()
            cur.execute("""
                INSERT INTO file_integrity_records 
                (integrity_id, product_id, seller_id, sha256_hash, file_size, original_filename, mime_type, hmac_seal, is_verified, tampered_detected, verified_at, created_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, datetime('now'), datetime('now'), 'Seeded demo asset with real file bytes')
            """, (iid, pid, "seller00-0000-0000-0000-000000000001", real_hash, str(file_size), filename, "application/octet-stream", seal))
            cur.execute("UPDATE products SET integrity_id = ? WHERE id = ?", (iid, pid))
            print(f"      Integrity: {iid} (Created)")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] All 10 demo products now have REAL files on disk and REAL SHA-256 fingerprints in the database!")

if __name__ == "__main__":
    main()
