"""
Snapshot current job counts and calculate trends.

Reads job counts from companies_with_salary.json, generates SQL to:
1. UPSERT into job_count_snapshots for the current period
2. Calculate trend by comparing with the previous period
3. Update company_profiles with prev_month count and trend

Usage:
    uv run scripts/snapshot-job-counts.py
    uv run scripts/snapshot-job-counts.py --period 2026-09
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "companies_with_salary.json"
OUTPUT_FILE = Path(__file__).parent / "db" / "snapshot.sql"

EXPANDING_THRESHOLD = 0.10
SHRINKING_THRESHOLD = -0.10
MIN_ABSOLUTE_DELTA = 5


def get_period(override: str | None = None) -> str:
    if override:
        return override
    return datetime.now().strftime("%Y-%m")


def prev_period(period: str) -> str:
    year, month = map(int, period.split("-"))
    dt = datetime(year, month, 1) - timedelta(days=1)
    return dt.strftime("%Y-%m")


def calculate_trend(current: int, previous: int) -> str:
    if previous == 0:
        return "stable"
    delta_pct = (current - previous) / previous
    abs_delta = current - previous
    if delta_pct > EXPANDING_THRESHOLD and abs_delta >= MIN_ABSOLUTE_DELTA:
        return "expanding"
    if delta_pct < SHRINKING_THRESHOLD and abs_delta <= -MIN_ABSOLUTE_DELTA:
        return "shrinking"
    return "stable"


def escape_sql(value: str) -> str:
    return value.replace("'", "''")


def main():
    period_override = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--period" and i < len(sys.argv) - 1:
            period_override = sys.argv[i + 1]

    period = get_period(period_override)
    prev = prev_period(period)

    with open(DATA_FILE) as f:
        companies = json.load(f)

    lines = [
        f"-- Job count snapshot for period {period}",
        f"-- Generated at {datetime.now().isoformat()}",
        f"-- Companies: {len(companies)}",
        "",
        "-- 1. Snapshot current job counts",
        "",
    ]

    for c in companies:
        stock_id = escape_sql(c["stock_id"])
        j104 = c.get("job_count_104") or 0
        jli = c.get("job_count_linkedin") or 0
        total = j104 + jli

        lines.append(
            f"INSERT INTO job_count_snapshots (stock_id, period, job_count_104, job_count_linkedin, job_count_total) "
            f"VALUES ('{stock_id}', '{period}', {j104}, {jli}, {total}) "
            f"ON CONFLICT (stock_id, period) DO UPDATE SET "
            f"job_count_104 = {j104}, job_count_linkedin = {jli}, job_count_total = {total}, "
            f"captured_at = datetime('now');"
        )

    lines.extend([
        "",
        "-- 2. Calculate trends by comparing with previous period",
        f"-- Previous period: {prev}",
        "",
    ])

    for c in companies:
        stock_id = escape_sql(c["stock_id"])
        current_total = (c.get("job_count_104") or 0) + (c.get("job_count_linkedin") or 0)

        lines.append(
            f"UPDATE company_profiles SET "
            f"job_count_prev_month = COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0), "
            f"job_count_trend = CASE "
            f"WHEN COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0) = 0 THEN 'stable' "
            f"WHEN ({current_total} - COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0)) >= {MIN_ABSOLUTE_DELTA} "
            f"AND CAST(({current_total} - COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0)) AS REAL) / "
            f"COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 1) > {EXPANDING_THRESHOLD} THEN 'expanding' "
            f"WHEN ({current_total} - COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0)) <= -{MIN_ABSOLUTE_DELTA} "
            f"AND CAST(({current_total} - COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 0)) AS REAL) / "
            f"COALESCE("
            f"(SELECT job_count_total FROM job_count_snapshots "
            f"WHERE stock_id = '{stock_id}' AND period = '{prev}'), 1) < {SHRINKING_THRESHOLD} THEN 'shrinking' "
            f"ELSE 'stable' END "
            f"WHERE stock_id = '{stock_id}';"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} lines to {OUTPUT_FILE}")
    print(f"Period: {period}, Previous: {prev}")

    with_jobs = sum(1 for c in companies if (c.get("job_count_104") or 0) + (c.get("job_count_linkedin") or 0) > 0)
    print(f"Companies with jobs: {with_jobs}/{len(companies)}")
    print(f"\nApply with: wrangler d1 execute offernow-db --file={OUTPUT_FILE}")


if __name__ == "__main__":
    main()
