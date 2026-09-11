#!/usr/bin/env bash
set -euo pipefail

# OfferNow 資料更新一鍵腳本
# 用法：
#   ./scripts/refresh-data.sh              # 完整流程（爬取 + 快照 + 更新 D1）
#   ./scripts/refresh-data.sh --skip-fetch  # 跳過爬取，只更新 D1
#   ./scripts/refresh-data.sh --local       # apply 到 local D1（開發用）

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_FETCH=false
D1_TARGET="--remote"

for arg in "$@"; do
  case $arg in
    --skip-fetch) SKIP_FETCH=true ;;
    --local) D1_TARGET="--local" ;;
  esac
done

echo "============================================================"
echo "OfferNow — 資料更新流程"
echo "============================================================"
echo ""

# ── Step 1: 爬取職缺 ──────────────────────────────────────────
if [ "$SKIP_FETCH" = false ]; then
  echo "📡 Step 1/5: 爬取 104 職缺…"
  uv run --with requests fetch-data/fetch.py
  echo ""

  echo "📡 Step 1/5: 爬取 LinkedIn 職缺…"
  uv run --with requests --with beautifulsoup4 fetch-data/fetch_linkedin.py
  echo ""
else
  echo "⏭️  Step 1/5: 跳過爬取（--skip-fetch）"
  echo ""
fi

# ── Step 2: 快照當前職缺數（趨勢追蹤）──────────────────────────
echo "📸 Step 2/5: 快照職缺數量（趨勢追蹤）…"
uv run scripts/snapshot-job-counts.py
echo ""

# ── Step 3: 生成 jobs seed SQL ─────────────────────────────────
echo "🔧 Step 3/5: 生成 seed-jobs.sql…"
uv run scripts/db/seed-jobs.py
echo ""

# ── Step 4: Apply 到 D1 ───────────────────────────────────────
echo "🚀 Step 4/5: Apply seed-jobs.sql 到 D1 ($D1_TARGET)…"
wrangler d1 execute offernow-db $D1_TARGET --file=scripts/db/seed-jobs.sql --yes
echo ""

echo "🚀 Step 4/5: Apply snapshot.sql 到 D1 ($D1_TARGET)…"
wrangler d1 execute offernow-db $D1_TARGET --file=scripts/db/snapshot.sql --yes
echo ""

# ── Step 5: 驗證 ──────────────────────────────────────────────
echo "✅ Step 5/5: 驗證…"
wrangler d1 execute offernow-db $D1_TARGET --command "SELECT COUNT(*) as job_count FROM jobs" --yes
wrangler d1 execute offernow-db $D1_TARGET --command "SELECT COUNT(*) as snapshot_count FROM job_count_snapshots" --yes 2>/dev/null || echo "   (job_count_snapshots 表尚未建立，先跑 schema.sql)"
echo ""

echo "============================================================"
echo "✅ 資料更新完成！"
echo ""
echo "下一步（可選）："
echo "  pnpm run deploy    # 部署最新前端到 Cloudflare"
echo "============================================================"
