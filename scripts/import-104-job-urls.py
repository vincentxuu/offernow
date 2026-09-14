#!/usr/bin/env python3
"""
Import specific 104 job URLs into scripts/data/jobs.json.

Usage:
    uv run --with playwright --with playwright-stealth python scripts/import-104-job-urls.py \
      https://www.104.com.tw/job/90ngc
    pbpaste | uv run --with playwright --with playwright-stealth python scripts/import-104-job-urls.py
"""

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
JOBS_FILE = DATA_DIR / "jobs.json"
SEED_JOBS_SCRIPT = Path(__file__).parent / "db" / "seed-jobs.py"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"


def clean_str(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in ("None", "nan", "NaN", "null") else text


def parse_job_ids(values):
    text = "\n".join(values) if values else sys.stdin.read()
    return list(dict.fromkeys(re.findall(r"104\.com\.tw/job/([0-9a-z]+)", text)))


def load_seed_jobs_helpers():
    spec = importlib.util.spec_from_file_location("seed_jobs", SEED_JOBS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SEED_JOBS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_companies_name_map(), module.match_stock_id


def parse_date(value):
    value = clean_str(value)
    if re.match(r"^\d{4}/\d{2}/\d{2}$", value):
        return value.replace("/", "-")
    if re.match(r"^\d{8}$", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return value


def fetch_jobs(job_ids):
    stealth = Stealth()
    results = []
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
        page.goto("https://www.104.com.tw/jobs/search/?zone=16", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        print(f"104 title: {page.title()}")

        for job_id in job_ids:
            raw = page.evaluate(
                """async (jobId) => {
                  const resp = await fetch(`/job/ajax/content/${jobId}`, {
                    headers: { Referer: `https://www.104.com.tw/job/${jobId}` },
                  });
                  return JSON.stringify({ status: resp.status, text: await resp.text() });
                }""",
                job_id,
            )
            response = json.loads(raw)
            if response["status"] != 200:
                print(f"skip {job_id}: HTTP {response['status']}")
                continue
            try:
                body = json.loads(response["text"])
            except json.JSONDecodeError:
                print(f"skip {job_id}: non-JSON response")
                continue
            data = body.get("data", {})
            header = data.get("header", {})
            detail = data.get("jobDetail", {})
            results.append(
                {
                    "job_id": job_id,
                    "title": clean_str(header.get("jobName")),
                    "company_name_full": clean_str(header.get("custName")),
                    "location": clean_str(detail.get("addressRegion") or detail.get("addressArea")),
                    "salary_min": detail.get("salaryMin"),
                    "salary_max": detail.get("salaryMax"),
                    "date_posted": parse_date(header.get("appearDate")),
                    "job_url": f"https://www.104.com.tw/job/{job_id}",
                    "source": "104",
                    "description": clean_str(detail.get("jobDescription"))[:500],
                    "job_type": "",
                }
            )
            print(f"{job_id}: {results[-1]['company_name_full']} - {results[-1]['title']}")
            time.sleep(0.5)

        browser.close()
    return results


def match_company(job, companies, alias_name_map, match_stock_id):
    tax_map = {c["tax_id"]: c for c in companies if c.get("tax_id")}
    stock_map = {c["stock_id"]: c for c in companies}
    name_map = {}
    for c in companies:
        full = clean_str(c.get("name"))
        short = clean_str(c.get("short_name"))
        clean = full.replace("股份有限公司", "").replace("有限公司", "").strip()
        for key in (full, short, clean):
            if key:
                name_map[key] = c

    company_full = job["company_name_full"]
    clean = company_full.replace("股份有限公司", "").replace("有限公司", "").strip()
    matched = tax_map.get(job.get("cust_no")) or name_map.get(company_full) or name_map.get(clean)
    stock_id = matched["stock_id"] if matched else match_stock_id(company_full, alias_name_map)
    matched = matched or stock_map.get(stock_id)
    job["stock_id"] = stock_id or f"ext_{clean[:20]}"
    job["company_name"] = (matched.get("short_name") or clean) if matched else clean
    job.pop("company_name_full", None)
    return job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*")
    args = parser.parse_args()
    job_ids = parse_job_ids(args.urls)
    if not job_ids:
        raise SystemExit("No 104 job URLs found")

    alias_name_map, match_stock_id = load_seed_jobs_helpers()
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    imported = [
        match_company(job, companies, alias_name_map, match_stock_id)
        for job in fetch_jobs(job_ids)
        if job["title"] and job["company_name_full"]
    ]

    existing = []
    if JOBS_FILE.exists():
        with open(JOBS_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    by_url = {clean_str(j.get("job_url")): j for j in existing if clean_str(j.get("job_url"))}

    added = 0
    updated = 0
    for job in imported:
        if job["job_url"] in by_url:
            by_url[job["job_url"]].update(job)
            updated += 1
        else:
            existing.append(job)
            by_url[job["job_url"]] = job
            added += 1

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"Imported {len(imported)} jobs: {added} added, {updated} updated")


if __name__ == "__main__":
    main()
