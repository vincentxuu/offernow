#!/usr/bin/env python3
"""
Seed D1 database from companies_with_salary.json.
Generates a SQL file that can be run with wrangler d1 execute.

Usage:
    python3 scripts/db/seed.py
    # Then:
    pnpm wrangler d1 execute offernow-db --local --file scripts/db/seed.sql
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "companies_with_salary.json"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"
OUTPUT_FILE = Path(__file__).parent / "seed.sql"


def escape_sql(val: str | None) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


def sql_val(val) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    return escape_sql(str(val))


COLS = [
    "stock_id", "name", "short_name", "industry", "market",
    "chairman", "gm", "address", "phone",
    "established", "listed_date", "capital", "tax_id", "shares_outstanding",
    "salary_median_k", "salary_mean_k",
    "salary_median_prev_k", "salary_mean_prev_k",
    "salary_median_change_pct", "salary_mean_change_pct",
    "employee_count", "eps", "salary_year",
    "salary_male_median_k", "salary_female_median_k",
    "salary_male_mean_k", "salary_female_mean_k",
    "industry_salary_avg_k", "industry_avg_eps", "salary_vs_industry_pct",
    "flag_low_salary", "flag_eps_high_salary_low", "flag_eps_up_salary_down",
    "salary_explanation", "improvement_measures",
    "revenue_latest", "revenue_yoy_pct", "revenue_period",
    "market_cap",
    "job_count_104", "encoded_cust_no_104",
    "job_count_linkedin",
    "ai_insight",
]


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema_sql = f.read()

    lines = [schema_sql, "", "-- Seed data", ""]

    for c in companies:
        vals = [sql_val(c.get(col)) for col in COLS]
        lines.append(
            f"INSERT OR REPLACE INTO company_profiles ({', '.join(COLS)}) VALUES ({', '.join(vals)});"
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {OUTPUT_FILE} with {len(companies)} INSERT statements")


if __name__ == "__main__":
    main()
