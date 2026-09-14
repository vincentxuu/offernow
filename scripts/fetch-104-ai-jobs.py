#!/usr/bin/env python3
"""
用 Playwright 從 104 爬取 AI 相關的上市櫃職缺。

搜尋關鍵字：AI, 人工智慧, machine learning, deep learning, NLP, LLM, data scientist
每個關鍵字最多 5 頁（100 筆），zone=16（上市櫃）。

用法：
    python3 scripts/fetch-104-ai-jobs.py
"""

import json
import importlib.util
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
JOBS_FILE = DATA_DIR / "jobs.json"
SEED_JOBS_SCRIPT = Path(__file__).parent / "db" / "seed-jobs.py"
SEED_JOBS_SQL = Path(__file__).parent / "db" / "seed-jobs.sql"
FIX_JOB_MAPPING_SQL = Path(__file__).parent / "db" / "fix-job-company-mapping.sql"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"

KEYWORDS = ["AI", "人工智慧", "machine learning", "deep learning", "NLP", "LLM", "data scientist"]
MAX_PAGES_PER_KEYWORD = 5
PAGE_SIZE = 20


def load_seed_jobs_helpers():
    spec = importlib.util.spec_from_file_location("seed_jobs", SEED_JOBS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SEED_JOBS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_companies_name_map(), module.match_stock_id


def main():
    print("=" * 60)
    print("OfferNow — Fetching AI Jobs from 104 via Playwright")
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

        # Pass Cloudflare
        print("\n1. Passing Cloudflare...")
        page.goto("https://www.104.com.tw/jobs/search/?zone=16", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        print(f"   Title: {page.title()}")

        if "moment" in page.title().lower() or not page.title():
            print("   Still on challenge, waiting longer...")
            time.sleep(15)
            print(f"   Title: {page.title()}")

        # Fetch AI jobs for each keyword
        print("\n2. Fetching AI jobs...")
        all_raw_jobs = []
        seen_job_nos = set()

        for kw_idx, keyword in enumerate(KEYWORDS):
            encoded_kw = quote(keyword)
            print(f"\n   [{kw_idx+1}/{len(KEYWORDS)}] Keyword: '{keyword}'")

            for page_num in range(1, MAX_PAGES_PER_KEYWORD + 1):
                print(f"     Page {page_num}...", end=" ", flush=True)
                try:
                    raw_text = page.evaluate(f"""
                        async () => {{
                            const resp = await fetch('/jobs/search/api/jobs?keyword={encoded_kw}&order=15&pagesize={PAGE_SIZE}&zone=16&page={page_num}');
                            return await resp.text();
                        }}
                    """)
                    result = json.loads(raw_text)

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

                    new_count = 0
                    for item in items:
                        job_no = item.get("jobNo", "")
                        if job_no in seen_job_nos:
                            continue
                        seen_job_nos.add(job_no)
                        new_count += 1

                        link = item.get("link", {})
                        all_raw_jobs.append({
                            "job_no": job_no,
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
                            "keyword": keyword,
                        })

                    print(f"{len(items)} results, {new_count} new (total unique: {len(all_raw_jobs)})")

                    if len(items) < PAGE_SIZE:
                        break
                except Exception as e:
                    print(f"Error: {e}")
                    break

                time.sleep(2)

            time.sleep(5)

        print(f"\n   Total unique AI jobs: {len(all_raw_jobs)}")
        browser.close()

    # Save raw backup
    backup_file = DATA_DIR / "104_ai_jobs.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(all_raw_jobs, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_raw_jobs)} raw AI jobs to {backup_file}")

    # Convert to OfferNow Job schema
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    alias_name_map, match_stock_id = load_seed_jobs_helpers()
    tax_map = {c["tax_id"]: c for c in companies if c.get("tax_id")}
    stock_map = {c["stock_id"]: c for c in companies}
    name_map = {}
    for c in companies:
        full = c.get("name", "")
        clean = full.replace("股份有限公司", "").replace("有限公司", "").strip()
        name_map[full] = c
        name_map[clean] = c

    converted = []
    for j in all_raw_jobs:
        cust_no = j.get("cust_no", "")
        company_full = j.get("company_name_full", "")
        clean = company_full.replace("股份有限公司", "").replace("有限公司", "").strip()
        matched_c = tax_map.get(cust_no) or name_map.get(company_full) or name_map.get(clean)
        stock_id = matched_c["stock_id"] if matched_c else match_stock_id(company_full, alias_name_map)
        matched_c = matched_c or stock_map.get(stock_id)
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

    # Merge with existing jobs (dedupe by title + company)
    existing = []
    if JOBS_FILE.exists():
        with open(JOBS_FILE, encoding="utf-8") as f:
            existing = json.load(f)

    existing_keys = set()
    for j in existing:
        key = f"{j.get('title', '')}|{j.get('company_name', '')}|{j.get('source', '')}"
        existing_keys.add(key)

    added = 0
    for j in converted:
        key = f"{j['title']}|{j['company_name']}|{j['source']}"
        if key not in existing_keys:
            existing.append(j)
            existing_keys.add(key)
            added += 1

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"\nMerged: {added} new AI jobs added, total jobs now: {len(existing)}")

    # Stats
    ai_jobs = [j for j in existing if any(kw.lower() in j.get("title", "").lower() for kw in ["ai", "人工智慧", "machine learning", "deep learning", "nlp", "llm", "data scien"])]
    print(f"Jobs with AI-related titles: {len(ai_jobs)}")

    # Re-seed D1
    print("\n--- Re-seeding D1 ---")
    subprocess.run(["python3", str(SEED_JOBS_SCRIPT)], check=True)
    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", str(SEED_JOBS_SQL)],
                   check=True, capture_output=True)
    print("Local D1 updated")

    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--remote", "--file", str(SEED_JOBS_SQL)],
                   check=True, capture_output=True)
    print("Remote D1 jobs updated")

    if FIX_JOB_MAPPING_SQL.exists():
        subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", str(FIX_JOB_MAPPING_SQL)],
                       check=True, capture_output=True)
        subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--remote", "--file", str(FIX_JOB_MAPPING_SQL)],
                   check=True, capture_output=True)
        print("Financial company mappings fixed")

    # Deploy
    print("\n--- Deploying ---")
    subprocess.run(["pnpm", "run", "deploy"], check=True, capture_output=True)
    print("Deployed!")

    print("\nDone!")


if __name__ == "__main__":
    main()
