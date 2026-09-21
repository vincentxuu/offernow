#!/usr/bin/env python3
"""
Fetch 104 jobs company-first using each company's encoded 104 customer ID.

This is broader than keyword search and catches jobs that are visible on a
company's 104 page but absent from `/jobs/search/api/jobs?keyword=...`.

Usage:
    uv run --with playwright --with playwright-stealth python scripts/fetch-104-company-jobs.py --financial-only
    uv run --with playwright --with playwright-stealth python scripts/fetch-104-company-jobs.py --stock-ids 2885 2891
    uv run --with playwright --with playwright-stealth python scripts/fetch-104-company-jobs.py --limit-companies 20 --max-pages 3
"""

import argparse
import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
COMPANY_ALIASES_FILE = DATA_DIR / "104_company_aliases.json"
JOBS_FILE = DATA_DIR / "jobs.json"
RAW_OUTPUT_FILE = DATA_DIR / "104_company_jobs.json"
SEED_JOBS_SCRIPT = Path(__file__).parent / "db" / "seed-jobs.py"
SEED_JOBS_SQL = Path(__file__).parent / "db" / "seed-jobs.sql"
FIX_JOB_MAPPING_SQL = Path(__file__).parent / "db" / "fix-job-company-mapping.sql"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
PAGE_SIZE = 20
AI_KEYWORDS = [
    "agentic ai",
    "generative ai",
    "人工智慧",
    "機器學習",
    "深度學習",
    "machine learning",
    "deep learning",
    "data scientist",
    "ai engineer",
]
AI_SHORT_TOKENS = ["ai", "gai", "nlp", "llm"]


def clean_str(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in ("None", "nan", "NaN", "null") else text


def parse_date(value):
    value = clean_str(value)
    if re.match(r"^\d{8}$", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    if re.match(r"^\d{4}/\d{2}/\d{2}$", value):
        return value.replace("/", "-")
    return value


def load_seed_jobs_helpers():
    spec = importlib.util.spec_from_file_location("seed_jobs", SEED_JOBS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SEED_JOBS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_companies_name_map(), module.match_stock_id


def select_targets(companies, args):
    targets = [c for c in companies if c.get("encoded_cust_no_104")]
    if args.financial_only:
        targets = [c for c in targets if "金融" in clean_str(c.get("industry"))]
    if args.stock_ids:
        wanted = set(args.stock_ids)
        targets = [c for c in targets if c.get("stock_id") in wanted]
    if args.min_job_count > 0:
        targets = [c for c in targets if (c.get("job_count_104") or 0) >= args.min_job_count]
    targets.sort(key=lambda c: (c.get("job_count_104") or 0), reverse=True)
    if args.limit_companies:
        targets = targets[: args.limit_companies]

    alias_targets = load_company_alias_targets(args)
    manual_targets = []
    for encoded in args.company_ids or []:
        manual_targets.append(
            {
                "stock_id": "",
                "encoded_cust_no_104": encoded,
                "short_name": encoded,
                "name": encoded,
                "job_count_104": 0,
            }
        )
    for url in args.company_urls or []:
        encoded = extract_company_id(url)
        if encoded:
            manual_targets.append(
                {
                    "stock_id": "",
                    "encoded_cust_no_104": encoded,
                    "short_name": encoded,
                    "name": encoded,
                    "job_count_104": 0,
                }
            )

    if manual_targets and not args.financial_only and not args.stock_ids and not args.limit_companies:
        targets = []

    seen = {c.get("encoded_cust_no_104") for c in targets}
    for target in alias_targets + manual_targets:
        encoded = target.get("encoded_cust_no_104")
        if encoded and encoded not in seen:
            targets.append(target)
            seen.add(encoded)
    return targets


def load_company_alias_targets(args):
    if not COMPANY_ALIASES_FILE.exists():
        return []
    with open(COMPANY_ALIASES_FILE, encoding="utf-8") as f:
        aliases = json.load(f)

    targets = []
    wanted_stock_ids = set(args.stock_ids or [])
    for entry in aliases:
        stock_id = clean_str(entry.get("stock_id"))
        if wanted_stock_ids and stock_id not in wanted_stock_ids:
            continue
        if args.financial_only and "金融" not in clean_str(entry.get("industry")):
            continue
        for encoded in entry.get("cust_ids", []):
            encoded = clean_str(encoded)
            if not encoded:
                continue
            targets.append(
                {
                    "stock_id": stock_id,
                    "encoded_cust_no_104": encoded,
                    "short_name": "",
                    "name": clean_str(entry.get("name")) or encoded,
                    "job_count_104": 0,
                }
            )
    return targets


def extract_company_id(url_or_id):
    value = clean_str(url_or_id)
    if not value:
        return ""
    if "/" not in value:
        return value.split("#", 1)[0].split("?", 1)[0]
    parsed = urlparse(value)
    parts = [p for p in parsed.path.split("/") if p]
    if "company" in parts:
        index = parts.index("company")
        if index + 1 < len(parts):
            return parts[index + 1]
    return ""


def normalize_search_job(item, fallback_company, alias_name_map, match_stock_id):
    link = item.get("link", {}) if isinstance(item.get("link"), dict) else {}
    company_name = clean_str(item.get("custName")) or clean_str(fallback_company.get("short_name"))
    stock_id = clean_str(fallback_company.get("stock_id"))
    matched_stock_id = match_stock_id(company_name, alias_name_map)
    if matched_stock_id:
        stock_id = matched_stock_id
    fallback_short_name = clean_str(fallback_company.get("short_name"))
    if fallback_short_name == clean_str(fallback_company.get("encoded_cust_no_104")):
        fallback_short_name = ""

    return {
        "stock_id": stock_id,
        "company_name": fallback_short_name or company_name,
        "title": clean_str(item.get("jobName")),
        "location": clean_str(item.get("jobAddrNoDesc")),
        "date_posted": parse_date(item.get("appearDate")),
        "job_url": clean_str(link.get("job")) or f"https://www.104.com.tw/job/{item.get('jobNo', '')}",
        "source": "104",
        "description": clean_str(item.get("description"))[:500],
        "salary_min": item.get("salaryLow") or None,
        "salary_max": item.get("salaryHigh") or None,
        "job_type": "",
    }


def is_ai_related(item):
    text = " ".join(
        [
            clean_str(item.get("jobName")),
            clean_str(item.get("jobNameSnippet")),
        ]
    ).lower()
    if any(keyword in text for keyword in AI_KEYWORDS):
        return True

    for token in AI_SHORT_TOKENS:
        start = text.find(token)
        while start != -1:
            end = start + len(token)
            before = text[start - 1] if start > 0 else ""
            after = text[end] if end < len(text) else ""
            before_is_ascii_alnum = bool(before) and before.isascii() and before.isalnum()
            after_is_ascii_alnum = bool(after) and after.isascii() and after.isalnum()
            if not before_is_ascii_alnum and not after_is_ascii_alnum:
                return True
            start = text.find(token, start + 1)

    return False


def fetch_company_jobs(page, company, max_pages, sleep_seconds):
    encoded = company["encoded_cust_no_104"]
    rows = []
    seen_job_nos = set()
    for page_num in range(1, max_pages + 1):
        raw = page.evaluate(
            """async ({ encoded, pageNum, pageSize }) => {
              const resp = await fetch(`/jobs/search/api/jobs?custNo=${encoded}&order=15&pagesize=${pageSize}&page=${pageNum}`);
              return JSON.stringify({ status: resp.status, text: await resp.text() });
            }""",
            {"encoded": encoded, "pageNum": page_num, "pageSize": PAGE_SIZE},
        )
        response = json.loads(raw)
        if response["status"] != 200:
            print(f"  page {page_num}: HTTP {response['status']}")
            break
        try:
            result = json.loads(response["text"])
        except json.JSONDecodeError:
            print(f"  page {page_num}: non-JSON response ({response['text'][:120]})")
            break

        items = result.get("data", result.get("list", [])) if isinstance(result, dict) else result
        if isinstance(items, dict):
            items = items.get("list", [])
        if not items:
            break

        new_items = 0
        for item in items:
            job_no = clean_str(item.get("jobNo"))
            if not job_no or job_no in seen_job_nos:
                continue
            seen_job_nos.add(job_no)
            rows.append(item)
            new_items += 1
        print(f"  page {page_num}: {len(items)} rows, {new_items} new")
        if len(items) < PAGE_SIZE:
            break
        if new_items == 0:
            break
        time.sleep(sleep_seconds)
    return rows


def merge_jobs(imported):
    existing = []
    if JOBS_FILE.exists():
        with open(JOBS_FILE, encoding="utf-8") as f:
            existing = json.load(f)

    by_url = {clean_str(j.get("job_url")): j for j in existing if clean_str(j.get("job_url"))}
    added = 0
    updated = 0
    for job in imported:
        url = clean_str(job.get("job_url"))
        if not url or not job.get("title"):
            continue
        if url in by_url:
            by_url[url].update(job)
            updated += 1
        else:
            existing.append(job)
            by_url[url] = job
            added += 1

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return added, updated, len(existing)


def run_pipeline(skip_d1, skip_deploy):
    subprocess.run(["python3", str(SEED_JOBS_SCRIPT)], check=True)
    if skip_d1:
        return
    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", str(SEED_JOBS_SQL)], check=True)
    subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--remote", "--file", str(SEED_JOBS_SQL)], check=True)
    if FIX_JOB_MAPPING_SQL.exists():
        subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--local", "--file", str(FIX_JOB_MAPPING_SQL)], check=True)
        subprocess.run(["pnpm", "wrangler", "d1", "execute", "offernow-db", "--remote", "--file", str(FIX_JOB_MAPPING_SQL)], check=True)
    if not skip_deploy:
        subprocess.run(["pnpm", "run", "deploy"], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--financial-only", action="store_true")
    parser.add_argument("--stock-ids", nargs="*")
    parser.add_argument("--company-ids", nargs="*")
    parser.add_argument("--company-urls", nargs="*")
    parser.add_argument("--limit-companies", type=int)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--min-job-count", type=int, default=1)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--ai-only", action="store_true")
    parser.add_argument("--skip-d1", action="store_true")
    parser.add_argument("--skip-deploy", action="store_true")
    args = parser.parse_args()

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)
    targets = select_targets(companies, args)
    if not targets:
        raise SystemExit("No companies matched the requested filters")

    alias_name_map, match_stock_id = load_seed_jobs_helpers()
    raw_records = []
    normalized = []
    stealth = Stealth()

    print(f"Fetching 104 company jobs for {len(targets)} companies")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 720}, locale="zh-TW")
        stealth.apply_stealth_sync(context)
        page = context.new_page()
        page.goto("https://www.104.com.tw/company/search/?zone=16", wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        print(f"104 title: {page.title()}")

        for index, company in enumerate(targets, 1):
            label = company.get("short_name") or company.get("name")
            print(f"\n[{index}/{len(targets)}] {label} ({company['stock_id']}, {company['encoded_cust_no_104']})")
            items = fetch_company_jobs(page, company, args.max_pages, args.sleep_seconds)
            if args.ai_only:
                before = len(items)
                items = [item for item in items if is_ai_related(item)]
                print(f"  AI filter: {before} -> {len(items)}")
            raw_records.extend(
                {
                    "stock_id": company["stock_id"],
                    "encoded_cust_no_104": company["encoded_cust_no_104"],
                    "short_name": company.get("short_name"),
                    "item": item,
                }
                for item in items
            )
            normalized.extend(normalize_search_job(item, company, alias_name_map, match_stock_id) for item in items)
            print(f"  total imported for company: {len(items)}")
            time.sleep(args.sleep_seconds)

        browser.close()

    with open(RAW_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_records, f, ensure_ascii=False, indent=2)
    added, updated, total = merge_jobs(normalized)
    print(f"\nMerged {len(normalized)} jobs: {added} added, {updated} updated, {total} total")
    run_pipeline(args.skip_d1, args.skip_deploy)
    print("Done")


if __name__ == "__main__":
    main()
