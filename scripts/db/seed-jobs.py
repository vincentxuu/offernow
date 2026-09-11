#!/usr/bin/env python3
"""
Seed D1 jobs table from all job JSON sources.
Merges jobs.json + 104_remotework_jobs.json + global_remote_jobs.json,
deduplicates, cleans, and generates seed-jobs.sql.

Usage:
    python3 scripts/db/seed-jobs.py
    pnpm wrangler d1 execute offernow-db --local --file scripts/db/seed-jobs.sql
    pnpm wrangler d1 execute offernow-db --remote --file scripts/db/seed-jobs.sql
"""

import json
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = Path(__file__).parent / "seed-jobs.sql"

REMOTE_KW_STRICT = [
    "remote work", "remote position", "remote job", "remote role",
    "fully remote", "work remotely", "remote-first",
    "work from home", "wfh",
    "遠端工作", "遠端辦公", "遠距工作", "遠距辦公",
    "在家工作", "居家辦公", "居家工作",
    "混合辦公", "混合工作", "hybrid work",
]


def clean_str(s):
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", s)
    if s in ("None", "nan", "NaN", "null"):
        return ""
    return s.strip()


def escape_sql(val):
    if val is None:
        return "NULL"
    s = clean_str(val)
    if not s:
        return "NULL"
    # Replace newlines with spaces, escape single quotes
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace("'", "''")
    return "'" + s + "'"


def sql_int(val):
    if val is None or val == "" or val == "None":
        return "NULL"
    try:
        v = int(float(val))
        return str(v) if v > 0 else "NULL"
    except (ValueError, TypeError):
        return "NULL"


def is_truly_remote(title, description):
    text = (clean_str(title) + " " + clean_str(description)).lower()
    return any(kw in text for kw in REMOTE_KW_STRICT)


def load_companies_name_map():
    companies_file = DATA_DIR / "companies_with_salary.json"
    if not companies_file.exists():
        return {}
    with open(companies_file, encoding="utf-8") as f:
        companies = json.load(f)
    name_map = {}
    for c in companies:
        name = c.get("name", "")
        short = c.get("short_name", "")
        name_map[name] = c["stock_id"]
        if short:
            name_map[short] = c["stock_id"]
            name_map[short.replace("*-KY", "").replace("-KY", "").strip()] = c["stock_id"]
        clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
        if clean:
            name_map[clean] = c["stock_id"]
    return name_map


def match_stock_id(company_name, name_map):
    cn = clean_str(company_name)
    sid = name_map.get(cn)
    if sid:
        return sid
    clean = cn.replace("股份有限公司", "").replace("有限公司", "").strip()
    sid = name_map.get(clean)
    if sid:
        return sid
    first = cn.split("_")[0].replace("(總公司)", "").replace("集團", "").strip()
    sid = name_map.get(first)
    if sid:
        return sid
    for name, s in name_map.items():
        if len(name) >= 2 and name in cn:
            return s
    return ""


def main():
    print("=" * 60)
    print("OfferNow — Seeding D1 Jobs Table")
    print("=" * 60)

    name_map = load_companies_name_map()
    seen = set()
    all_jobs = []

    # Source 1: existing jobs.json (already in Job format)
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        with open(jobs_file, encoding="utf-8") as f:
            jobs = json.load(f)
        for j in jobs:
            title = clean_str(j.get("title", ""))
            cn = clean_str(j.get("company_name", ""))
            key = (title, cn)
            if not title or key in seen:
                continue
            seen.add(key)
            sid = j.get("stock_id", "")
            if not sid or sid.startswith("ext_"):
                sid = match_stock_id(cn, name_map) or sid
            jt = clean_str(j.get("job_type", ""))
            if jt == "None":
                jt = ""
            all_jobs.append({
                "stock_id": sid,
                "company_name": cn,
                "title": title,
                "location": clean_str(j.get("location", "")),
                "date_posted": clean_str(j.get("date_posted", "")),
                "job_url": clean_str(j.get("job_url", "")),
                "source": clean_str(j.get("source", "")),
                "description": clean_str(j.get("description", ""))[:200],
                "salary_min": j.get("salary_min"),
                "salary_max": j.get("salary_max"),
                "job_type": jt,
            })
        print(f"  jobs.json: {len(jobs)} loaded, {len(all_jobs)} after dedup")

    # Source 2: 104 remoteWork jobs (104 raw format)
    remotework_file = DATA_DIR / "104_remotework_jobs.json"
    if remotework_file.exists():
        with open(remotework_file, encoding="utf-8") as f:
            raw = json.load(f)
        added = 0
        for item in raw:
            cn = clean_str(item.get("custName", ""))
            title = clean_str(item.get("jobName", ""))
            key = (title, cn)
            if not title or key in seen:
                continue
            seen.add(key)
            sid = match_stock_id(cn, name_map)
            appear = clean_str(item.get("appearDate", ""))
            date_fmt = f"{appear[:4]}-{appear[4:6]}-{appear[6:8]}" if len(appear) == 8 else ""
            link = item.get("link", {}).get("job", "") or ""
            if isinstance(link, str) and link.startswith("//"):
                link = "https:" + link
            desc = clean_str(item.get("description", ""))[:200]
            jt = "remote" if is_truly_remote(title, desc) else ""
            all_jobs.append({
                "stock_id": sid or f"ext_{cn[:20]}",
                "company_name": cn,
                "title": title,
                "location": clean_str(item.get("jobAddrNoDesc", "")),
                "date_posted": date_fmt,
                "job_url": clean_str(link),
                "source": "104",
                "description": desc,
                "salary_min": item.get("salaryLow"),
                "salary_max": item.get("salaryHigh"),
                "job_type": jt,
            })
            added += 1
        print(f"  104_remotework_jobs.json: {len(raw)} loaded, {added} new")

    # Source 3: global remote jobs (Job format)
    global_file = DATA_DIR / "global_remote_jobs.json"
    if global_file.exists():
        with open(global_file, encoding="utf-8") as f:
            global_jobs = json.load(f)
        added = 0
        for j in global_jobs:
            title = clean_str(j.get("title", ""))
            cn = clean_str(j.get("company_name", ""))
            key = (title, cn)
            if not title or key in seen:
                continue
            seen.add(key)
            sid = match_stock_id(cn, name_map) or j.get("stock_id", "") or f"ext_{cn[:20]}"
            all_jobs.append({
                "stock_id": sid,
                "company_name": cn,
                "title": title,
                "location": clean_str(j.get("location", "")),
                "date_posted": clean_str(j.get("date_posted", "")),
                "job_url": clean_str(j.get("job_url", "")),
                "source": clean_str(j.get("source", "")),
                "description": clean_str(j.get("description", ""))[:200],
                "salary_min": j.get("salary_min"),
                "salary_max": j.get("salary_max"),
                "job_type": "global_remote",
            })
            added += 1
        print(f"  global_remote_jobs.json: {len(global_jobs)} loaded, {added} new")

    print(f"\nTotal jobs to seed: {len(all_jobs)}")

    # Generate SQL
    lines = [
        "DROP TABLE IF EXISTS jobs;",
        "",
        "CREATE TABLE jobs (",
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "  stock_id TEXT,",
        "  company_name TEXT NOT NULL,",
        "  title TEXT NOT NULL,",
        "  location TEXT,",
        "  date_posted TEXT,",
        "  job_url TEXT,",
        "  source TEXT,",
        "  description TEXT,",
        "  salary_min INTEGER,",
        "  salary_max INTEGER,",
        "  job_type TEXT DEFAULT ''",
        ");",
        "",
        "CREATE INDEX idx_jobs_stock_id ON jobs(stock_id);",
        "CREATE INDEX idx_jobs_source ON jobs(source);",
        "CREATE INDEX idx_jobs_job_type ON jobs(job_type);",
        "",
        "-- Seed data",
        "",
    ]

    for j in all_jobs:
        # Skip jobs with no company name or title
        if not j["company_name"] or not j["title"]:
            continue
        vals = ", ".join([
            escape_sql(j["stock_id"]),
            escape_sql(j["company_name"]),
            escape_sql(j["title"]),
            escape_sql(j["location"]),
            escape_sql(j["date_posted"]),
            escape_sql(j["job_url"]),
            escape_sql(j["source"]),
            escape_sql(j["description"]),
            sql_int(j["salary_min"]),
            sql_int(j["salary_max"]),
            escape_sql(j["job_type"]),
        ])
        lines.append(
            f"INSERT INTO jobs (stock_id, company_name, title, location, date_posted, job_url, source, description, salary_min, salary_max, job_type) VALUES ({vals});"
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {OUTPUT_FILE} with {len(all_jobs)} INSERT statements")

    # Stats
    by_source = {}
    by_type = {}
    for j in all_jobs:
        by_source[j["source"]] = by_source.get(j["source"], 0) + 1
        jt = j["job_type"] or "general"
        by_type[jt] = by_type.get(jt, 0) + 1

    print(f"\nBy source: {by_source}")
    print(f"By type: {by_type}")


if __name__ == "__main__":
    main()
