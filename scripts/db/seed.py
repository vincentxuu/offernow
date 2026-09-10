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


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema_sql = f.read()

    lines = [schema_sql, "", "-- Seed data", ""]

    for c in companies:
        cols = [
            "stock_id", "name", "short_name", "industry", "market",
            "chairman", "gm", "address", "phone",
            "established", "listed_date", "capital", "tax_id",
            "salary_median_k", "salary_mean_k",
            "salary_median_change_pct",
            "employee_count", "eps", "salary_year",
        ]
        vals = [
            sql_val(c.get("stock_id")),
            sql_val(c.get("name")),
            sql_val(c.get("short_name")),
            sql_val(c.get("industry")),
            sql_val(c.get("market")),
            sql_val(c.get("chairman")),
            sql_val(c.get("gm")),
            sql_val(c.get("address")),
            sql_val(c.get("phone")),
            sql_val(c.get("established")),
            sql_val(c.get("listed_date")),
            sql_val(c.get("capital")),
            sql_val(c.get("tax_id")),
            sql_val(c.get("salary_median_k")),
            sql_val(c.get("salary_mean_k")),
            sql_val(c.get("salary_median_change_pct")),
            sql_val(c.get("employee_count")),
            sql_val(c.get("eps")),
            sql_val(c.get("salary_year")),
        ]
        lines.append(
            f"INSERT OR REPLACE INTO company_profiles ({', '.join(cols)}) VALUES ({', '.join(vals)});"
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {OUTPUT_FILE} with {len(companies)} INSERT statements")


if __name__ == "__main__":
    main()
