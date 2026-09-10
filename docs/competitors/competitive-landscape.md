# 台灣百大上市櫃公司職缺聚合：競品分析與市場機會

> 研究日期：2026-09-10
> 研究目的：評估「以上市櫃公司為軸心，主動聚合職缺」的市場空白與技術可行性

---

## 子問題與結論總覽

| # | 子問題 | 結論 |
|---|--------|------|
| 1 | 104/1111 上市櫃篩選體驗 | 有篩選但被動（企業付費才上架），覆蓋約 70%（1,280/1,800+ 家） |
| 2 | TWSE/TPEx OpenAPI 能取得什麼 | 免費、免註冊，公司基本資料+產業分類+財報+股價齊全，JSON 格式 |
| 3 | 上市櫃公司招募頁面 ATS 生態 | 自建為主（鴻海/聯發科/金融業），台積電用 SuccessFactors，高度碎片化 |
| 4 | 台灣版 Levels.fyi | 比薪水(salary.tw)最接近，但無職缺聚合功能 |
| 5 | 證交所員工薪資揭露資料 | 每年 6 月底於 MOPS 公布，含中位數（108 年度起），無正式 API 需爬取 |
| 6 | 商業模式可行性 | Niche board 毛利 85-99%，solo operator $2K-$110K/月；Freemium + 訂閱最可行 |

---

## 1. 競品地圖

### 1.1 直接競品（台灣職缺聚合）

**結論：無人專做「以上市櫃公司為軸心」的職缺聚合。**

| 產品 | 定位 | 資料來源 | 覆蓋範圍 | AI 功能 | 商業模式 |
|------|------|----------|----------|---------|----------|
| **Job Frog** (job-frog.com) | 台灣外商科技職缺聚合 | 爬 ATS（Greenhouse/Lever/Workday） | 20+ 家外商科技（Google/Apple/NVIDIA），不含台灣本土上市櫃 | Claude AI 繁中摘要、中文語意搜尋 | 免費，個人 side project |
| **Jobuzzer** (jobuzzer.com) | 全球職缺聚合 | 爬公司 career page | 全球科技公司，非專注台灣 | AI 履歷配對評分（S+~F） | Freemium + Buzz 訂閱（email alert） |
| **Jobbo** (jobbojobs.com) | 跨人力銀行聚合搜尋 | 整合 104/LinkedIn/CakeResume | 跨平台通用職缺，不以公司為軸心 | AI 求職信產生器 | Freemium（AI 求職信付費） |

**來源**：各網站首頁及功能頁 [實測/scrape]

### 1.2 間接競品（人力銀行）

| 平台 | 上市櫃篩選 | 限制 |
|------|-----------|------|
| **104 人力銀行** | 有「上市上櫃」篩選（zone=16），約 1,280 家；有薪資中位數排行 | 職缺由企業付費刊登（$4,200/月起），被動覆蓋；薪資與職缺頁面分開 |
| **1111 人力銀行** | 無專門篩選器，僅關鍵字搜尋 | 同被動刊登模式 |
| **CakeResume / Yourator** | 無上市櫃篩選，偏新創/科技 | 不適用 |
| **LinkedIn** | 可搜公司名，無台灣上市櫃分類 | 台灣資料較稀疏 |

### 1.3 薪資透明平台

| 平台 | 定位 | 資料量 | 與上市櫃交集 | 串職缺？ |
|------|------|--------|-------------|---------|
| **比薪水 (salary.tw)** | 最大匿名薪資共享，積分制 | 台積電 2070 筆、ASUS 1160 筆 | 熱門公司多為上市櫃 | ❌ |
| **GoodJob** | 開源社群，薪資+面試+工時 | 萬筆以上 | 通用 | ❌ |
| **Levels.fyi 台灣** | 國際平台，TC 拆分 | 台灣 SWE 中位 NT$1.51M | 以外商科技為主 | ✅ 但台灣稀疏 |
| **104 排行** | 證交所資料視覺化 | 全部上市櫃 | ✅ 完整覆蓋 | ❌（薪資與職缺頁分開） |
| **勞動部薪情平台** | 主計總處統計調查 | 按職類/學歷/年資 | 統計級，非個別公司 | ❌ |

### 1.4 補充競品（第二輪搜尋）

| 產品 | 定位 | 相關度 | 備註 |
|------|------|--------|------|
| **JobSeek** (cclts, 190⭐) | 開源，監控 4,400+ 家公司官網 career page | **高** | 爬蟲架構最接近（monitors/ 按 ATS 分類 + Redis queue），但沒有台灣上市櫃 |
| **JobSmith** (sanyoii) | 台灣多代理 AI 求職 co-pilot，LangGraph 編排 | **高** | 同時搜 104/Cake/Yourator/LinkedIn/JobFrog 等 8 平台 |
| **job-source-mcp** (wmh) | MCP Server 搜台灣職缺 | **高** | 104/Yourator/CakeResume/LinkedIn 的現成資料管道 |
| **Jobscanner** | 台灣職缺聚合 Web App | 中 | 104/Yourator/CakeResume，Vercel 部署 |
| **yes123** | 台灣第三大人力銀行 | 中 | 575 筆上市櫃搜尋結果，同被動刊登制 |
| **Meet.jobs** | 跨境社交求職（**已 2026/6/30 關站**） | 中 | 30 萬用戶仍撐不住，驗證存活風險 |
| **Techmap** (jobdatafeeds.com) | B2B 職缺數據 feed | 低 | 台灣約 9K 筆/月，驗證數據賣給企業的模式存在 |

### 1.5 技術參考（開源專案）

#### Tier 1 — ATS 爬蟲架構（直接可用）

| 專案 | Stars | 語言 | 定位 | 最值得借鏡 |
|------|-------|------|------|-----------|
| **ats-scrapers** (kalil0321) | PyPI | Python | 統一 ATS 爬蟲庫，20+ 平台 | `pip install ats-scrapers`，**內建 SuccessFactors adapter（台積電用的）**+ Workday/iCIMS/Oracle；`get_scraper_for_url()` 自動辨識 ATS 類型 + 統一 schema |
| **job-board-aggregator** (Feashliaa) | — | Python | 索引 1M+ 職缺，7 ATS 並行爬取 | 多執行緒架構（Workday 50 workers、Greenhouse 30）+ 30 天自動清理 + 異常偵測 |
| **ever-jobs** | — | — | 支援 **35+ ATS 平台** | 最廣覆蓋（含 SuccessFactors/Taleo/ADP），薪資萃取 + 年薪標準化 + 按 ATS 自動路由 |
| **JobSeek** (colophon-group) | 190 | Python | 監控 4,400+ 家公司 | monitors/ 按 ATS 分類 + dashboard |
| **JobSpy** (speedyapply) | 4.3K | Python | 一行程式爬 LinkedIn/Indeed/Glassdoor/Google | `scrape_jobs()` 統一介面，最成熟的人力銀行爬蟲 |

#### Tier 2 — AI 求職整合

| 專案 | Stars | 語言 | 定位 | 最值得借鏡 |
|------|-------|------|------|-----------|
| **career-ops** (career-ops-hq) | **70.4K** | JS/Go | 最熱門 AI 求職框架 | A-H 結構化評估 + 五維度評分 + 150+ 公司 portal 掃描 |
| **ai-job-search** (MadsLorentzen) | **41.1K** | Python/TS | AI 求職自動化 | 雙 agent 對抗（drafter vs reviewer）、`/add-portal` 插件式架構、候選人 profile 放 CLAUDE.md |
| **Resume Matcher** (srbhr) | **28.1K** | Python/TS | AI 履歷-職缺配對 | 100+ LLM 支援 + ATS 評分 + 向量搜尋 |
| **JobSync** (Gsync) | 987 | TypeScript | 自架 AI 求職追蹤器 | MCP 支援 + Ollama 本地 LLM + 隱私優先 |

#### Tier 3 — 台灣相關 / 基礎設施

| 專案 | 語言 | 定位 | 最值得借鏡 |
|------|------|------|-----------|
| **job-source-mcp** (wmh) | Python | 台灣職缺 MCP Server | 104/Yourator/CakeResume/LinkedIn 爬蟲現成可用 |
| **TWSEMCPServer** (twjackysu) | Python FastMCP | 證交所/櫃買/期交所 API | 143 個 tools，公司名單+財務資料一站取得 |
| **openings-mcp** (amikai) | Go | 多 ATS 搜尋 MCP Server | Go 寫的 MCP 範本 |
| **freehire** (strelov1, 649⭐) | Go/Svelte | 自架職缺搜尋引擎 | Meilisearch + LangChain，全端 self-hosted |

> ⚠️ **JobFunnel (2.2K stars) 已於 2025/12 歸檔**，驗證純爬蟲路線的維護成本風險。

### 1.6 國際模式參考

| 平台 | 可借鏡的產品機制 |
|------|-----------------|
| **RemoteOK** | Solo operator $25K-$110K/月，Premium listing 定價 $599+ |
| **Remotive** | 職缺 + 社群生態 |
| **FlexJobs** | 人工策展精選品質 |
| **WorkingNomads** | 訂閱推播 + 分類清楚 |
| **Indeed** | CPC 模式 $7.4B 營收，ARPJ 成長 13-19% YoY |
| **ZipRecruiter** | 訂閱制 ~75%，89% 毛利率，AI outbound matching |

### 1.7 技術棧建議（基於開源生態）

根據以上開源專案，最務實的技術組合：

```
資料層：
├── 公司名單：TWSEMCPServer（143 tools，免費 JSON API）
├── ATS 爬蟲：ats-scrapers（pip install，SuccessFactors/Workday/20+ 平台）
├── 人力銀行：job-source-mcp（104/CakeResume/Yourator/LinkedIn）
├── 薪資資料：MOPS 爬蟲（POST 表單，年度更新）
└── 去重/排程：job-board-aggregator 的多執行緒 + 30 天清理模式

AI 層：
├── 職缺配對：career-ops 的五維度評分 or Resume Matcher 的向量搜尋
├── 中文語意搜尋：Job Frog 已驗證 Claude AI 可做繁中摘要
└── 雙 agent 品質控制：ai-job-search 的 drafter vs reviewer 模式

產品層：
├── 前端：freehire 的 Svelte + Meilisearch 全文搜尋
├── MCP 整合：JobSync 的 MCP 支援模式
└── 訂閱通知：WorkingNomads 的 email alert 機制
```

---

## 2. 資料來源可行性

### 2.1 TWSE/TPEx OpenAPI

**免費、免註冊、免 API key，HTTP GET 回 JSON。**

| 端點 | 回傳內容 | 市場 |
|------|---------|------|
| `t187ap03_L` | 上市公司基本資料（名稱、產業別、統編、董監事） | 上市 |
| `mopsfin_t187ap03_O` | 同上，上櫃版（欄位改用英文命名） | 上櫃 |
| `t187ap05_L` | 每月營業收入（當月/上月/去年同月+增減%） | 上市 |
| `STOCK_DAY_ALL` | 全市場單一交易日開高低收+成交量 | 上市 |

注意：日期為民國年（1150730 = 2026-07-30）、上市/上櫃分屬兩套 API、多數端點為最新快照無歷史查詢。

### 2.2 MOPS 員工薪資揭露

- **法規**：108 年度（2019）起揭露，115 年起資本額 100 億以上需揭露性別薪資
- **欄位**：非主管全時員工人數、薪資總額、薪資平均數、薪資中位數
- **查詢**：`mopsov.twse.com.tw/mops/web/t100sb15`
- **更新**：每年 6 月底統一揭示前一年度
- **無正式 API**：需 POST 表單爬取，已有社群 Python 爬蟲（GitHub Gist jkjung-avt）
- 104 的排行引用同一份資料（確認標註「證交所公開資訊觀測站」）

### 2.3 常見 ATS 平台總覽

ATS（Applicant Tracking System，申請人追蹤系統）是企業管理招募流程的軟體，負責刊登職缺、收集履歷、追蹤面試。對爬蟲來說，用標準 ATS 的公司有結構化頁面可以批量爬；自建系統的就得一家一家寫。

#### 國際主流 ATS

| ATS 平台 | 市場定位 | 開源爬蟲支援 | 台灣使用者 |
|----------|---------|-------------|-----------|
| **Workday** | 大型企業/外商首選 | ✅ ats-scrapers、ever-jobs、JobSeek | 外商在台辦公室 |
| **SAP SuccessFactors** | 大型製造/半導體 | ✅ ats-scrapers、ever-jobs | **台積電** |
| **Greenhouse** | 中型科技/新創熱門 | ✅ ats-scrapers、JobSeek、Job Frog | 外商科技（Google 等在台） |
| **Lever** | 中型科技/新創 | ✅ ats-scrapers、JobSeek、Job Frog | 外商科技 |
| **Oracle Taleo** | 傳統大型企業 | ✅ ever-jobs | 少數台灣企業 |
| **iCIMS** | 美國中大型企業 | ✅ ats-scrapers | 極少 |
| **Ashby** | 新創/scale-up | ✅ ats-scrapers | 極少 |
| **SmartRecruiters** | 中大型企業 | ✅ ats-scrapers | 少數 |
| **ADP** | HR 全套解決方案 | ✅ ever-jobs | 少數外商 |

#### 台灣本土 ATS / 招募系統

| 系統 | 定位 | 客戶 | 開源爬蟲 |
|------|------|------|---------|
| **ARES 資通** | 台灣最大本土 ATS | 華碩、世界先進、欣興、寶成、建興、采鈺 | ❌ 需自建 |
| **104 企業版** | 人力銀行 + 簡易 ATS | 多數中小型上市櫃 | ⚠️ job-source-mcp 有 104 爬蟲 |
| **各公司自建** | 客製化招募站 | 鴻海（isite-web）、聯發科、國泰金（iMatch）、富邦金、中信金、台達電、廣達 | ❌ 需逐家寫 |

### 2.4 台灣上市櫃 ATS 使用分布（爬取難度地圖）

| 公司 | 招募系統 | 爬取難度 | 來源 |
|------|---------|---------|------|
| 台積電 | SAP SuccessFactors | 中（需 JS render，URL 結構固定） | 實測 URL |
| 鴻海 | 自建 isite-web | 中（Java 框架，session/CSRF） | 實測 URL |
| 聯發科 | 自建 yourcareers.mediatek.com | 中 | 實測 URL |
| 國泰金控 | 自建 iMatch | 中 | 實測 URL |
| 富邦金/中信金 | 自建（嵌入官網） | 高 | 實測 URL |
| 台達電/廣達 | 自建 | 中 | 實測 URL |
| 華碩/世界先進/欣興 | ARES 資通 | 中（本土 ATS，結構統一） | ARES 官網客戶案例 |
| 外商科技 | Greenhouse/Lever/Workday | 低（有結構化 API） | Job Frog 已驗證 |
| 中小型上市櫃 | 主要透過 104 刊登 | N/A | 推測 |

**結論**：高度碎片化。最務實策略 = **104 + LinkedIn 雙主要來源 + ats-scrapers 覆蓋標準 ATS + 逐家補自建系統**。

### 2.5 資料來源優先級（修正版）

```
第一層（核心，~70%）：104 結構化 JSON API（zone=16）
第二層（補齊，覆蓋率可能更高）：LinkedIn（job-source-mcp / JobSpy）
第三層（官網差異）：ats-scrapers（SuccessFactors/Workday）+ 逐家自建
公開資料層：TWSE/TPEx API（公司資料）+ MOPS（薪資，年度更新）

串接 key：股票代號（TWSE 公司代號 = 104 exchangeId = MOPS 公司代號）
LinkedIn 需額外建立 companyId ↔ 股票代號 mapping
```

---

## 3. 商業模式

### 3.1 全球職缺平台營收模式

| 模式 | 代表 | 營收規模 | 毛利率 |
|------|------|---------|--------|
| CPC 按點擊付費 | Indeed | $7.4B | ~36% EBITDA |
| 訂閱制 | ZipRecruiter | $449M | 89% gross |
| 多元串流 | LinkedIn | ~$17B+ | N/A |
| 動態定價 | Seek (澳洲) | AUD $1.1B | ~42% EBITDA |

### 3.2 Niche Job Board 實際營收

| 平台 | 月營收 | 模式 |
|------|--------|------|
| MoAIJobs (AI niche) | $2,300/月 | 付費刊登，solo |
| Work With Indies | $5,000/月 | 社群+刊登 |
| Remote Rocketship | $6,500/月 | 向求職者收費 |
| RemoteOK | $25K-$110K/月 | Premium listings，solo |
| Just Join IT | €14.5M/年 | bootstrapped，19x 成長 |

### 3.3 台灣市場適用性 [推測]

| 模式 | 適用度 | 理由 |
|------|--------|------|
| Freemium + 訂閱通知 | ⭐⭐⭐⭐ | 免費瀏覽，付費「新職缺即時通知」+「AI 配對」 |
| 企業端品牌頁 | ⭐⭐⭐ | 上市櫃公司付費升級品牌頁面 |
| 資料分析 API | ⭐⭐⭐ | 職缺趨勢數據賣給投資機構/HR tech |
| 獵頭佣金 | ⭐⭐ | 台灣獵頭市場已飽和 |

---

## 4. 事實交叉表

| 事實 | 來源 1 | 來源 2 | 狀態 |
|------|--------|--------|------|
| TWSE OpenAPI 免註冊免 key | openapi.twse.com.tw Swagger | twmarketdata.com 教學 | ✅ |
| 上市上櫃分屬兩套 API | TWSE Swagger | TPEx 官網 | ✅ |
| 日期為民國年格式 | twmarketdata.com | Threads @jimmy.ai.dev 實測 | ✅ |
| 員工薪資中位數 108 年起公布 | MOPS 官網說明 | 金管會 2019 公告 | ✅ |
| 每年 6 月底揭示薪資 | MOPS 官網 | 104 職場力報導 | ✅ |
| 114 年度平均薪資 144.7 萬，年增 6.8% | TWSE 新聞稿 | — | ⚠️ unverified（單源官方） |
| MOPS 無正式 API | 多篇爬蟲教學均用 POST 表單 | — | ⚠️ unverified |
| 台積電用 SuccessFactors | URL 結構實測 | owlapply.com 攻略 | ✅ |
| 鴻海自建 isite-web | URL 結構實測 | — | ⚠️ unverified（單源） |
| ARES 客戶含華碩/世界先進/欣興 | ares.com.tw 官方 | — | ⚠️ unverified（單源官方） |
| 104 覆蓋約 1,280 家上市櫃公司 | 104 搜尋 zone=16 | blog.jiatool.com 爬蟲文 | ✅ |
| Indeed 年營收 $7.4B | cavuno.com 引用 Recruit Holdings 財報 | — | ⚠️ unverified |
| Niche board 毛利 85-99% | gaps.com | cavuno.com | ✅ |
| RemoteOK $25K-$110K/月 | cavuno.com | gaps.com | ✅ |

---

## 5. 市場機會總結

### 5.1 核心空白

**沒有人在做「以上市櫃公司為軸心，主動爬取並聚合所有職缺來源」這件事。**

- 104 → 被動（企業付費上架）
- Job Frog → 只做外商科技
- Jobuzzer → 不專注台灣
- Jobbo → 聚合人力銀行不爬官網
- 比薪水 → 只有薪資無職缺

### 5.2 獨特價值主張

把三個目前分散的公開資料串在一起：

1. **TWSE/TPEx OpenAPI** → 公司基本資料、產業分類、市值、營收
2. **MOPS 員工薪資揭露** → 非主管全時員工薪資中位數
3. **各公司招募頁面 + 104** → 即時職缺

= **「看得到公司全貌的職缺平台」**

### 5.3 差異化功能方向

| 功能 | 競品無 | 技術可行性 |
|------|--------|-----------|
| 產業板塊職缺趨勢（「半導體業本週新增 200 缺」） | ✅ | 高 |
| 擴編/縮編信號（某公司 6 個月職缺數量變化） | ✅ | 高（需定期快照） |
| 薪資 × 職缺交叉（「中位數 300 萬，正在徵 XX」） | ✅ | 高 |
| 財報 × 招募交叉（「營收成長 20% 的公司都在招什麼人」） | ✅ | 中 |
| AI 職缺配對 + 中文語意搜尋 | Job Frog 部分有 | 高 |

### 5.4 技術風險

| 風險 | 嚴重度 | 應對 |
|------|--------|------|
| 各公司招募頁面結構不統一 | 高 | 104 當 fallback + 逐步擴展官網爬蟲 |
| MOPS 無 API，結構可能改版 | 中 | 每年抓一次（6 月底），快照存檔 |
| 法律風險（爬取官網職缺） | 中 | 職缺屬公開資訊，但需注意各站 ToS |
| TWSE API 速率限制 | 低 | 自行節流 + 快取 |

---

## 6. 競品 Teardown 摘要

完整拆解報告見各獨立檔案，此處摘錄核心發現。

### 6.1 Job Frog（job-frog.com）

> 完整報告：`2026-09-10-jobfrog-teardown.md`

**一句話**：台灣外商科技職缺聚合，92 家公司 3,000+ 職缺，AI 摘要 + 中文語意搜尋。

**技術架構**：Next.js RSC + Cloudflare，搜尋走伺服器端渲染（無獨立搜尋 API），展開公司時才打 `/api/search`。

**AI 機制**：
- 預先生成（批次 Claude API），非即時 — 搜尋結果秒出
- 四欄摘要：職責 / 領域 / 技能 / 亮點（全繁中）
- 每家公司有 AI 生成介紹（一句話標題 + 詳述 + 3 標籤 + 台灣在地觀點）
- 職缺分類也是 AI 自動分類（軟體工程 / 現場服務 / 品質與測試等 12 類）

**可借鏡**：四欄 AI 摘要結構、預先生成存 DB 的做法、按公司分組的 UX、`/go/{id}` 導流追蹤。

**我們超越的空間**：只有 92 家外商 vs 我們 1,800+ 上市櫃、無薪資/財務資料、無歷史趨勢、無多來源交叉比對。

### 6.2 Jobuzzer（jobuzzer.com）

> 完整報告：`2026-09-10-jobuzzer-teardown.md`

**一句話**：全球職缺聚合 600K+ 職缺，AI 評級 S+~F + 履歷報告 + MCP Server。

**技術架構**：Next.js RSC + Cloudflare + 獨立 API（`api.jobuzzer.com`）+ MCP Server（`mcp.jobuzzer.com`），PostHog 分析。

**AI 機制**：
- **S+~F 評級**：上傳履歷一次，AI 比對每個職缺打分（付費功能）
- **履歷報告**：硬技能覆蓋率 + 缺口辨識 + 逐句修改建議（消耗 AI 額度）
- 每個職缺有 AI 生成的繁中摘要 + 產業分類 + 技能標籤

**MCP Server（11 tools）**：
- 解析工具：`search_skills`、`search_locations`、`search_organizations`（先 resolve 再搜尋）
- 核心搜尋：`search_jobs`、`get_job`
- 用戶操作：`save_job`/`unsave_job`、`mark_applied`、`list_applications`、`update_application_status`
- 免費 10 req/min、付費 100 req/min

**商業模式**：
- 免費：瀏覽全部 + 12hr 延遲通知 + 3 份履歷 + MCP
- Buzz $5/月：即時每小時通知 + AI 評級 + 150 點 AI 額度 + 履歷報告 + CSV 匯出
- 7 天免費試用

**可借鏡**：AI S+~F 評級概念、MCP Server 的解析-搜尋分離設計、12hr 延遲 vs 即時作為付費轉換點、提示詞產生器降低 MCP 門檻。

**我們超越的空間**：全球但台灣稀疏、無公司財務/薪資、非原生繁中、無產業趨勢。

### 6.3 Job Frog vs Jobuzzer 比較

| 面向 | Job Frog | Jobuzzer | 我們的定位 |
|------|----------|---------|-----------|
| **定位** | 台灣外商科技 | 全球職缺 | 台灣上市櫃全產業 |
| **規模** | 92 家，3K 職缺 | 12K 家，600K 職缺 | 1,800+ 家上市櫃 |
| **AI 角色** | 摘要+翻譯（預處理） | 評級+報告（互動式） | 兩者結合 + 結構化資料 |
| **獨特資料** | 無 | 無 | TWSE API + MOPS 薪資 |
| **商業模式** | 免費 side project | Freemium $5/月 | Freemium + 資料分析 API |
| **MCP** | ❌ | ✅ 11 tools | ✅（參考 Jobuzzer 設計） |
| **台灣在地化** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 7. ATS 平台深度研究摘要

> 完整報告：`2026-09-10-ats-platforms-deep-dive.md`

**市場規模**：全球 ATS 市場 ~$3.3B（2025），CAGR 8-10%，亞太成長最快（11.6%）。

**爬取策略分層**：

| 層級 | ATS 平台 | 爬取方式 | 覆蓋 |
|------|---------|---------|------|
| **最易** | Greenhouse / Lever / Ashby | 免費公開 JSON API | 外商科技 |
| **中等** | Workday / SuccessFactors | JS render + ats-scrapers 套件 | 台積電 + 部分大型企業 |
| **困難** | 自建系統（鴻海/聯發科/金控） | 逐家寫爬蟲 or LLM schema extraction | 多數台灣上市櫃 |
| **Fallback** | 104 人力銀行 | job-source-mcp 現成爬蟲 | ~70% 上市櫃 |

**關鍵工具**：
- `ats-scrapers`（PyPI）：50+ adapter，含 SuccessFactors，MIT 授權
- `job-source-mcp`：104/Yourator/CakeResume/LinkedIn 台灣職缺現成管道
- `TWSEMCPServer`：143 個 TWSE/TPEx tools

**台灣 ATS 生態**：ARES（本土龍頭，華碩/世界先進等）、MAYO（SaaS）、104 Pro、Teamdoor — 全部沒有公開 API。

**法律風險**：爬取公開 career page 和 ATS public API 風險最低（hiQ v. LinkedIn 判例支持），避免登入牆後的平台。

### 6.4 104 人力銀行（104.com.tw）

> 完整報告：`2026-09-10-104-teardown.md`

**一句話**：台灣最大人力銀行，1,280 家上市櫃公司、結構化 JSON API、薪資排行直接有股票代號。

**三大核心 API（全部不需登入）**：

1. **公司列表** `GET /company/ajax/list?zone=16&pageSize=18`
   - 1,280 家上市櫃，分 72 頁
   - 欄位：encodedCustNo、name、industryDesc、capitalDesc、jobCount、mainScore、tagNames

2. **薪資排行** `GET /company/ajax/salary/top100`
   - 155 家公司，直接有 `exchangeId`（**股票代號**）
   - 欄位：`medianNonSupervisor`（非主管中位數）、`mean`（全員工平均）、`industryMean`（產業平均）
   - **exchangeId 可直接串 TWSE OpenAPI** — 這是最大發現

3. **職缺搜尋** `GET /jobs/search/api/jobs?keyword=...&zone=16&pagesize=20`
   - 完整 JD + 地點（含 GPS）+ 薪資 + 學歷 + 語言要求 + HR 回應速度
   - `tags.zone.param: 16` 標記上市櫃
   - `custNo` 是公司統編，可用於去重

**公司 ID 串接鏈**：
```
104 encodedCustNo → exchangeId（股票代號）→ TWSE OpenAPI → MOPS 薪資
```

**可借鏡**：API 設計清晰（JSON、分頁、結構化）、zone 參數篩選、薪資 × 職缺的資料模型。

**注意**：需確認 ToS 爬取合規性，建議用 `job-source-mcp` 間接取得。

### 6.5 LinkedIn（linkedin.com/jobs）

> 完整報告：`2026-09-10-linkedin-teardown.md`

**一句話**：台灣上市櫃職缺量遠超預期（鴻海 11K、台積電 7K、聯發科 4K），有 Guest API，是不可忽略的第二資料來源。

**職缺量抽樣（vs 之前認為「台灣稀疏」是錯的）**：

| 公司 | LinkedIn | 104（推估） |
|------|----------|-----------|
| 鴻海 | 11,000+ | 數百 |
| 台積電 | 7,000+ | 數百 |
| 聯發科 | 4,000+ | 476 |
| 國泰金控 | 1,000+ | 數十 |

> 注意：LinkedIn 數字可能含子公司/過期職缺，需打折。但即便如此仍遠超 104。

**Guest API**：`GET /jobs-guest/jobs/api/jobPosting/{id}` — 不需登入，回傳 HTML fragment。

**爬取策略**：反爬嚴格，建議用已有開源工具（`job-source-mcp` / `JobSpy`），不直接爬。

**Company ID 問題**：LinkedIn 用自己的 `companyId`，需建立 companyId ↔ 股票代號 mapping（一次性用公司名搜尋建表）。

### 6.6 MOPS 公開資訊觀測站

> 完整報告：`2026-09-10-mops-teardown.md`

**一句話**：全部上市櫃公司的非主管薪資中位數，POST 一次就能拿到，31 個欄位比 104 多很多。

**API**：
```
POST /mops/web/ajax_t100sb15
Body: encodeURIComponent=1&step=1&firstin=1&TYPEK=sii&RYEAR=114&code=
```
- `TYPEK=sii`（上市）/ `otc`（上櫃），`code` 留空查全部
- Response 是 HTML table，需 parse

**31 欄位含**：公司代號（=股票代號）、薪資總額、員工人數、平均數（今/去年）、中位數（今/去年）、變動%、EPS、男/女性薪資（100 億以上）、同業平均、薪資統計旗標、公司自述改善措施。

**有 CSV 下載**：`/server-java/t105sb02`

### 6.7 TWSE/TPEx OpenAPI

> 完整報告：`2026-09-10-twse-api-teardown.md`

**一句話**：1,094 上市 + 890 上櫃 = 1,984 家公司，免費 JSON API，`公司代號` = 104 `exchangeId` 已驗證。

**注意**：TWSE 用中文欄位、TPEx 用英文欄位，需建 mapping 層。「百大」需自己算（收盤價 × 發行股數 = 市值）。

---

## 8. 附件索引

| 檔案 | 內容 |
|------|------|
| `2026-09-10-taiwan-listed-company-job-aggregator.md` | 本文（主 research note） |
| `2026-09-10-ats-platforms-deep-dive.md` | ATS 平台完整深度研究 |
| `2026-09-10-jobfrog-teardown.md` | Job Frog 完整 service teardown（L1-L6） |
| `2026-09-10-jobuzzer-teardown.md` | Jobuzzer 完整 service teardown（L1-L6） |
| `2026-09-10-jobbo-teardown.md` | Jobbo service teardown（Tinder UX + 即時聚合） |
| `2026-09-10-104-teardown.md` | 104 人力銀行 service teardown（API 重點） |
| `2026-09-10-linkedin-teardown.md` | LinkedIn service teardown（Guest API + 覆蓋率） |
| `2026-09-10-mops-teardown.md` | MOPS 公開資訊觀測站（薪資揭露 POST API） |
| `2026-09-10-twse-api-teardown.md` | TWSE/TPEx OpenAPI（公司資料 JSON API） |
| `2026-09-10-jobseek-code-teardown.md` | JobSeek 開源爬蟲架構分析 |
| `2026-09-10-jobuzzer-teardown.md` | Jobuzzer 完整 service teardown（L1-L6） |

---

## 草稿骨架（供後續發文用）

1. **問題**：想找上市櫃公司的工作，為什麼得一家一家翻？
2. **現況**：台灣職缺聚合生態盤點（104 被動 / Job Frog 外商 / 比薪水只有薪資）
3. **機會**：三個公開資料源的交叉點（TWSE API × MOPS 薪資 × 招募頁面）
4. **國際參考**：Indeed/Levels.fyi/RemoteOK 的產品機制與營收
5. **技術可行性**：ATS 碎片化地圖 + 104 作為 fallback 的務實策略
6. **商業模式**：Niche board 光譜（$2K side project → $110K solo operator）
7. **結論**：這個空白值不值得填？
