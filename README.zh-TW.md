<div align="center">

# OfferNow

**台灣上市櫃公司職缺聚合平台 — 把 TWSE、MOPS、104 三個散落的公開資料串在一起。**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-early_preview-orange.svg)

[快速開始](#快速開始) · [功能總覽](#功能總覽) · [資料管道](#資料管道) · [MCP Server](#mcp-server) · [部署](#部署)

[English](README.md) · [繁體中文](README.zh-TW.md)

</div>

> [!IMPORTANT]
> OfferNow 是非官方的個人開源學習專案，僅供教育研究與個人使用。未獲 104 人力銀行或 LinkedIn 官方授權，使用可能違反各平台服務條款，請自行評估法律與合規風險。

## 為什麼做這個？

想找上市櫃公司的工作，你得在三個地方來回翻：

- **證交所 / 櫃買中心** — 公司基本資料、產業分類、市值、營收
- **公開資訊觀測站 (MOPS)** — 非主管全時員工薪資中位數（每年 6 月更新）
- **104 / LinkedIn / 公司官網** — 職缺

OfferNow 把這三層公開資料串成一個平台，讓你一眼看到「**這家公司薪水多少、在不在擴編、財務健不健康**」。

## 功能總覽

| 功能 | 說明 |
| --- | --- |
| **1,984 家公司資料** | 上市 1,094 + 上櫃 890，含產業分類、市值、營收、員工數 |
| **薪資排行** | MOPS 非主管薪資中位數 / 平均數，含性別薪資（資本額 100 億以上） |
| **職缺聚合** | 104 + LinkedIn + 遠端職缺，3,370+ 筆 |
| **公司吸引力分數** | 五維度結構化評分（A–F）：薪資競爭力、成長動能、擴編趨勢、財務健康、風險旗標 |
| **產業趨勢** | 各產業職缺增減 delta，擴編 / 縮編信號 |
| **薪資 × 職缺交叉** | 「只看招募中」篩選、「成長招募中」徽章 |
| **導流追蹤** | `/go/{id}` 點擊計數 + 302 redirect，為未來 CPC 變現鋪路 |
| **JSON-LD SEO** | `JobPosting` + `Organization` structured data，Google for Jobs 可收錄 |
| **MCP Server** | 6 個工具，讓 Claude Code 直接查詢公司與職缺資料 |

## 架構

```text
資料來源                    資料管道                      前端 + 服務
─────────                  ─────────                    ────────────
TWSE OpenAPI ─┐
TPEx OpenAPI ─┤
MOPS 薪資    ─┼── Python 爬蟲 ──→ JSON ──→ seed SQL ──→ Cloudflare D1
104 API      ─┤       │                                     │
LinkedIn     ─┘       │                                     ▼
                      │                              TanStack Start (React)
                      ▼                              Cloudflare Workers
               快照 + 趨勢計算                        Tailwind CSS
                                                          │
                                                          ▼
MCP Server ◄──── Claude Code                         offernow.workers.dev
(6 tools)         直接呼叫
```

## 快速開始

**環境需求：** Node.js 22+、pnpm、[uv](https://docs.astral.sh/uv/)（Python 爬蟲用）

```bash
git clone https://github.com/vincentxuu/offernow.git
cd offernow
pnpm install
pnpm dev
```

開發伺服器啟動在 `http://localhost:3000`。

### 資料更新（一鍵）

```bash
./scripts/refresh-data.sh              # 爬取 → 快照 → UPSERT D1
./scripts/refresh-data.sh --skip-fetch  # 跳過爬取，只更新 D1
./scripts/refresh-data.sh --local       # apply 到 local D1（開發用）
```

## 資料管道

### 爬蟲

| 腳本 | 資料來源 | 說明 |
| --- | --- | --- |
| `fetch-data/fetch.py` | 104 人力銀行 | 公開 JSON API，關鍵字搜尋 + 地區過濾 |
| `fetch-data/fetch_linkedin.py` | LinkedIn | HTML 解析公開職缺頁面 |
| `fetch-data/fetch_104_company_ids.py` | 104 公司列表 | 建立 stock_id ↔ encodedCustNo 映射 |
| `scripts/fetch-companies.py` | TWSE / TPEx | 公司基本資料 + 產業分類 |
| `scripts/fetch-mops-full.py` | MOPS | 員工薪資揭露（31 欄位） |

### 資料處理

| 腳本 | 說明 |
| --- | --- |
| `scripts/db/seed-jobs.py` | 合併職缺 JSON → UPSERT SQL（保留 click_count） |
| `scripts/snapshot-job-counts.py` | 月度快照 + 擴編 / 縮編趨勢計算 |
| `scripts/generate-insights.ts` | LLM 生成公司 AI 洞察（需 API key） |

### 資料串接鏈

```
104 encodedCustNo → exchangeId（股票代號）→ TWSE OpenAPI → MOPS 薪資
```

公司代號是串接所有資料的 key。目前 104 映射覆蓋率 59%（1,177 / 1,985）。

## MCP Server

讓 Claude Code 直接查詢 OfferNow 資料，不需要開瀏覽器。

| 工具 | 說明 |
| --- | --- |
| `search_companies` | 依名稱 / 產業 / 市場搜尋，支援薪資和市值門檻 |
| `get_company` | 依股票代號取得完整公司 profile |
| `get_top_salaries` | 薪資中位數排行，支援產業篩選 |
| `get_industry_trends` | 產業級聚合：公司數、職缺數、平均薪資 |
| `search_jobs` | 依關鍵字 / 公司 / 地點搜尋職缺 |
| `list_local_data` | 資料檔案狀態檢查 |

**安裝：**

```bash
claude mcp add -s user offernow -- bash -c "cd /path/to/offernow/fetch-data && uv run mcp_server.py"
```

## 技術棧

| 層 | 技術 |
| --- | --- |
| 前端 | TanStack Start (React) + TanStack Router + TanStack Query |
| 樣式 | Tailwind CSS v4 |
| 資料庫 | Cloudflare D1 (SQLite) |
| 部署 | Cloudflare Workers |
| 爬蟲 | Python + requests + BeautifulSoup |
| MCP | FastMCP (Python) |

## 部署

```bash
pnpm run deploy    # build + wrangler deploy
```

部署到 Cloudflare Workers，D1 資料庫隨 Worker binding 自動連接。

### D1 Schema 初始化

```bash
wrangler d1 execute offernow-db --remote --file=scripts/db/schema.sql
wrangler d1 execute offernow-db --remote --file=scripts/db/seed.sql
wrangler d1 execute offernow-db --remote --file=scripts/db/seed-jobs.sql
```

## 資料來源

| 來源 | 內容 | 更新頻率 |
| --- | --- | --- |
| [TWSE OpenAPI](https://openapi.twse.com.tw/) | 上市公司基本資料、股價、營收 | 即時 |
| [TPEx](https://www.tpex.org.tw/) | 上櫃公司基本資料、股價、營收 | 即時 |
| [MOPS 公開資訊觀測站](https://mopsov.twse.com.tw/) | 員工薪資揭露（中位數 / 平均數 / 性別） | 每年 6 月 |
| [104 人力銀行](https://www.104.com.tw/) | 職缺、公司資訊、薪資排行 | 即時 |
| [LinkedIn](https://www.linkedin.com/jobs/) | 職缺 | 即時 |

## 貢獻

歡迎透過 [GitHub Issues](https://github.com/vincentxuu/offernow/issues) 回報問題或提出建議。Pull Request 請先開 Issue 討論。

## 免責聲明

- 本工具未獲 104 人力銀行或 LinkedIn 官方授權，使用可能違反各平台服務條款（Terms of Service），請自行評估法律與合規風險。
- 所有分析結果僅供參考，不保證資料的即時性、完整性或準確性。
- 使用者同意自行承擔使用本工具的一切後果，作者及貢獻者不對任何損失或法律問題負責。

## 授權

MIT License
