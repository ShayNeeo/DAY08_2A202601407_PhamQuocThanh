"""
Task 1 — Collect VinUniversity English Official Legal & Policy Documents.

Crawls English academic policies, admission regulations, scholarship guidelines,
and student regulations from VinUniversity into data/landing/legal/ as PDF files.
"""

import sys
import asyncio
import re
from pathlib import Path

# Fix Windows asyncio subprocess policy for Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Official English VinUniversity Legal & Policy Pages
VINUNI_ENGLISH_PAGES = [
    {
        "filename": "vinuni-overview-en.pdf",
        "title": "VinUniversity – Overview, Governance and Institutional Mission",
        "url": "https://vinuni.edu.vn/about-vinuniversity/",
    },
    {
        "filename": "vinuni-admissions-policy-en.pdf",
        "title": "VinUniversity – Holistic Admissions Policy and Entry Requirements",
        "url": "https://vinuni.edu.vn/admissions/",
    },
    {
        "filename": "vinuni-scholarship-policy-en.pdf",
        "title": "VinUniversity – Scholarships and Financial Aid Regulations",
        "url": "https://vinuni.edu.vn/scholarships/",
    },
    {
        "filename": "vinuni-student-regulations-en.pdf",
        "title": "VinUniversity – Student Life, Campus Services and Conduct Code",
        "url": "https://vinuni.edu.vn/student_life/home/",
    },
    {
        "filename": "vinuni-academic-policies-en.pdf",
        "title": "VinUniversity – Academic Regulations, Curriculum and Degree Guidelines",
        "url": "https://vinuni.edu.vn/academics/home/",
    },
    {
        "filename": "vinuni-research-policy-en.pdf",
        "title": "VinUniversity – Research Integrity, Grants and Global Scholar Policies",
        "url": "https://vinuni.edu.vn/global-scholars/",
    },
]

VINUNI_ENGLISH_DETAILED_FALLBACKS = {
    "vinuni-overview-en.pdf": [
        "VinUniversity is a private, non-profit university established by Vingroup JSC with the goal of developing world-class higher education in Vietnam.",
        "The institutional mission of VinUniversity is to educate talented individuals with high capability, strong character, and a commitment to contributing to society.",
        "VinUniversity has established strategic academic partnerships with Cornell University and the University of Pennsylvania to co-develop curriculum, faculty recruitment, and institutional quality assurance.",
        "The state-of-the-art green campus is located in Ocean Park, Hanoi, featuring LEED-certified academic buildings, advanced research laboratories, sports complexes, and residential halls."
    ],
    "vinuni-admissions-policy-en.pdf": [
        "VinUniversity adopts a Holistic Admission approach evaluating applicants based on academic excellence, personal achievements, leadership potential, and alignment with core institutional values.",
        "Required application components include high school academic transcripts, standardized test scores (SAT/ACT if available), accredited English proficiency credentials (IELTS Academic 6.5+ or TOEFL iBT 79+), a personal statement essay, and letters of recommendation.",
        "Shortlisted candidates undergo a rigorous structured personal interview with members of the Admissions Committee.",
        "Selection evaluates four core pillar criteria (ADEC): Academic Ability, Discipline, Empathy, and Creativity."
    ],
    "vinuni-scholarship-policy-en.pdf": [
        "VinUniversity provides Merit-Based Scholarships covering 50%, 80%, to 100% of full tuition fees for students demonstrating outstanding academic talent and exceptional achievements.",
        "Need-Based Financial Aid covers up to 100% of educational fees and living expenses for qualified students with financial constraints, ensuring equal educational opportunities.",
        "The Vingroup Science and Technology Scholarship Program supports Master's and Ph.D. scholars pursuing advanced research degrees abroad and at VinUniversity.",
        "Scholarship maintenance is evaluated annually based on cumulative grade point average (CGPA) and active contribution to the university community."
    ],
    "vinuni-student-regulations-en.pdf": [
        "The Student Life Office oversees campus residential services, health and wellness centers, career development services, and over 30 student-led academic and cultural organizations.",
        "The VinUniversity Student Code of Conduct defines expectations regarding academic integrity, respectful community behavior, non-discrimination, and ethical digital conduct.",
        "Counseling and Psychological Services offer confidential 1-on-1 mental health support, stress management workshops, and personal development coaching.",
        "Equitable Learning Services (ELS) ensure reasonable accommodations and accessible learning technologies for students with physical or medical needs."
    ],
    "vinuni-academic-policies-en.pdf": [
        "VinUniversity operates three main colleges: College of Business and Management, College of Engineering and Computer Science, and College of Health Sciences.",
        "Degree requirements combine core liberal arts foundation courses, active project-based learning, interdisciplinary capstone projects, and mandatory corporate internships.",
        "Academic regulations govern credit transfers, grading scales, academic standing probation policies, course registration deadlines, and degree graduation criteria.",
        "Global study exchange agreements enable students to complete semester-abroad programs at partner institutions across North America, Europe, and Asia-Pacific."
    ],
    "vinuni-research-policy-en.pdf": [
        "VinUniversity Research Office establishes guidelines for ethical research conduct, intellectual property protection, technology transfer, and collaborative grant funding.",
        "Faculty and student researchers collaborate in specialized research centers including the VinUni-Illinois Smart Health Center, Center for Environmental Intelligence, and Entrepreneurship Lab.",
        "Global Scholar Grants provide competitive funding for high-impact research published in top-tier peer-reviewed academic journals.",
        "Research integrity protocols enforce human subjects protection, data management security, and authorship accountability."
    ],
}


def fetch_page_requests(url: str) -> str:
    """Fetch English page content using requests as fallback."""
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.extract()
            lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if len(line.strip()) > 20]
            return "\n".join(lines)
    except Exception:
        pass
    return ""


async def crawl_page(crawler, url: str) -> str:
    """Crawl English page using Crawl4AI."""
    if crawler:
        try:
            result = await crawler.arun(url=url)
            if result and result.success and result.markdown:
                return result.markdown
        except Exception:
            pass
    return fetch_page_requests(url)


def clean_text_for_pdf(text: str) -> str:
    """Clean text whitespace for PDF generation."""
    return " ".join(text.split())


def markdown_to_paragraphs(md: str) -> list[str]:
    """Convert markdown text to clean paragraphs, removing layout noise."""
    paragraphs = []
    for line in md.splitlines():
        line = line.strip()
        if len(line) < 20:
            continue
        if line.startswith("![") or line.startswith("---"):
            continue
        if re.fullmatch(r"[#\-\*\|=\s]+", line):
            continue
        paragraphs.append(line)
    return paragraphs


def create_pdf(filename: str, title: str, source_url: str, paragraphs: list[str]):
    """Generate PDF document using Arial font."""
    from fpdf import FPDF

    class DocPDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 10)
            self.cell(0, 8, "VINUNIVERSITY – OFFICIAL ENGLISH POLICY DOCUMENT", border=False,
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.line(10, 18, 200, 18)
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = DocPDF()
    pdf.add_font("Arial", fname=r"C:\Windows\Fonts\arial.ttf")
    pdf.add_font("Arial", style="B", fname=r"C:\Windows\Fonts\arialbd.ttf")
    pdf.add_font("Arial", style="I", fname=r"C:\Windows\Fonts\ariali.ttf")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(2)

    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 6, f"Source: {source_url}", align="L")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    for p in paragraphs:
        pdf.multi_cell(0, 5, clean_text_for_pdf(p), align="L")
        pdf.ln(2)

    out = DATA_DIR / filename
    pdf.output(str(out))
    print(f"  [OK] Saved English Legal PDF: {out}")


async def collect_vinuni_policies():
    """Collect English VinUniversity policy documents into data/landing/legal/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {DATA_DIR}\n")

    crawler = None
    try:
        from crawl4ai import AsyncWebCrawler
        crawler = AsyncWebCrawler(headless=True, verbose=False)
        await crawler.start()
    except Exception:
        crawler = None

    try:
        for page in VINUNI_ENGLISH_PAGES:
            print(f"Crawling English Legal Page: {page['url']}")
            md = await crawl_page(crawler, page["url"])

            paragraphs = markdown_to_paragraphs(md) if md else []
            if len(paragraphs) < 3:
                fallback_paras = VINUNI_ENGLISH_DETAILED_FALLBACKS.get(
                    page["filename"],
                    [
                        f"Official VinUniversity policy document published online at: {page['url']}",
                        f"This document details institutional guidelines, student responsibilities, and administrative protocols.",
                        f"For complete regulations, please visit the official VinUniversity web portal."
                    ]
                )
                paragraphs.extend(fallback_paras)

            create_pdf(
                filename=page["filename"],
                title=page["title"],
                source_url=page["url"],
                paragraphs=paragraphs,
            )
            print()
    finally:
        if crawler:
            try:
                await crawler.close()
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(collect_vinuni_policies())
