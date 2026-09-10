#!/usr/bin/env python3
"""
用 Playwright 繞過 104 Cloudflare 防護，在瀏覽器內攔截 API response。

策略：不用 cookies + requests，直接在瀏覽器裡觸發 API 並攔截 response。

用法：
    python3 scripts/fetch-104-playwright.py
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"


def main():
    print("=" * 60)
    print("OfferNow — Fetching 104 Data via Playwright (in-browser)")
    print("=" * 60)

    stealth = Stealth()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 720},
            locale="zh-TW",
        )
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        # Step 1: Navigate and pass Cloudflare
        print("\n1. Passing Cloudflare...")
        page.goto("https://www.104.com.tw/company/search/?zone=16", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        print(f"   Title: {page.title()}")

        if "moment" in page.title().lower() or not page.title():
            print("   Still on challenge, waiting longer...")
            time.sleep(15)
            print(f"   Title: {page.title()}")

        # Step 2: Fetch company list by intercepting in-browser fetch
        print("\n2. Fetching company list (in-browser)...")
        all_companies = []
        page_num = 1
        last_page = 72  # 1280 / 18 = ~72 pages, but we use pageSize=100

        while page_num <= 70:  # ~1280/20 = 64 pages
            print(f"   Page {page_num}...", end=" ", flush=True)
            try:
                raw_text = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch('/company/ajax/list?zone=16&features=1&pageSize=20&page={page_num}');
                        return await resp.text();
                    }}
                """)
                if not raw_text:
                    print("empty response")
                    break
                result = json.loads(raw_text)

                items = result.get("data", [])
                pagination = result.get("metadata", {}).get("pagination", {})
                if page_num == 1:
                    print(f"[debug] raw_len={len(raw_text)}, items={len(items)}, keys={list(result.keys())}", end=" ")
                total = pagination.get("total", 0)
                last_page_actual = pagination.get("lastPage", 1)

                for item in items:
                    all_companies.append({
                        "encoded_cust_no": item.get("encodedCustNo", ""),
                        "name": item.get("name", ""),
                        "job_count": item.get("jobCount", 0),
                        "industry_desc": item.get("industryDesc", ""),
                        "area_desc": item.get("areaDesc", ""),
                        "main_score": item.get("mainScore", 0),
                    })

                print(f"{len(items)} companies (total: {total})")

                if page_num >= last_page_actual:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

            page_num += 1
            time.sleep(1.5)

        print(f"\n   Total companies from 104: {len(all_companies)}")

        # Step 3: Fetch job listings
        print("\n3. Fetching job listings (in-browser)...")
        all_jobs = []
        job_page = 1

        while job_page <= 80:
            print(f"   Job page {job_page}...", end=" ", flush=True)
            try:
                raw_text = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch('/jobs/search/api/jobs?keyword=engineer&order=15&pagesize=20&zone=16&page={job_page}');
                        return await resp.text();
                    }}
                """)
                result = json.loads(raw_text)

                # Parse response
                if isinstance(result, list):
                    items = result
                elif isinstance(result, dict):
                    items = result.get("data", result.get("list", []))
                    if isinstance(items, dict):
                        items = items.get("list", [])
                else:
                    items = []

                if not items:
                    print("no more results")
                    break

                for item in items:
                    link = item.get("link", {})
                    all_jobs.append({
                        "job_no": item.get("jobNo", ""),
                        "title": item.get("jobName", ""),
                        "company_name_full": item.get("custName", ""),
                        "cust_no": item.get("custNo", ""),
                        "location": item.get("jobAddrNoDesc", ""),
                        "salary_low": item.get("salaryLow", 0),
                        "salary_high": item.get("salaryHigh", 0),
                        "appear_date": item.get("appearDate", ""),
                        "description": (item.get("description") or "")[:500],
                        "employee_count": item.get("employeeCount"),
                        "job_url": link.get("job", ""),
                    })

                print(f"{len(items)} jobs (total: {len(all_jobs)})")

                if len(items) < 20:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

            job_page += 1
            time.sleep(1.5)

        print(f"\n   Total jobs from 104: {len(all_jobs)}")

        browser.close()

    # Step 4: Save and merge
    if all_companies:
        backup = DATA_DIR / "104_companies_full.json"
        with open(backup, "w", encoding="utf-8") as f:
            json.dump(all_companies, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(all_companies)} companies to {backup}")

        # Match and update companies_with_salary.json
        with open(COMPANIES_FILE, encoding="utf-8") as f:
            companies = json.load(f)

        name_map = {}
        for c in all_companies:
            name = c["name"]
            clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
            name_map[name] = c
            name_map[clean] = c

        matched = 0
        for company in companies:
            full_name = company.get("name", "")
            clean_name = full_name.replace("股份有限公司", "").replace("有限公司", "").strip()
            c104 = name_map.get(full_name) or name_map.get(clean_name)
            if c104:
                company["job_count_104"] = c104["job_count"]
                company["encoded_cust_no_104"] = c104["encoded_cust_no"]
                matched += 1

        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)

        with_jobs = sum(1 for c in all_companies if c["job_count"] > 0)
        total_jobs = sum(c["job_count"] for c in all_companies)
        print(f"Matched: {matched} companies, {with_jobs} with jobs, {total_jobs} total postings")

        top10 = sorted(all_companies, key=lambda x: x["job_count"], reverse=True)[:10]
        print("\n--- TOP 10 職缺數 ---")
        for i, c in enumerate(top10, 1):
            print(f"  {i}. {c['name'][:20]} — {c['job_count']} 缺")

    if all_jobs:
        raw_backup = DATA_DIR / "104_jobs.json"
        with open(raw_backup, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(all_jobs)} raw jobs to {raw_backup}")

        # Convert to OfferNow schema and merge
        with open(COMPANIES_FILE, encoding="utf-8") as f:
            companies = json.load(f)
        tax_map = {c["tax_id"]: c for c in companies if c.get("tax_id")}
        name_map2 = {}
        for c in companies:
            full = c.get("name", "")
            clean = full.replace("股份有限公司", "").replace("有限公司", "").strip()
            name_map2[full] = c
            name_map2[clean] = c

        converted = []
        for j in all_jobs:
            cust_no = j.get("cust_no", "")
            company_full = j.get("company_name_full", "")
            clean = company_full.replace("股份有限公司", "").replace("有限公司", "").strip()
            matched_c = tax_map.get(cust_no) or name_map2.get(company_full) or name_map2.get(clean)
            stock_id = matched_c["stock_id"] if matched_c else ""
            short = (matched_c.get("short_name") or clean) if matched_c else clean

            appear = j.get("appear_date", "")
            date_posted = f"{appear[:4]}-{appear[4:6]}-{appear[6:]}" if len(appear) == 8 else appear

            converted.append({
                "stock_id": stock_id,
                "company_name": short,
                "title": j.get("title", ""),
                "location": j.get("location", ""),
                "date_posted": date_posted,
                "job_url": j.get("job_url", ""),
                "source": "104",
                "description": j.get("description", "")[:500],
                "salary_min": j.get("salary_low") if j.get("salary_low") else None,
                "salary_max": j.get("salary_high") if j.get("salary_high") else None,
                "job_type": "",
            })

        # Merge with existing jobs
        jobs_file = DATA_DIR / "jobs.json"
        existing = []
        if jobs_file.exists():
            with open(jobs_file, encoding="utf-8") as f:
                existing = json.load(f)
            existing = [j for j in existing if j.get("source") != "104"]

        merged = existing + converted
        with open(jobs_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"Jobs merged: {len(existing)} existing + {len(converted)} 104 = {len(merged)} total")

    # Re-seed D1
    print("\n--- Re-seeding D1 ---")
    import subprocess
    subprocess.run(["python3", "scripts/db/seed.py"], check=True)
    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", "scripts/db/seed.sql"],
                   check=True, capture_output=True)
    print("Local D1 updated")
    print("\nDone!")


if __name__ == "__main__":
    main()
