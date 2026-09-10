#!/usr/bin/env python3
"""
用 Playwright 繞過 104 Cloudflare 防護，抓取全部上市櫃公司職缺數 + 職缺列表。

流程：
1. Playwright 開 Chrome 通過 Cloudflare challenge
2. 拿 cookie，用 requests 打 API
3. /company/ajax/list?zone=16 → 公司列表 + jobCount
4. /jobs/search/api/jobs?zone=16 → 職缺列表

用法：
    python3 scripts/fetch-104-playwright.py
"""

import json
import time
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"


def get_cookies_via_playwright() -> tuple[str, dict]:
    """Open 104 in Playwright, pass Cloudflare, return cookie string and headers."""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    print("Opening 104 via Playwright (with stealth)...")
    stealth = Stealth()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 720},
            locale="zh-TW",
        )
        stealth.apply_stealth_sync(context)
        page = context.new_page()

        page.goto("https://www.104.com.tw/company/search/?zone=16", wait_until="domcontentloaded", timeout=60000)
        print("  Waiting for Cloudflare challenge...")
        time.sleep(10)

        # Wait until the page has actual content (not challenge page)
        for attempt in range(6):
            title = page.title()
            if title and "moment" not in title.lower() and "just" not in title.lower():
                break
            print(f"  Still on challenge (attempt {attempt+1}), waiting...")
            time.sleep(5)

        # Check if we passed
        title = page.title()
        print(f"  Page title: {title}")

        cookies = context.cookies()
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        browser.close()

    headers = {
        "Cookie": cookie_str,
        "User-Agent": UA,
        "Referer": "https://www.104.com.tw/company/search/?zone=16",
        "Accept": "application/json, text/plain, */*",
    }

    print(f"  Got {len(cookies)} cookies")
    return cookie_str, headers


def fetch_company_list(headers: dict) -> list[dict]:
    """Fetch all listed companies from 104 company API."""
    import urllib.request

    all_companies = []
    page = 1

    while True:
        url = f"https://www.104.com.tw/company/ajax/list?zone=16&features=1&pageSize=100&page={page}"
        req = urllib.request.Request(url, headers=headers)

        print(f"  Company list page {page}...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"Error: {e}")
            if page == 1:
                print("  ⚠️ Cloudflare still blocking. Falling back to teardown data.")
                return []
            break

        items = data.get("data", [])
        pagination = data.get("metadata", {}).get("pagination", {})
        total = pagination.get("total", 0)
        last_page = pagination.get("lastPage", 1)

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

        if page >= last_page:
            break
        page += 1
        time.sleep(2)

    return all_companies


def fetch_job_listings(headers: dict, max_pages: int = 80) -> list[dict]:
    """Fetch job listings from 104 job search API (zone=16)."""
    import urllib.request

    all_jobs = []
    page = 1

    while page <= max_pages:
        url = f"https://www.104.com.tw/jobs/search/api/jobs?keyword=&order=15&pagesize=100&zone=16&page={page}"
        req = urllib.request.Request(url, headers=headers)

        print(f"  Job listings page {page}...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                data = json.loads(raw)
        except Exception as e:
            print(f"Error: {e}")
            if page == 1:
                print("  ⚠️ Job search API blocked. Skipping.")
                return []
            break

        # Response can be a list or dict with data key
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data", data.get("list", []))
            if isinstance(items, dict):
                items = items.get("list", [])
        else:
            items = []

        if not items:
            print("no more results")
            break

        for item in items:
            link = item.get("link", {})
            tags = item.get("tags", {})
            all_jobs.append({
                "job_no": item.get("jobNo", ""),
                "title": item.get("jobName", ""),
                "company_name_full": item.get("custName", ""),
                "cust_no": item.get("custNo", ""),
                "location": item.get("jobAddrNoDesc", ""),
                "address": item.get("jobAddress", ""),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "salary_low": item.get("salaryLow", 0),
                "salary_high": item.get("salaryHigh", 0),
                "appear_date": item.get("appearDate", ""),
                "description": (item.get("description") or "")[:500],
                "employee_count": item.get("employeeCount"),
                "job_url": link.get("job", ""),
                "company_url": link.get("cust", ""),
                "zone": tags.get("zone", {}).get("desc", ""),
            })

        print(f"{len(items)} jobs (total so far: {len(all_jobs)})")

        if len(items) < 100:
            break
        page += 1
        time.sleep(2)

    return all_jobs


def match_and_update_companies(companies_104: list[dict]) -> int:
    """Match 104 companies to our stock_id and update companies_with_salary.json."""
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    # Build name → 104 data map
    name_map = {}
    for c in companies_104:
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

    return matched


def convert_104_jobs_to_schema(jobs_104: list[dict]) -> list[dict]:
    """Convert 104 job listings to OfferNow Job schema."""
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    # Build tax_id → stock_id map
    tax_map = {}
    name_map = {}
    for c in companies:
        if c.get("tax_id"):
            tax_map[c["tax_id"]] = c
        full = c.get("name", "")
        clean = full.replace("股份有限公司", "").replace("有限公司", "").strip()
        name_map[full] = c
        name_map[clean] = c

    converted = []
    for j in jobs_104:
        cust_no = j.get("cust_no", "")
        company_name_full = j.get("company_name_full", "")
        clean_name = company_name_full.replace("股份有限公司", "").replace("有限公司", "").strip()

        # Match by tax_id (custNo) or name
        matched = tax_map.get(cust_no) or name_map.get(company_name_full) or name_map.get(clean_name)
        stock_id = matched["stock_id"] if matched else ""
        short_name = (matched.get("short_name") or clean_name) if matched else clean_name

        # Format date: 20260908 → 2026-09-08
        appear = j.get("appear_date", "")
        date_posted = f"{appear[:4]}-{appear[4:6]}-{appear[6:]}" if len(appear) == 8 else appear

        converted.append({
            "stock_id": stock_id,
            "company_name": short_name,
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

    return converted


def main():
    print("=" * 60)
    print("OfferNow — Fetching 104 Data via Playwright")
    print("=" * 60)

    # Step 1: Get cookies
    try:
        cookie_str, headers = get_cookies_via_playwright()
    except Exception as e:
        print(f"Playwright failed: {e}")
        print("Using fallback data from teardown.")
        return

    # Step 2: Fetch company list
    print("\n--- Fetching Company List ---")
    companies_104 = fetch_company_list(headers)

    if companies_104:
        # Save backup
        backup = DATA_DIR / "104_companies_full.json"
        with open(backup, "w", encoding="utf-8") as f:
            json.dump(companies_104, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(companies_104)} companies to {backup}")

        # Match and update
        matched = match_and_update_companies(companies_104)
        total_jobs = sum(c["job_count"] for c in companies_104)
        with_jobs = sum(1 for c in companies_104 if c["job_count"] > 0)
        print(f"\nMatched: {matched} companies")
        print(f"With active jobs: {with_jobs}")
        print(f"Total job postings: {total_jobs}")
    else:
        print("Company list fetch failed, skipping.")

    # Step 3: Fetch job listings
    print("\n--- Fetching Job Listings ---")
    jobs_104 = fetch_job_listings(headers)

    if jobs_104:
        # Save raw backup
        raw_backup = DATA_DIR / "104_jobs.json"
        with open(raw_backup, "w", encoding="utf-8") as f:
            json.dump(jobs_104, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(jobs_104)} raw job listings to {raw_backup}")

        # Convert and merge with existing jobs
        converted = convert_104_jobs_to_schema(jobs_104)
        print(f"Converted {len(converted)} jobs to OfferNow schema")

        # Load existing jobs (LinkedIn/Indeed)
        jobs_file = DATA_DIR / "jobs.json"
        existing = []
        if jobs_file.exists():
            with open(jobs_file, encoding="utf-8") as f:
                existing = json.load(f)
            # Remove old 104 jobs
            existing = [j for j in existing if j.get("source") != "104"]

        merged = existing + converted
        with open(jobs_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"Merged: {len(existing)} existing + {len(converted)} 104 = {len(merged)} total jobs")
    else:
        print("Job listings fetch failed, skipping.")

    # Step 4: Re-seed D1
    print("\n--- Re-seeding D1 ---")
    import subprocess
    subprocess.run(["python3", "scripts/db/seed.py"], check=True)
    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", "scripts/db/seed.sql"], check=True, capture_output=True)
    print("Local D1 updated")

    # Top 10
    if companies_104:
        top10 = sorted(companies_104, key=lambda x: x["job_count"], reverse=True)[:10]
        print("\n--- TOP 10 職缺數 ---")
        for i, c in enumerate(top10, 1):
            print(f"  {i}. {c['name'][:20]} — {c['job_count']} 缺")

    print("\nDone!")


if __name__ == "__main__":
    main()
