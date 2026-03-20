"""
一鍵執行完整 pipeline：
  1. 爬取 104 職缺
  2. 爬取 LinkedIn 職缺
  3. 職缺過濾與 LLM 評分
  4. 技能分析

執行：
    uv run --with requests --with beautifulsoup4 fetch-data/run.py
    uv run --with requests --with beautifulsoup4 fetch-data/run.py --max-llm 50
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent


def run(cmd: list[str], label: str) -> bool:
    print(f"\n{'=' * 50}")
    print(f"▶ {label}")
    print("=" * 50)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n❌ {label} 失敗（exit {result.returncode}），中止 pipeline")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="一鍵執行完整 fetch-data pipeline")
    parser.add_argument("--max-llm", type=int, default=50,
                        help="filter.py LLM 評分上限（預設：50）")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="跳過爬蟲，直接跑 filter + analyze")
    args = parser.parse_args()

    py = sys.executable
    steps = []

    if not args.skip_fetch:
        steps += [
            ([py, str(SCRIPTS / "fetch.py")], "104 爬蟲"),
            ([py, str(SCRIPTS / "fetch_linkedin.py")], "LinkedIn 爬蟲"),
        ]

    steps += [
        ([py, str(SCRIPTS / "filter.py"), "--max-llm", str(args.max_llm)], f"職缺過濾與 LLM 評分（前 {args.max_llm} 筆）"),
        ([py, str(SCRIPTS / "analyze.py"), "--skip-llm"], "技能分析"),
    ]

    for cmd, label in steps:
        if not run(cmd, label):
            sys.exit(1)

    print(f"\n{'=' * 50}")
    print("✅ Pipeline 完成")
    print(f"   報告：fetch-data/reports/filter_report.md")
    print(f"         fetch-data/reports/skills_report.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
