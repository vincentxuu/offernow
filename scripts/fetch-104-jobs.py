#!/usr/bin/env python3
"""
從 104 薪資 API（已在 companies_with_salary.json 裡由 teardown 驗證過有 jobCount）
取得職缺數。

104 直接 curl 會被 Cloudflare 擋，改用兩種方式：
1. 優先：從 104 薪資排行 API response（teardown 時擷取的）取 jobCount
2. 備用：用已存在的 104_salary_top100 資料（有 exchangeId = stock_id）

用法：
    python3 scripts/fetch-104-jobs.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"

# 104 薪資 API 的 response（我們在 teardown 時已擷取）
SALARY_API_FILE = Path(__file__).parent.parent / ".playwright-mcp" / "104-salary-top100-response.json"
COMPANY_API_FILE = Path(__file__).parent.parent / ".playwright-mcp" / "104-company-list-api-response.json"


def main():
    print("=" * 60)
    print("OfferNow — Merging 104 Job Counts from Teardown Data")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    # Source 1: 104 salary API (has exchangeId = stock_id + jobCount)
    salary_job_map = {}
    if SALARY_API_FILE.exists():
        with open(SALARY_API_FILE, encoding="utf-8") as f:
            salary_data = json.load(f)
        items = salary_data if isinstance(salary_data, list) else salary_data.get("data", [])
        for item in items:
            stock_id = str(item.get("exchangeId", ""))
            job_count = item.get("jobCount", 0)
            encoded_id = item.get("encodedCustNo", "")
            if stock_id:
                salary_job_map[stock_id] = {
                    "job_count": job_count,
                    "encoded_cust_no": encoded_id,
                }
        print(f"Source 1 (salary API): {len(salary_job_map)} companies with job counts")

    # Source 2: 104 company list API (has encodedCustNo + jobCount + name)
    company_name_map = {}
    if COMPANY_API_FILE.exists():
        with open(COMPANY_API_FILE, encoding="utf-8") as f:
            company_data = json.load(f)
        items = company_data.get("data", []) if isinstance(company_data, dict) else company_data
        for item in items:
            name = item.get("name", "")
            job_count = item.get("jobCount", 0)
            encoded_id = item.get("encodedCustNo", "")
            if name:
                clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
                company_name_map[name] = {"job_count": job_count, "encoded_cust_no": encoded_id}
                company_name_map[clean] = {"job_count": job_count, "encoded_cust_no": encoded_id}
        print(f"Source 2 (company API): {len(items)} companies from first page")

    # Merge
    matched = 0
    for company in companies:
        stock_id = company.get("stock_id", "")
        full_name = company.get("name", "")
        clean_name = full_name.replace("股份有限公司", "").replace("有限公司", "").strip()

        # Try salary API first (by stock_id)
        info = salary_job_map.get(stock_id)
        if not info:
            # Try company API (by name)
            info = company_name_map.get(full_name) or company_name_map.get(clean_name)

        if info:
            company["job_count_104"] = info["job_count"]
            company["encoded_cust_no_104"] = info["encoded_cust_no"]
            matched += 1
        else:
            company.setdefault("job_count_104", 0)
            company.setdefault("encoded_cust_no_104", None)

    print(f"\nMatched: {matched}/{len(companies)} companies")

    with_jobs = [c for c in companies if c.get("job_count_104", 0) > 0]
    total_jobs = sum(c.get("job_count_104", 0) for c in companies)
    print(f"Companies with active jobs: {len(with_jobs)}")
    print(f"Total job postings: {total_jobs}")

    top10 = sorted(companies, key=lambda x: x.get("job_count_104", 0), reverse=True)[:10]
    print("\n--- TOP 10 職缺數 ---")
    for i, c in enumerate(top10, 1):
        print(f"  {i}. {c.get('short_name') or c.get('name')} ({c['stock_id']}) — {c.get('job_count_104', 0)} 缺")

    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated {COMPANIES_FILE}")
    print("Done!")


if __name__ == "__main__":
    main()
