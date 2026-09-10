#!/usr/bin/env python3
"""
Generate AI insights for top companies using Claude API.

Requires ANTHROPIC_API_KEY environment variable.

Usage:
    ANTHROPIC_API_KEY=sk-... python3 scripts/generate-insights.py
    # or if key is already exported:
    python3 scripts/generate-insights.py
"""

import json
import os
import sys
import time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: uv pip install --system --break-system-packages anthropic")
    sys.exit(1)

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
INSIGHTS_FILE = DATA_DIR / "insights.json"

MODEL = "claude-sonnet-5"
BATCH_SIZE = 5
TOP_N = 100


def generate_insight(client: anthropic.Anthropic, company: dict) -> str:
    salary_wan = (company.get("salary_median_k") or 0) / 10
    change = company.get("salary_median_change_pct")
    change_str = f"{change:+.1f}%" if change is not None else "無資料"

    prompt = f"""公司：{company.get('name', '')}（{company.get('stock_id', '')}）
產業：{company.get('industry', '未分類')}
薪資中位數：{salary_wan:.1f} 萬
薪資變動：{change_str}
EPS：{company.get('eps', '無資料')}
員工數：{company.get('employee_count', '無資料')}
104 職缺數：{company.get('job_count_104', 0)}

用一句話（30 字內）總結這家公司對求職者的吸引力。
只說客觀事實，不做主觀評價。不要用「值得」「推薦」等詞。
直接輸出那句話，不要加引號或其他格式。"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Usage: ANTHROPIC_API_KEY=sk-... python3 scripts/generate-insights.py")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 60)
    print(f"OfferNow — Generating AI Insights (Top {TOP_N})")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    with_salary = [c for c in companies if c.get("salary_median_k") is not None]
    with_salary.sort(key=lambda x: x.get("salary_median_k", 0), reverse=True)
    top = with_salary[:TOP_N]

    print(f"Processing {len(top)} companies...\n")

    insights = {}
    for i in range(0, len(top), BATCH_SIZE):
        batch = top[i : i + BATCH_SIZE]
        for c in batch:
            name = c.get("short_name") or c.get("name")
            stock_id = c.get("stock_id")
            try:
                insight = generate_insight(client, c)
                insights[stock_id] = insight
                print(f"  [{i + batch.index(c) + 1}/{len(top)}] {name} ({stock_id}): {insight}")
            except Exception as e:
                print(f"  [{i + batch.index(c) + 1}/{len(top)}] {name} ({stock_id}): ERROR - {e}")
                insights[stock_id] = None

        if i + BATCH_SIZE < len(top):
            time.sleep(1)

    # Save insights backup
    with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    print(f"\nSaved insights to {INSIGHTS_FILE}")

    # Merge back into companies
    for company in companies:
        stock_id = company.get("stock_id")
        if stock_id in insights and insights[stock_id]:
            company["ai_insight"] = insights[stock_id]

    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)
    print(f"Updated {COMPANIES_FILE}")

    generated = sum(1 for v in insights.values() if v)
    print(f"\nGenerated {generated}/{len(top)} insights")
    print("Done!")


if __name__ == "__main__":
    main()
