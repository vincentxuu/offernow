#!/bin/bash
set -e

cd "$(dirname "$0")"

MAX_LLM=${MAX_LLM:-50}
SKIP_FETCH=${SKIP_FETCH:-0}

run() {
    echo ""
    echo "=================================================="
    echo "▶ $1"
    echo "=================================================="
    shift
    "$@"
}

# ── 環境檢查 ──────────────────────────────────────────────────

# 安裝 uv（若未安裝）
if ! command -v uv &>/dev/null; then
    echo "📦 安裝 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 建立虛擬環境並安裝依賴（若尚未建立）
if [ ! -f "pyproject.toml" ]; then
    echo "📦 初始化 uv 環境..."
    uv init --no-workspace
fi

uv add --quiet requests beautifulsoup4

# 檢查 claude CLI
if ! command -v claude &>/dev/null; then
    echo "⚠️  找不到 claude CLI，filter.py 將使用 fallback 分數"
    echo "   安裝：https://claude.ai/download"
fi

# ── Pipeline ──────────────────────────────────────────────────

if [ "$SKIP_FETCH" != "1" ]; then
    run "104 爬蟲"      uv run fetch.py
    run "LinkedIn 爬蟲" uv run fetch_linkedin.py
fi

run "職缺過濾與 LLM 評分（前 ${MAX_LLM} 筆）" uv run filter.py --max-llm "$MAX_LLM"
run "技能分析" uv run analyze.py --skip-llm

echo ""
echo "=================================================="
echo "✅ Pipeline 完成"
echo "   報告：reports/filter_report.md"
echo "         reports/skills_report.md"
echo "=================================================="
