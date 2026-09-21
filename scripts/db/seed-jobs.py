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

COMPANY_NAME_ALIASES = {
    "華南金融控股": "2880",
    "華南金控": "2880",
    "華南商業銀行": "2880",
    "華南銀行": "2880",
    "華南永昌證券": "2880",
    "富邦金融控股": "2881",
    "富邦金控": "2881",
    "台北富邦銀行": "2881",
    "富邦銀行": "2881",
    "富邦人壽": "2881",
    "富邦產險": "2881",
    "富邦證券": "2881",
    "富邦綜合證券": "2881",
    "Fubon Financial": "2881",
    "國泰金融控股": "2882",
    "國泰金控": "2882",
    "國泰世華": "2882",
    "國泰人壽": "2882",
    "國泰產險": "2882",
    "國泰證券": "2882",
    "Cathay Financial": "2882",
    "凱基金融控股": "2883",
    "凱基金控": "2883",
    "凱基證券": "2883",
    "凱基銀行": "2883",
    "凱基人壽": "2883",
    "中華開發資本": "2883",
    "KGI Financial": "2883",
    "KGI SECURITIES": "2883",
    "KGI Bank": "2883",
    "玉山金融控股": "2884",
    "玉山金控": "2884",
    "玉山商業銀行": "2884",
    "玉山銀行": "2884",
    "E.SUN": "2884",
    "元大金控": "2885",
    "元大金融控股": "2885",
    "元大證券": "2885",
    "元大銀行": "2885",
    "元大人壽": "2885",
    "元大投信": "2885",
    "Yuanta Financial": "2885",
    "兆豐金融控股": "2886",
    "兆豐金控": "2886",
    "兆豐國際商業銀行": "2886",
    "兆豐銀行": "2886",
    "兆豐證券": "2886",
    "Mega Financial": "2886",
    "台新新光金融控股": "2887",
    "台新新光金控": "2887",
    "台新銀行": "2887",
    "台新證券": "2887",
    "新光銀行": "2887",
    "新光人壽": "2887",
    "Taishin": "2887",
    "國票金融控股": "2889",
    "國票金控": "2889",
    "國際票券": "2889",
    "國票證券": "2889",
    "永豐金融控股": "2890",
    "永豐金控": "2890",
    "永豐商業銀行": "2890",
    "永豐銀行": "2890",
    "永豐金證券": "2890",
    "永豐證券": "2890",
    "SinoPac": "2890",
    "中信金控": "2891",
    "中國信託金融控股": "2891",
    "中國信託": "2891",
    "中信銀行": "2891",
    "中國信託商業銀行": "2891",
    "中國信託產物保險": "2891",
    "中國信託綜合證券": "2891",
    "台灣人壽": "2891",
    "中信證券": "2891",
    "CTBC Financial": "2891",
    "第一金融控股": "2892",
    "第一金控": "2892",
    "第一商業銀行": "2892",
    "第一銀行": "2892",
    "第一金證券": "2892",
    "合庫金融控股": "5880",
    "合作金庫金融控股": "5880",
    "合庫金控": "5880",
    "合作金庫商業銀行": "5880",
    "合作金庫銀行": "5880",
    "合庫銀行": "5880",
    "合庫證券": "5880",
    "群聯電子": "8299",
    "群聯": "8299",
    "Phison": "8299",
}


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
            normalized_short = short.replace("*-KY", "").replace("-KY", "").strip()
            if normalized_short:
                name_map.setdefault(normalized_short, c["stock_id"])
        clean = name.replace("股份有限公司", "").replace("有限公司", "").strip()
        if clean:
            name_map.setdefault(clean, c["stock_id"])
    return name_map


def match_stock_id(company_name, name_map):
    cn = clean_str(company_name)
    for alias, sid in COMPANY_NAME_ALIASES.items():
        if alias.lower() in cn.lower():
            return sid
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
    for name, s in sorted(name_map.items(), key=lambda item: len(item[0]), reverse=True):
        if len(name) >= 4 and name in cn:
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
            sid = match_stock_id(cn, name_map) or j.get("stock_id", "")
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

    # Generate SQL — UPSERT mode: preserve click_count, update job data
    lines = [
        "-- OfferNow jobs UPSERT (preserves click_count)",
        "-- Generated by seed-jobs.py",
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
        "-- UPSERT: new jobs get inserted, existing jobs (same job_url) get updated",
        "",
    ]

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
