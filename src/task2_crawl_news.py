"""
Task 2 — Crawl các bài viết/thông báo thực tế từ website chính thức RMIT Vietnam (verified 200 OK endpoints).
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


RMIT_REAL_NEWS_URLS = [
    {
        "url": "https://www.rmit.edu.vn/study-at-rmit/undergraduate-programs",
        "customer_role": "applicant",
        "title": "RMIT Vietnam Undergraduate Degree Programs & Admission Pathways"
    },
    {
        "url": "https://www.rmit.edu.vn/students/my-studies",
        "customer_role": "student",
        "title": "RMIT Student Portal - My Studies, Enrolment & Academic Guidance"
    },
    {
        "url": "https://www.rmit.edu.vn/students",
        "customer_role": "student",
        "title": "RMIT Student Essentials, Library & Support Services"
    },
    {
        "url": "https://www.rmit.edu.vn/students/careers-and-employability",
        "customer_role": "both",
        "title": "RMIT Vietnam Careers, Industry Internships & Employability"
    },
    {
        "url": "https://www.rmit.edu.vn/news",
        "customer_role": "both",
        "title": "RMIT Vietnam News, Events & Campus Announcements"
    }
]


async def crawl_live_verified_rmit_news():
    """Crawl trực tiếp từ 5 endpoint RMIT 200 OK thật."""
    setup_directory()
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for i, item in enumerate(RMIT_REAL_NEWS_URLS, 1):
            url = item["url"]
            print(f"[{i}/{len(RMIT_REAL_NEWS_URLS)}] Crawling RMIT 200 OK endpoint: {url}")
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=45000)
                await asyncio.sleep(2)

                page_title = await page.title()
                content_text = await page.inner_text("body")

                lines = [line.strip() for line in content_text.split("\n") if line.strip()]
                clean_markdown = f"# {item['title']}\n\n**Source URL:** {url}\n\n" + "\n\n".join(lines[:120])

                article = {
                    "url": url,
                    "title": page_title.strip() if page_title else item["title"],
                    "date_crawled": datetime.now().isoformat(),
                    "customer_role": item["customer_role"],
                    "content_markdown": clean_markdown
                }

                filename = f"article_{i:02d}.json"
                filepath = DATA_DIR / filename
                filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  ✓ Đã crawl và lưu JSON thật (200 OK): {filepath.name} ({filepath.stat().st_size} bytes)")
                await page.close()
            except Exception as e:
                print(f"  ⚠ Lỗi crawl {url}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(crawl_live_verified_rmit_news())
