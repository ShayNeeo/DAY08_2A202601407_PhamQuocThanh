import re
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")


def clean_text_for_pdf(text: str) -> str:
    """Loại bỏ ký tự không thuộc latin-1 để tránh lỗi font trong fpdf2."""
    # Transliterate common accented/special characters to ASCII/Latin-1
    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text.strip()


def fetch_rmit_page_content(url: str) -> str:
    """Fetch và trích xuất nội dung văn bản từ trang web RMIT Vietnam."""
    print(f"Dang tai du lieu truc tiep tu RMIT: {url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Loi khi tai {url}: {e}")
        return ""

    # Clear HTML scripts, styles, header, footer
    html = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style.*?>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<header.*?>.*?</header>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<footer.*?>.*?</footer>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Extract headings, paragraphs, and list items
    items = re.findall(r"<(h[1-4]|p|li)[^>]*>(.*?)</\1>", html, flags=re.DOTALL | re.IGNORECASE)
    
    extracted_paragraphs = []
    for tag, content in items:
        clean_str = re.sub(r"<.*?>", " ", content)
        clean_str = re.sub(r"\s+", " ", clean_str).strip()
        if len(clean_str) > 25 and not clean_str.startswith("{") and not clean_str.startswith("var "):
            extracted_paragraphs.append(clean_str)

    return "\n\n".join(extracted_paragraphs)


def create_pdf_from_rmit_web(filename: str, title: str, source_url: str, body_text: str):
    """Tạo file PDF từ nội dung crawl trực tiếp từ web RMIT."""
    from fpdf import FPDF

    class RMITPolicyPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 8, "RMIT UNIVERSITY VIETNAM - OFFICIAL ONLINE DOCUMENT", border=False, new_x="LMARGIN", new_y="NEXT", align="C")
            self.line(10, 18, 200, 18)
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = RMITPolicyPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Document Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 6, clean_text_for_pdf(f"Source URL: {source_url}"), align="L")
    pdf.ln(5)

    # Body Content
    pdf.set_font("Helvetica", "", 10)
    paragraphs = body_text.split("\n\n")
    
    for p in paragraphs:
        cleaned_p = clean_text_for_pdf(p)
        if cleaned_p:
            pdf.multi_cell(0, 5, cleaned_p, align="L")
            pdf.ln(3)

    output_path = DATA_DIR / filename
    pdf.output(str(output_path))
    print(f"[OK] Da tao PDF tu du lieu web RMIT: {output_path}")


def collect_rmit_policies():
    """Thu thập dữ liệu trực tiếp từ website chính thức của RMIT Vietnam."""
    setup_directory()

    rmit_pages = [
        {
            "filename": "tuition-fees-rmit.pdf",
            "title": "RMIT Vietnam Tuition Fees and Financial Regulations",
            "url": "https://www.rmit.edu.vn/study-at-rmit/tuition-fees"
        },
        {
            "filename": "scholarships-rmit.pdf",
            "title": "RMIT Vietnam Scholarship Eligibility and Guidelines",
            "url": "https://www.rmit.edu.vn/study-at-rmit/scholarships"
        },
        {
            "filename": "undergraduate-programs-rmit.pdf",
            "title": "RMIT Vietnam Undergraduate Programs and Admission Policy",
            "url": "https://www.rmit.edu.vn/study-at-rmit/undergraduate-programs"
        },
        {
            "filename": "student-services-rmit.pdf",
            "title": "RMIT Vietnam Current Student Services and Regulations",
            "url": "https://www.rmit.edu.vn/students"
        }
    ]

    for page in rmit_pages:
        content = fetch_rmit_page_content(page["url"])
        if content:
            create_pdf_from_rmit_web(
                filename=page["filename"],
                title=page["title"],
                source_url=page["url"],
                body_text=content
            )
        else:
            print(f"[WARNING] Khong lay duoc noi dung tu {page['url']}")


if __name__ == "__main__":
    collect_rmit_policies()


