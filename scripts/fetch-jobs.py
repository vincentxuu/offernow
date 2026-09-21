#!/usr/bin/env python3
"""
用 JobSpy 抓取 TOP 50 上市櫃公司的真實職缺（LinkedIn + Indeed）。

用法：
    python3 scripts/fetch-jobs.py
"""

import json
import time
from pathlib import Path
from jobspy import scrape_jobs

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
JOBS_FILE = DATA_DIR / "jobs.json"
TOP_N = 100

# 公司名 → 英文搜尋名（LinkedIn 英文搜比較準）
NAME_MAP = {
    "台積電": "TSMC",
    "聯發科": "MediaTek",
    "鴻海": "Foxconn",
    "台達電": "Delta Electronics",
    "華碩": "ASUS",
    "瑞昱": "Realtek",
    "廣達": "Quanta Computer",
    "聯詠": "Novatek",
    "日月光投控": "ASE Group",
    "信驊": "Aspeed Technology",
    "祥碩": "ASMedia",
    "群聯": "Phison",
    "元大金": "Yuanta Financial",
    "國泰金": "Cathay Financial",
    "富邦金": "Fubon Financial",
    "中信金": "CTBC Financial",
    "智邦": "Accton Technology",
    "矽力-KY": "Silergy",
    "力旺": "eMemory",
    "原相": "PixArt",
    "世芯-KY": "Alchip",
    "創意": "GUC",
    "譜瑞-KY": "Parade Technologies",
    "M31": "M31 Technology",
    "晶心科": "Andes Technology",
    "神盾": "Egis Technology",
    "緯穎": "Wiwynn",
    "緯創": "Wistron",
    "仁寶": "Compal Electronics",
    "英業達": "Inventec",
}


def main():
    print("=" * 60)
    print("OfferNow — Fetching Real Jobs via JobSpy")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    top = sorted(
        [c for c in companies if c.get("salary_median_k")],
        key=lambda x: x["salary_median_k"],
        reverse=True,
    )[:TOP_N]

    all_jobs = []

    for i, company in enumerate(top):
        short_name = company.get("short_name") or company.get("name", "")
        search_name = NAME_MAP.get(short_name, short_name)
        stock_id = company["stock_id"]

        print(f"\n[{i+1}/{len(top)}] {short_name} ({stock_id}) → searching '{search_name}'...")

        try:
            results = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=search_name,
                location="Taiwan",
                results_wanted=20,
                hours_old=720,  # 30 days
                country_indeed="Taiwan",
            )

            for _, row in results.iterrows():
                listed_company = str(row.get("company", ""))
                is_match = (
                    short_name.lower() in listed_company.lower()
                    or search_name.lower() in listed_company.lower()
                    or listed_company.lower() in short_name.lower()
                )
                job = {
                    "stock_id": stock_id if is_match else "",
                    "company_name": listed_company or short_name,
                    "company_search": search_name,
                    "title": str(row.get("title", "")),
                    "company_listed": listed_company,
                    "location": str(row.get("location", "")),
                    "date_posted": str(row.get("date_posted", "")),
                    "job_url": str(row.get("job_url", "")),
                    "source": str(row.get("site", "")),
                    "description": str(row.get("description", ""))[:500],
                    "salary_min": row.get("min_amount") if row.get("min_amount") else None,
                    "salary_max": row.get("max_amount") if row.get("max_amount") else None,
                    "job_type": str(row.get("job_type", "")),
                }
                all_jobs.append(job)

            print(f"  → {len(results)} jobs found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        time.sleep(3)

    print(f"\n{'=' * 60}")
    print(f"Total jobs fetched: {len(all_jobs)}")

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    print(f"Saved to {JOBS_FILE}")

    # Stats
    by_company = {}
    for j in all_jobs:
        by_company.setdefault(j["stock_id"], []).append(j)

    print(f"\nCompanies with jobs: {len(by_company)}")
    for sid, jobs in sorted(by_company.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        name = jobs[0]["company_name"]
        print(f"  {name} ({sid}): {len(jobs)} jobs")

    print("\nDone!")


if __name__ == "__main__":
    main()
