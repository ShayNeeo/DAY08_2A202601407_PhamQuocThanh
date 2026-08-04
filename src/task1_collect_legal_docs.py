"""
Task 1 — Thu thập văn bản chính sách RMIT (Expand All Collapsed Accordions & Sections → Render to PDF).
"""

import asyncio
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


RMIT_LIVE_POLICY_ENDPOINTS = [
    {
        "url": "https://www.rmit.edu.vn/study-at-rmit/tuition-fees",
        "filename": "tuition-fees-rmit.pdf"
    },
    {
        "url": "https://www.rmit.edu.vn/study-at-rmit/scholarships",
        "filename": "academic-achievement-scholarship-rmit.pdf"
    },
    {
        "url": "https://www.rmit.edu.vn/students/my-studies/fees-and-payments",
        "filename": "accommodation-services-rmit.pdf"
    }
]


async def export_expanded_rmit_policies_to_pdf():
    """Mở trang RMIT, tự động mở tất cả accordions/collapsed tabs, và in PDF hoàn chỉnh."""
    setup_directory()
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for item in RMIT_LIVE_POLICY_ENDPOINTS:
            filepath = DATA_DIR / item["filename"]
            print(f"Đang tải, mở rộng tất cả accordions và in PDF từ: {item['url']}")
            try:
                page = await context.new_page()
                await page.goto(item["url"], wait_until="networkidle", timeout=45000)
                await asyncio.sleep(2)

                # Execute JS to expand all accordions, details, and hidden sections
                await page.evaluate("""
                    () => {
                        document.querySelectorAll('details').forEach(d => d.open = true);
                        document.querySelectorAll('[aria-expanded="false"]').forEach(el => el.setAttribute('aria-expanded', 'true'));
                        document.querySelectorAll('.accordion-content, .cmp-accordion__panel, .collapse, .tab-pane').forEach(el => {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                            el.classList.add('is-open', 'in', 'active', 'cmp-accordion__panel--expanded');
                        });
                    }
                """)
                await asyncio.sleep(1)

                # Export to PDF with background styles enabled
                await page.pdf(path=str(filepath), format="A4", print_background=True)
                print(f"  ✓ Đã in PDF mở rộng hoàn chỉnh: {filepath.name} ({filepath.stat().st_size} bytes)")
                await page.close()
            except Exception as e:
                print(f"  ⚠ Lỗi in PDF từ {item['url']}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(export_expanded_rmit_policies_to_pdf())
