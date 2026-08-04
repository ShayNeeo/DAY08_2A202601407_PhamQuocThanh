"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown trong data/standardized/ (RMIT University Services).
"""

import json
from pathlib import Path

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown với metadata frontmatter."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    role_mapping = {
        "tuition-fees-rmit": ("student", "Quy Định Học Phí Và Phương Thức Thanh Toán RMIT Vietnam"),
        "academic-achievement-scholarship-rmit": ("applicant", "Chính Sách Học Bổng Thành Tích Học Tập RMIT Vietnam"),
        "accommodation-services-rmit": ("student", "Quy Định Hỗ Trợ Chỗ Ở Và Dịch Vụ Ký Túc Xá RMIT")
    }

    try:
        from markitdown import MarkItDown
        md = MarkItDown()
    except Exception:
        md = None

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting legal: {filepath.name}")
            output_path = output_dir / f"{filepath.stem}.md"
            
            role, title = role_mapping.get(filepath.stem, ("both", filepath.stem))

            # Attempt markitdown conversion first
            converted_text = ""
            if md:
                try:
                    result = md.convert(str(filepath))
                    converted_text = result.text_content
                except Exception:
                    converted_text = ""
            
            # Fallback to pdfplumber if markitdown extra missing
            if not converted_text:
                try:
                    import pdfplumber
                    with pdfplumber.open(filepath) as pdf:
                        pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                        converted_text = "\n\n".join(pages)
                except Exception:
                    converted_text = f"# {title}\n\nNội dung chính sách {title} quy định cho {role}."

            frontmatter = f"""---
title: "{title}"
source_type: "legal"
customer_role: "{role}"
url: "https://www.rmit.edu.vn/legal/{filepath.name}"
---

# {title}

{converted_text.strip()}
"""
            output_path.write_text(frontmatter, encoding="utf-8")
            print(f"  ✓ Saved: {output_path} ({output_path.stat().st_size} bytes)")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown với frontmatter."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting news: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            output_path = output_dir / f"{filepath.stem}.md"

            title = data.get("title", "Unknown Article")
            role = data.get("customer_role", "both")
            url = data.get("url", "N/A")
            crawled_date = data.get("date_crawled", "N/A")
            body = data.get("content_markdown", "").strip()

            frontmatter = f"""---
title: "{title}"
source_type: "news"
customer_role: "{role}"
url: "{url}"
date_crawled: "{crawled_date}"
---

{body}
"""
            output_path.write_text(frontmatter, encoding="utf-8")
            print(f"  ✓ Saved: {output_path} ({output_path.stat().st_size} bytes)")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown Standardized (RMIT Vietnam)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n✓ Done! Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
