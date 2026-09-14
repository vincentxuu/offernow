#!/usr/bin/env python3
"""
Audit local job data before seeding/deploying.

Checks:
- regression job URLs exist and map to expected stock IDs
- 104 company alias cust IDs are represented in local jobs
- one company name is not split across multiple stock IDs
- company-first raw output does not contain non-title-AI jobs when present
"""

import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
JOBS_FILE = DATA_DIR / "jobs.json"
COMPANY_ALIASES_FILE = DATA_DIR / "104_company_aliases.json"
REGRESSIONS_FILE = DATA_DIR / "job_quality_regressions.json"
RAW_COMPANY_JOBS_FILE = DATA_DIR / "104_company_jobs.json"
SEED_JOBS_SCRIPT = Path(__file__).parent / "db" / "seed-jobs.py"

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


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_seed_helpers():
    spec = importlib.util.spec_from_file_location("seed_jobs", SEED_JOBS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SEED_JOBS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_companies_name_map(), module.match_stock_id


def is_ascii_alnum(value):
    return bool(value) and value.isascii() and value.isalnum()


def is_title_ai_related(title):
    text = clean_str(title).lower()
    if any(keyword in text for keyword in AI_KEYWORDS):
        return True
    for token in AI_SHORT_TOKENS:
        start = text.find(token)
        while start != -1:
            end = start + len(token)
            before = text[start - 1] if start > 0 else ""
            after = text[end] if end < len(text) else ""
            if not is_ascii_alnum(before) and not is_ascii_alnum(after):
                return True
            start = text.find(token, start + 1)
    return False


def normalize_company_name(name):
    name = clean_str(name)
    for suffix in ("股份有限公司", "有限公司"):
        name = name.replace(suffix, "")
    return re.sub(r"\s+", "", name)


def audit_regressions(jobs_by_url):
    failures = []
    for sample in load_json(REGRESSIONS_FILE, []):
        url = clean_str(sample.get("job_url"))
        expected = clean_str(sample.get("expected_stock_id"))
        job = jobs_by_url.get(url)
        if not job:
            if sample.get("allow_missing"):
                continue
            failures.append(f"missing regression job: {url} ({sample.get('note', '')})")
            continue
        actual = clean_str(job.get("stock_id"))
        if actual != expected:
            failures.append(f"bad stock_id for {url}: expected {expected}, got {actual}")
    return failures


def audit_company_alias_coverage(jobs):
    failures = []
    aliases = load_json(COMPANY_ALIASES_FILE, [])
    urls_by_company_id = defaultdict(list)
    for job in jobs:
        url = clean_str(job.get("job_url"))
        if "104.com.tw/job/" not in url:
            continue
        company_name = normalize_company_name(job.get("company_name"))
        for entry in aliases:
            expected_stock_id = clean_str(entry.get("stock_id"))
            names = [entry.get("name", ""), *entry.get("aliases", [])]
            if expected_stock_id and any(normalize_company_name(name) in company_name for name in names if name):
                urls_by_company_id[expected_stock_id].append(url)

    for entry in aliases:
        stock_id = clean_str(entry.get("stock_id"))
        if not stock_id:
            continue
        if not urls_by_company_id.get(stock_id):
            failures.append(f"no local jobs matched 104 company alias stock_id={stock_id}")
    return failures


def audit_company_name_splits(jobs):
    failures = []
    stock_ids_by_name = defaultdict(set)
    for job in jobs:
        if clean_str(job.get("source")) != "104":
            continue
        name = normalize_company_name(job.get("company_name"))
        if not name:
            continue
        stock_ids_by_name[name].add(clean_str(job.get("stock_id")))

    for name, stock_ids in sorted(stock_ids_by_name.items()):
        non_empty = {sid for sid in stock_ids if sid}
        if len(non_empty) > 1:
            failures.append(f"company_name split across stock_ids: {name} -> {sorted(non_empty)}")
    return failures


def audit_seed_mapping(jobs):
    name_map, match_stock_id = load_seed_helpers()
    failures = []
    for job in jobs:
        if clean_str(job.get("source")) != "104":
            continue
        company_name = clean_str(job.get("company_name"))
        expected = match_stock_id(company_name, name_map)
        actual = clean_str(job.get("stock_id"))
        if expected and actual and actual != expected:
            failures.append(
                f"company mapping drift: {company_name} expected {expected}, got {actual} ({job.get('job_url')})"
            )
    return failures


def audit_raw_company_ai_filter():
    failures = []
    for row in load_json(RAW_COMPANY_JOBS_FILE, []):
        item = row.get("item", {})
        title = clean_str(item.get("jobName"))
        if title and not is_title_ai_related(title):
            failures.append(f"raw company output contains non-title-AI job: {title}")
    return failures


def main():
    jobs = load_json(JOBS_FILE, [])
    jobs_by_url = {clean_str(job.get("job_url")): job for job in jobs if clean_str(job.get("job_url"))}

    failures = []
    failures.extend(audit_regressions(jobs_by_url))
    failures.extend(audit_company_alias_coverage(jobs))
    failures.extend(audit_company_name_splits(jobs))
    failures.extend(audit_seed_mapping(jobs))
    failures.extend(audit_raw_company_ai_filter())

    if failures:
        print("Job data quality audit failed:")
        for failure in failures[:80]:
            print(f"- {failure}")
        if len(failures) > 80:
            print(f"- ... {len(failures) - 80} more")
        return 1

    print(f"Job data quality audit passed: {len(jobs)} local jobs checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
