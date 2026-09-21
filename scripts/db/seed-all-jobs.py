#!/usr/bin/env python3
"""
Seed D1 jobs table from ALL job JSON sources (scripts/data + fetch-data/data).
Merges, deduplicates, cleans, and generates seed-all-jobs.sql.

Usage:
    python3 scripts/db/seed-all-jobs.py
    pnpm wrangler d1 execute offernow-db --remote --file scripts/db/seed-all-jobs.sql
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = ROOT / "scripts" / "data"
FETCH_DATA = ROOT / "fetch-data" / "data"
OUTPUT_FILE = Path(__file__).parent / "seed-all-jobs.sql"

REMOTE_KW = [
    "remote work", "remote position", "remote job", "fully remote",
    "work remotely", "remote-first", "work from home", "wfh",
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


def load_companies_map():
    f = SCRIPTS_DATA / "companies_with_salary.json"
    if not f.exists():
        return {}
    with open(f, encoding="utf-8") as fh:
        companies = json.load(fh)
    m = {}
    for c in companies:
        name = c.get("name", "")
        short = c.get("short_name", "")
        sid = c["stock_id"]
        m[name] = sid
        if short:
            m[short] = sid
            m[short.replace("*-KY", "").replace("-KY", "").strip()] = sid
        clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
        if clean:
            m[clean] = sid
    return m


def match_stock_id(company_name, name_map):
    cn = clean_str(company_name)
    if not cn:
        return ""
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
        if len(name) >= 3 and name in cn:
            return s
    return ""


def normalize_job(j, source_hint="", job_type_hint="", name_map=None):
    title = clean_str(j.get("title") or j.get("job_name") or j.get("name", ""))
    cn = clean_str(j.get("company_name") or j.get("company", ""))
    if not title:
        return None

    sid = j.get("stock_id", "")
    if (not sid or sid.startswith("ext_")) and name_map:
        sid = match_stock_id(cn, name_map) or sid
    if not sid:
        sid = f"ext_{cn[:20]}" if cn else ""

    source = clean_str(j.get("source", "")) or source_hint
    jt = clean_str(j.get("job_type", "")) or job_type_hint
    if jt in ("None", "nan"):
        jt = ""

    url = clean_str(j.get("job_url") or j.get("link", ""))
    if url.startswith("//"):
        url = "https:" + url

    loc = clean_str(j.get("location", ""))
    desc = clean_str(j.get("description", ""))[:200]
    date = clean_str(j.get("date_posted") or j.get("posted_date", ""))

    return {
        "stock_id": sid,
        "company_name": cn,
        "title": title,
        "location": loc,
        "date_posted": date,
        "job_url": url,
        "source": source.lower(),
        "description": desc,
        "salary_min": j.get("salary_min"),
        "salary_max": j.get("salary_max"),
        "job_type": jt,
    }


def load_json(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []


def main():
    print("=" * 60)
    print("OfferNow — Seed ALL Jobs into D1")
    print("=" * 60)

    name_map = load_companies_map()
    seen_urls = set()
    seen_title_company = set()
    all_jobs = []

    sources = [
        # scripts/data
        (SCRIPTS_DATA / "jobs.json", "", ""),
        (SCRIPTS_DATA / "104_ai_jobs.json", "104", ""),
        (SCRIPTS_DATA / "104_remotework_jobs.json", "104", "remote"),
        (SCRIPTS_DATA / "104_remote_jobs.json", "104", "remote"),
        (SCRIPTS_DATA / "global_remote_jobs.json", "", "global_remote"),
        (SCRIPTS_DATA / "remote_jobs_jobspy.json", "", "global_remote"),
        # fetch-data/data
        (FETCH_DATA / "yourator_jobs.json", "yourator", ""),
        (FETCH_DATA / "remoteok_jobs.json", "remoteok", "global_remote"),
        (FETCH_DATA / "wwr_jobs.json", "wwr", "global_remote"),
        (FETCH_DATA / "arcdev_jobs.json", "arcdev", "global_remote"),
        (FETCH_DATA / "hn_jobs.json", "hackernews", "global_remote"),
        (FETCH_DATA / "global_ai_jobs.json", "", ""),
        (FETCH_DATA / "cakeresume_jobs.json", "cakeresume", ""),
        (FETCH_DATA / "104_jobs_search.json", "104", ""),
        (FETCH_DATA / "justremote_jobs.json", "justremote", "global_remote"),
        (FETCH_DATA / "remotive_jobs.json", "remotive", "global_remote"),
        (FETCH_DATA / "dynamitejobs_jobs.json", "dynamitejobs", "global_remote"),
        (FETCH_DATA / "careervault_jobs.json", "careervault", "global_remote"),
        (FETCH_DATA / "himalayas_jobs.json", "himalayas", "global_remote"),
        (FETCH_DATA / "workingnomads_jobs.json", "workingnomads", "global_remote"),
    ]

    for path, source_hint, jt_hint in sources:
        raw = load_json(path)
        if not raw:
            print(f"  {path.name}: (empty or missing)")
            continue

        added = 0
        for item in raw:
            # Handle 104 raw format
            if "custName" in item:
                item = {
                    "title": item.get("jobName", ""),
                    "company_name": item.get("custName", ""),
                    "location": item.get("jobAddrNoDesc", ""),
                    "date_posted": "",
                    "job_url": ("https:" + item["link"]["job"]) if isinstance(item.get("link"), dict) and item["link"].get("job", "").startswith("//") else "",
                    "source": "104",
                    "description": item.get("description", "")[:200],
                    "salary_min": item.get("salaryLow"),
                    "salary_max": item.get("salaryHigh"),
                    "job_type": jt_hint,
                }

            job = normalize_job(item, source_hint, jt_hint, name_map)
            if not job:
                continue

            url = job["job_url"]
            tc_key = (job["title"], job["company_name"])

            if url and "104.com.tw/job/" in url:
                slug = url.split("/job/")[-1].split("?")[0]
                if slug.isdigit():
                    continue

            if url and url in seen_urls:
                continue
            if not url and tc_key in seen_title_company:
                continue

            if url:
                seen_urls.add(url)
            seen_title_company.add(tc_key)
            all_jobs.append(job)
            added += 1

        print(f"  {path.name}: {len(raw)} loaded, {added} new")

    print(f"\nTotal jobs to seed: {len(all_jobs)}")

    lines = [
        "-- OfferNow ALL jobs UPSERT",
        "-- Generated by seed-all-jobs.py",
        "",
        "CREATE TABLE IF NOT EXISTS jobs (",
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "  stock_id TEXT,",
        "  company_name TEXT NOT NULL,",
        "  title TEXT NOT NULL,",
        "  location TEXT,",
        "  date_posted TEXT,",
        "  job_url TEXT UNIQUE,",
        "  source TEXT,",
        "  description TEXT,",
        "  salary_min INTEGER,",
        "  salary_max INTEGER,",
        "  job_type TEXT DEFAULT '',",
        "  click_count INTEGER DEFAULT 0",
        ");",
        "",
        "CREATE INDEX IF NOT EXISTS idx_jobs_stock_id ON jobs(stock_id);",
        "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);",
        "CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);",
        "",
    ]

    count = 0
    for j in all_jobs:
        if not j["company_name"] or not j["title"]:
            continue
        url = escape_sql(j["job_url"])
        if url == "NULL":
            continue
        vals = ", ".join([
            escape_sql(j["stock_id"]),
            escape_sql(j["company_name"]),
            escape_sql(j["title"]),
            escape_sql(j["location"]),
            escape_sql(j["date_posted"]),
            url,
            escape_sql(j["source"]),
            escape_sql(j["description"]),
            sql_int(j["salary_min"]),
            sql_int(j["salary_max"]),
            escape_sql(j["job_type"]),
        ])
        lines.append(
            f"INSERT INTO jobs (stock_id, company_name, title, location, date_posted, job_url, source, description, salary_min, salary_max, job_type) VALUES ({vals})"
            f" ON CONFLICT(job_url) DO UPDATE SET stock_id=excluded.stock_id, company_name=excluded.company_name, title=excluded.title, location=excluded.location, date_posted=excluded.date_posted, description=excluded.description, salary_min=excluded.salary_min, salary_max=excluded.salary_max, job_type=excluded.job_type;"
        )
        count += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nGenerated {OUTPUT_FILE}")
    print(f"  {count} UPSERT statements")

    by_source = {}
    for j in all_jobs:
        s = j["source"] or "unknown"
        by_source[s] = by_source.get(s, 0) + 1
    print(f"\nBy source:")
    for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
