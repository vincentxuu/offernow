# Code Teardown: JobSeek (colophon-group/jobseek)

> 分析日期：2026-09-10
> Repo：github.com/colophon-group/jobseek（190⭐）
> 語言：Python（爬蟲）+ Next.js 16（前端）
> 授權：MIT（程式碼）/ CC BY-NC 4.0（職缺資料）
> 規模：5,300+ 家公司、6,200+ career boards

---

## 專案概覽

瑞士團隊 Colophon Group 開發的開源職缺聚合平台，直接監控公司 career page 和 ATS feed，統一成一致的搜尋模型。產品站 jseek.co。

---

## 目錄結構

```
apps/crawler/                    Python 爬蟲核心
  src/core/monitors/             Career-board 發現（ATS API/sitemap/DOM/feed）
  src/core/scrapers/             職缺萃取（JSON-LD/DOM/PDF/vendor formats）
  src/workers/                   HTTP workers + browser workers + description drain
  src/exporter.py                Postgres → Typesense CDC（Change Data Capture）
  src/labeller/                  每日金標資料集標注 → Hugging Face 上傳
  src/workspace/                 `ws` workflow：agent 驅動的公司新增流程
  data/companies.csv             公司設定 source of truth
  data/boards.csv                Career boards + monitor/scraper 對應設定

apps/web/                        Next.js 16 前端
  app/[lang]/                    多語言路由（en/de/fr/it）
  app/api/v1/                    Public REST API
  app/mcp/                       Hosted Streamable HTTP MCP 端點
  src/db/schema.ts               Web-owned Postgres schema（Drizzle ORM）

packages/mcp-server/             Published @jseek/mcp-server npm 套件
docs/                            架構文件、ADR、runbook
```

---

## 核心架構

```
Company requests → Coding-agent PR → companies.csv + boards.csv
  → Crawler runtime（sync + Redis scheduling + HTTP/browser workers + Postgres）
  → Published read layer（Typesense + S3 descriptions）
  → Next.js web app + REST API + MCP
  → Web Postgres（auth / watchlist / application tracker）
```

**關鍵設計決策**：
- **CSV 是 source of truth**：公司和 board 設定全存 CSV，不存 DB — 易版控、易 review、易 agent 自動化
- **爬蟲 Postgres 和 Web Postgres 分離**：兩個 boundary 各管各的
- **Typesense 做搜尋**：不用 Postgres 做全文搜尋，用 Typesense 的 facet search
- **S3 存完整 JD**：description 不存 DB，存 object storage — 省 DB 空間、便宜

---

## Monitor / Scraper 分層

**Monitor**（`src/core/monitors/`）：**發現** career board 上有哪些職缺 URL
- ATS API monitor（Greenhouse/Lever/Ashby 等有公開 API 的）
- Sitemap monitor（解析 sitemap.xml 找職缺 URL）
- DOM monitor（HTML 解析找職缺列表）
- Feed monitor（RSS/Atom feed）

**Scraper**（`src/core/scrapers/`）：**萃取** 單一職缺頁面的結構化資料
- JSON-LD scraper（解析頁面 structured data）
- DOM scraper（HTML 解析）
- PDF scraper
- Vendor-specific formats（各 ATS 特有格式）

**設計亮點**：monitor 和 scraper 分開註冊，同一個 board 可以用不同組合。`boards.csv` 指定每個 career board 用哪個 monitor + 哪個 scraper。

---

## 排程和 Worker

- **Redis** 做排程（scheduling）
- **HTTP workers** 處理不需要瀏覽器的頁面（純 API / 靜態 HTML）
- **Browser workers**（Playwright）處理需要 JS render 的頁面
- **Description drain** 把完整 JD 送到 S3
- **Exporter** 做 CDC：Postgres 變更 → Typesense 索引更新
- 四個 process role 需要同時跑

---

## 去重策略

- **Source-URL identity**：以原始職缺 URL 做 canonical 去重
- 每個 posting 用 source URL 唯一識別，不靠標題或內容比對

---

## 搜尋模型

Typesense-backed，支援 facets：
- occupation、seniority、technology、location、work mode
- employment type、salary、experience、posting language

---

## Agent 驅動的公司新增

`ws`（workspace）是一個 agent utility：
1. 從 GitHub issue（`company-request` label）取得公司名
2. 查重複
3. 研究公司所有 career board
4. 選擇 monitor + scraper 類型
5. 驗證抓到的資料 + 品牌素材
6. 開 PR

支援的 crawler types：ATS APIs / sitemaps / structured data / rendered pages / PDFs / vendor-specific formats。

生產環境用 Hetzner-hosted Codex runner 自動處理 backlog。

---

## 對我們的可複用價值

| 元件 | 可複用？ | 說明 |
|------|---------|------|
| **CSV source of truth 模式** | ✅ 直接採用 | 公司/board 設定存 CSV，Git 版控 |
| **Monitor/Scraper 分層架構** | ✅ 直接採用 | 發現（monitor）和萃取（scraper）分開，靈活組合 |
| **Typesense 全文搜尋** | ✅ 適合 | 比 Postgres 全文搜尋效能好，facet search 天然支援篩選器 |
| **S3 存描述** | ✅ 適合 | JD 文字量大，存 object storage 省成本 |
| **CDC Exporter** | ✅ 適合 | Postgres → Typesense 增量同步 |
| **MCP Server** | ✅ 參考 | Streamable HTTP，不需 auth，讀取用 |
| **Agent 新增公司** | ⚠️ 概念可用 | 但我們的公司名單來自 TWSE，不需 issue-driven |
| **Labeller（Hugging Face）** | ⚠️ 未來考慮 | 金標資料集訓練用，初期不需要 |

---

## 限制和需要自建的部分

1. **無台灣 ATS 支援**：所有 monitor/scraper 針對西方 ATS（Greenhouse/Lever/Workday），台灣自建系統需全部自寫
2. **無 104 整合**：沒有台灣人力銀行的 adapter
3. **無 TWSE/MOPS 串接**：沒有台灣公開資料的整合
4. **Job data 授權是 CC BY-NC 4.0**：職缺資料不可商用，商用需聯繫授權
5. **基礎設施要求高**：需要 2 個 Postgres + Redis + Typesense + S3，不是簡單 side project 能跑的
6. **5,300 家公司全是歐美**：公司名單和我們完全不重疊

---

## 原始資料來源

- GitHub README：`github.com/colophon-group/jobseek/blob/main/README.md`（via tavily search）
- GitHub topics 頁：`github.com/topics/job-scraper`、`github.com/topics/job-aggregator`
