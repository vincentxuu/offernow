#!/usr/bin/env python3
"""
用 Playwright 從 104 爬取遠端/遠距工作的上市櫃職缺。
複用 fetch-104-ai-jobs.py 的架構，改關鍵字。

用法：
    python3 scripts/fetch-104-remote-jobs.py
"""

import json
import time
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
JOBS_FILE = DATA_DIR / "jobs.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"

KEYWORDS = ["remote", "遠端", "遠距", "在家工作", "work from home", "居家辦公"]
MAX_PAGES_PER_KEYWORD = 3
PAGE_SIZE = 20


def main():
    print("=" * 60)
    print("OfferNow — Fetching Remote Jobs from 104")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    name_map = {}
    for c in companies:
        name = c["name"]
        short = c.get("short_name", "")
        name_map[name] = c["stock_id"]
        if short:
            name_map[short] = c["stock_id"]
        clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
        name_map[clean] = c["stock_id"]

    all_jobs = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA)
        Stealth().apply_stealth_sync(context)
        page = context.new_page()

        print("Navigating to 104 to get Cloudflare cookies...")
        page.goto("https://www.104.com.tw/jobs/search/?zone=16", wait_until="networkidle", timeout=30000)
        time.sleep(5)
        print("  Ready!")

        for keyword in KEYWORDS:
            print(f"\n--- Searching: {keyword} ---")
            for page_num in range(1, MAX_PAGES_PER_KEYWORD + 1):
                url = f"https://www.104.com.tw/jobs/search/api/jobs?keyword={quote(keyword)}&order=15&pagesize={PAGE_SIZE}&zone=16&page={page_num}"
                try:
                    result = page.evaluate(f"""
                        async () => {{
                            const resp = await fetch("{url}");
                            return await resp.text();
                        }}
                    """)
                    data = json.loads(result) if isinstance(result, str) else result
                    items = data if isinstance(data, list) else []
                    if not items:
                        break

                    for item in items:
                        job_no = item.get("jobNo", "")
                        if not job_no or job_no in all_jobs:
                            continue
                        cust_name = item.get("custName", "")
                        clean_name = cust_name.replace("股份有限公司", "").replace("有限公司", "").strip()
                        stock_id = name_map.get(cust_name) or name_map.get(clean_name)
                        if not stock_id:
                            for name, sid in name_map.items():
                                if len(name) >= 2 and name in cust_name:
                                    stock_id = sid
                                    break

                        appear = item.get("appearDate", "")
                        date_fmt = f"{appear[:4]}-{appear[4:6]}-{appear[6:8]}" if len(appear) == 8 else ""

                        all_jobs[job_no] = {
                            "stock_id": stock_id or f"ext_{cust_name[:20]}",
                            "company_name": cust_name,
                            "title": item.get("jobName", ""),
                            "location": item.get("jobAddrNoDesc", ""),
                            "date_posted": date_fmt,
                            "job_url": (item.get("link", {}).get("job", "") or "").replace("//", "https://", 1) if item.get("link", {}).get("job", "").startswith("//") else item.get("link", {}).get("job", ""),
                            "source": "104",
                            "description": (item.get("description", "") or "")[:500],
                            "salary_min": item.get("salaryLow"),
                            "salary_max": item.get("salaryHigh"),
                            "job_type": "remote",
                        }

                    print(f"  Page {page_num}: {len(items)} jobs")
                except Exception as e:
                    print(f"  Error page {page_num}: {e}")
                    break

                time.sleep(2)
            time.sleep(3)

        browser.close()

    print(f"\nTotal unique remote jobs: {len(all_jobs)}")

    remote_file = DATA_DIR / "104_remote_jobs.json"
    with open(remote_file, "w", encoding="utf-8") as f:
        json.dump(list(all_jobs.values()), f, ensure_ascii=False, indent=2)
    print(f"Saved to {remote_file}")

    # Merge into jobs.json
    with open(JOBS_FILE, encoding="utf-8") as f:
        existing = json.load(f)

    existing_titles = {(j.get("title", ""), j.get("company_name", "")) for j in existing}
    new_count = 0
    for job in all_jobs.values():
        key = (job["title"], job["company_name"])
        if key not in existing_titles:
            existing.append(job)
            existing_titles.add(key)
            new_count += 1

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"Merged: {new_count} new remote jobs, total jobs now: {len(existing)}")
    print("Done!")


if __name__ == "__main__":
    main()
