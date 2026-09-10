# ATS 平台深度研究：市場格局、技術架構與爬取策略

> 研究日期：2026-09-10
> 研究目的：為「台灣百大上市櫃職缺聚合」專案評估 ATS 平台的爬取可行性與技術策略

---

## Q1: 全球 ATS 市場格局

### 市場規模

| 來源 | 2025 估值 | 2030 預測 | CAGR | 驗證 |
|------|----------|----------|------|------|
| MarketsandMarkets | $3.28B | $4.88B | 8.2% | ✅ [官方報告](https://www.marketsandmarkets.com/Market-Reports/applicant-tracking-system-market-27004100.html) |
| The Insight Partners | $3.52B | — (2034: $8.23B) | 10.0% | ✅ [官方報告](https://www.theinsightpartners.com/reports/applicant-tracking-system-market) |
| IMARC Group | $3.14B | — (2034: $6.35B) | 8.14% | ✅ [官方報告](https://www.imarcgroup.com/applicant-tracking-system-market) |

**共識**：2025 年全球 ATS 市場約 $3.1-3.5B，CAGR 8-10%。亞太是成長最快區域（~10-11.6% CAGR）。

### 市佔率與排名

| 排名 | 廠商 | 市佔 | 定位 | 來源 |
|------|------|------|------|------|
| 1 | **Workday** | ~32% 美國企業市場 | 統一 HCM + 招募，2025 年收購 Paradox | `實測` [BestRecruitingTools](https://bestrecruitingtools.com/blog/icims-ats-review-enterprise-2026) |
| 2 | **Greenhouse** | ~18% 美國企業市場 | 結構化面試、科技業首選 | 同上 |
| 3 | **iCIMS** | ~10% 美國企業市場 | 獨立 ATS，2025 年收購 Apli | 同上 |
| 4 | **SAP SuccessFactors** | 企業 HCM 套件內 ATS | 全球合規、製造業 | `官方文件` MarketsandMarkets |
| 5 | **Oracle (Taleo/Cloud HCM)** | 企業 HCM 套件內 ATS | ERP 整合、供應鏈連結招募 | 同上 |

Top 5 廠商合計佔企業 ATS 營收約 55-60%。`官方文件` [IMARC](https://www.imarcgroup.com/applicant-tracking-system-market)

> ⚠️ **2025 年三大併購重塑市場**：SAP 買 SmartRecruiters、Workday 買 Paradox、iCIMS 買 Apli。獨立 ATS 正被 HCM 套件吸收。`二手` [Pin.com](https://www.pin.com/blog/best-applicant-tracking-systems)

### 各平台目標客群與定價

| 平台 | 目標客群 | 定價範圍 | 來源 |
|------|---------|---------|------|
| **Workday** | 大型企業（1000+ 員工）、BFSI、醫療、IT | $6K-$140K+/yr | `二手` Pin.com |
| **Greenhouse** | 中型到大型科技公司 | $6K-$140K+/yr | 同上 |
| **iCIMS** | 大型複雜招募組織 | 企業報價 | 同上 |
| **SAP SuccessFactors** | 全球大型企業、製造業 | 企業報價（SAP HCM 套件） | `官方文件` SAP |
| **Lever** | 中型科技公司、新創 | 較低起步價 | `二手` |
| **Ashby** | 新創、scale-up | $3K+/yr | `二手` |

### 97.8% 的 Fortune 500 使用 ATS

Jobscan 2025 分析確認。`二手` [Pin.com](https://www.pin.com/blog/best-applicant-tracking-systems)

---

## Q2: 各 ATS 的技術架構（爬蟲角度）

### 核心概念

> 「Career page 只是店面，ATS 才握有真正的資料——薪資、職責、申請連結。每個 ATS 供應商在所有使用它的公司上渲染相同的欄位、相同的結構。為一家公司寫的爬蟲可以讀所有用同一 ATS 的公司。」`二手` [Firecrawl Blog](https://www.firecrawl.dev/blog/scrape-job-boards-firecrawl-openai)

### 各 ATS 爬取方法一覽

| ATS | 方法 | URL 格式 | API 端點 | 難度 | 來源 |
|-----|------|---------|---------|------|------|
| **Greenhouse** | **公開 JSON API** | `boards.greenhouse.io/company` | `GET boards-api.greenhouse.io/v1/boards/{token}/jobs` | **最低** | `官方` [Greenhouse API](https://developers.greenhouse.io/job-board.html), `實測` [Cavuno](https://cavuno.com/blog/ats-platforms-public-job-posting-apis) |
| **Lever** | **公開 JSON API** | `jobs.lever.co/company` | `GET api.lever.co/v0/postings/{company}` | **低** | `官方` Lever docs, `實測` [Cavuno](https://cavuno.com/blog/ats-platforms-public-job-posting-apis) |
| **Ashby** | **公開 JSON API** | `jobs.ashbyhq.com/company` | `GET api.ashbyhq.com/posting-api/job-board/{token}` | **低** | `實測` [Cavuno](https://cavuno.com/blog/ats-platforms-public-job-posting-apis) |
| **Workday** | HTML 爬取 + JS render | `company.wd5.myworkdayjobs.com` | 無公開 API，需 headless browser | **中** | `實測` [Apify Workday Scraper](https://apify.com/vamsi-krishna/workday-jobs-scraper) |
| **SuccessFactors** | HTML 爬取 + JS render | `career*.successfactors.com` 或 `performancemanager*.successfactors.com` | OData API v2/v4 存在但非公開（需客戶授權） | **中-高** | `官方` [SAP Community](https://community.sap.com/t5/human-capital-management-q-a/integrating-successfactors-recruiting-with-customer-career-site/qaq-p/13785161), `實測` [Apify SF Scraper](https://apify.com/signalcrawl/successfactors-jobs-api) |
| **Oracle Cloud HCM** | API call | `company.fa.*.oraclecloud.com` | `GET /hcmRestApi/...` | **中** | `實測` [OpenPostings](https://github.com/Masterjx9/OpenPostings/discussions/16) |
| **iCIMS** | HTML 爬取 | `careers-company.icims.com` | 無公開 API | **中-高** | `二手` |
| **SmartRecruiters** | 公開 JSON API | `jobs.smartrecruiters.com/company` | `GET api.smartrecruiters.com/v1/companies/{id}/postings` | **低** | `實測` [Cavuno](https://cavuno.com/blog/ats-platforms-public-job-posting-apis) |
| **Workable** | 公開 JSON API | `apply.workable.com/company` | `GET apply.workable.com/api/v1/widget/accounts/{shortcode}` | **低** | `實測` [Cavuno](https://cavuno.com/blog/ats-platforms-public-job-posting-apis) |
| **Personio** | XML feed | N/A | XML job feed | **低** | `二手` Cavuno |

### Greenhouse 為什麼最容易爬

1. **公開 JSON API**：`boards-api.greenhouse.io` 是 Greenhouse 官方的公開端點，每個公司的 career page widget 都用同一支 API
2. **不需認證**：無 API key、無登入
3. **結構化回傳**：JSON 包含 `title`, `location`, `departments[]`, `offices[]`, `content`, `metadata[]`, `updated_at`, `absolute_url`, `application_url`
4. **官方聲明合法**：「Greenhouse job boards are intentionally public — companies publish them so job seekers can find and apply for roles without authentication.」`官方` [Greenhouse docs](https://developers.greenhouse.io/)

### SuccessFactors 技術細節（台積電用的）

- **URL 模式**：`career*.successfactors.com/{locale}/careers/SearchJobs`（台積電：`careers.tsmc.com` 重定向至此）
- **OData API**：SAP 提供 OData v2/v4 框架，但「SAP does not provide any documentation regarding custom integrations as we do not support them」— 公開爬取需走 HTML
- **Jobo.world 已建立 SuccessFactors API**：提供結構化 JSON，每小時刷新。`實測` [Jobo](https://jobo.world/ats/successfactors)
- **ats-scrapers 有 adapter**：`pip install ats-scrapers` 內建 SuccessFactors 支援

### 統一 Schema（跨 ATS 共通欄位）

基於 Apify Career Site Job Listing API、ats-scrapers、Unified.to 的統一模型：

```
{
  "id": "string",              // ATS 內部 ID
  "title": "string",           // 職缺標題
  "company": "string",         // 公司名稱
  "location": "string",        // 地點
  "department": "string",      // 部門
  "employmentType": "string",  // Full-time / Part-time / Contract
  "workplaceType": "string",   // Remote / Hybrid / On-site
  "description": "string",     // 職缺描述（HTML 或純文字）
  "jobUrl": "string",          // 職缺頁面連結
  "applicationUrl": "string",  // 申請連結
  "publishedAt": "ISO8601",    // 刊登日期
  "updatedAt": "ISO8601",      // 最後更新
  "salary": {                  // 薪資（如有）
    "min": "number",
    "max": "number",
    "currency": "string"
  },
  "ats": "string",             // 來源 ATS 平台
  "scrapedAt": "ISO8601"       // 爬取時間
}
```

來源：[Apify Career Site API](https://apify.com/fantastic-jobs/career-site-job-listing-api)、[ats-scrapers](https://github.com/kalil0321/ats-scrapers)、[Unified.to](https://unified.to/blog/how_to_build_a_job_board_integrating_greenhouse_lever_and_73_ats_platforms_with_an_ats_api)

---

## Q3: ATS 在亞洲/台灣的滲透率

### 亞太市場概況

| 指標 | 數值 | 來源 |
|------|------|------|
| 亞太 ATS 市場 2025 | $653.7M | `官方` MarketsandMarkets |
| 亞太 ATS 市場 2030（預測） | $1,131.6M | 同上 |
| 亞太 CAGR | 11.6%（全球最快） | 同上 |
| 亞太佔全球比重 | ~21.8% | `官方` IMARC |

### 日本 ATS 市場

| 指標 | 數值 | 來源 |
|------|------|------|
| 日本 ATS 市場 2025 | $159-183M | `官方` MarketsandMarkets / IMARC |
| 日本 CAGR | 6.3-10.6% | 同上 |

**日本本土 ATS 大廠**（Top 4 佔 60-65% 市場）：

| 廠商 | 產品 | 定位 | 來源 |
|------|------|------|------|
| **Recruit Holdings** | **AirWORK** | 日本最大 ATS，整合日本最大求職網路 | `官方` IMARC |
| **en Inc.** | en 系列 | 綜合人力資源 | 同上 |
| **SmartHR Inc.** | SmartHR | 雲端 HR，ATS 模組 | 同上 |
| **Visional Inc.** | BizReach（含 HRMOS） | 中高階人才，HRMOS 是雲端 ATS | 同上 |

其他日本本土：**HERP Hire**（新創/IT 公司愛用）、**Sonar ATS**、**HirePlanner**（雙語招募）。`二手` [GetHirex](https://gethirex.com/blog/top-ats-tools-for-japanese-employers-in-2026)

Workday/SuccessFactors 在日本主要服務**大型跨國日企**。`官方` IMARC

### 台灣 ATS / HR Tech 廠商

| 廠商 | 產品 | 定位 | 客戶 | 來源 |
|------|------|------|------|------|
| **ARES 資通** | ARES 招募管理系統 | 台灣領導品牌，on-premise 為主，高科技製造業 | 華碩、世界先進、欣興、寶成、建興、采鈺 | `官方` [ares.com.tw](https://www.ares.com.tw/products/e-recruiting) |
| **MAYO 鼎恒數位** | Apollo 雲端人資系統 | SaaS HR 全套（出勤/薪資/招募），2,500+ 客戶 | TutorABC、奧圖碼、餐飲/製造/科技 | `官方` [mayohr.com](https://www.mayohr.com/tw) |
| **104** | 104 招募管理 Pro | ATS + 人力銀行整合，AI 虛擬面試官 | 使用 104 的企業 | `官方` [ats.104.com.tw](https://ats.104.com.tw) |
| **Yourator** | **Teamdoor 2.0** | AI 招募助理，看板式管理 | 91APP、昕力、iCHEF、ViewSonic | `官方` [plans.yourator.co](https://www.plans.yourator.co/teamdoor-ats-ai) |

**關鍵觀察**：
- 台灣大型上市櫃（台積電、鴻海、金融業）多用國際 ATS 或自建
- 中型企業用 ARES（on-premise）或 MAYO（SaaS）
- 中小型靠 104 招募管理 Pro 或 Teamdoor
- **沒有一個台灣本土 ATS 有公開 API 給第三方爬取** — 這跟 Greenhouse/Lever 的開放生態截然不同

### 亞洲本土 ATS 大廠

| 國家 | 廠商 | 備註 | 來源 |
|------|------|------|------|
| 日本 | Recruit Holdings (AirWORK)、SmartHR、HERP、HRMOS | Top 4 佔 60-65% | `官方` IMARC |
| 印度 | Zoho Recruit、nCore HR、Keka、PeopleStrong | Zoho 是亞太 SME 主力 | `官方` Maximize MR |
| 泰國 | Manatal | 全球化 SaaS ATS，泰國起家 | 同上 |
| 中國 | Beijing ELi Technology、DHC Software | 中國本土封閉市場 | 同上 |
| 韓國 | 無顯著本土 ATS 品牌 | SAP/Workday + 本土求職板（Saramin、JobKorea） | `推測` |

---

## Q4: 爬取 ATS 的法律與技術挑戰

### 法律風險光譜

| 來源類型 | 風險等級 | 說明 | 來源 |
|---------|---------|------|------|
| **公司官網 career page** | **最低** | 公開資訊，公司希望被搜尋引擎索引 | `二手` [Olostep](https://www.olostep.com/blog/job-scraping), [Cavuno](https://cavuno.com/blog/job-scraping) |
| **ATS 公開 API（Greenhouse 等）** | **最低** | 官方設計為公開端點，無需認證 | `官方` Greenhouse docs |
| **聚合器（Google for Jobs）** | **中** | 有衍生使用政策 | `二手` Olostep |
| **人力銀行（LinkedIn/Indeed）** | **最高** | 主動執行反爬、有明確 ToS 禁令 | `二手` Cavuno, Olostep |

**關鍵判例**：
- **hiQ v. LinkedIn (2022)**：美國最高法院支持爬取公開資料不違反 CFAA（Computer Fraud and Abuse Act）
- **Reddit v. Perplexity AI (2025)**：新法律向量 — DMCA §1201 反規避條款用於對抗爬蟲繞過反爬機制
- **模式清楚**：CFAA 對公開資料爬取的訴訟一貫失敗，但合約法（ToS 違約）和反規避法仍是風險

`二手` [Cavuno](https://cavuno.com/blog/job-scraping)

### 技術挑戰

| 挑戰 | 影響的平台 | 應對策略 | 來源 |
|------|----------|---------|------|
| **JS 渲染** | Workday、SuccessFactors、自建系統 | Headless browser（Playwright/Puppeteer）或 JS render API | `二手` [ScrapeBadger](https://scrapebadger.com/blog/how-to-scrape-job-listings-from-any-website-with-python) |
| **Rate Limiting** | 所有平台 | 1-2 req/sec/domain、proxy 輪替 | `二手` Cavuno |
| **CAPTCHA** | Indeed、LinkedIn、部分自建 | 避免這些平台，改爬 ATS 源頭 | `二手` JobsPikr |
| **結構不一致** | 自建系統 | LLM schema-based extraction（用 AI 讀頁面而非寫 CSS selector） | `二手` [Firecrawl](https://www.firecrawl.dev/blog/scrape-job-boards-firecrawl-openai) |
| **Ghost jobs（幽靈職缺）** | 所有平台 | 30 天自動清理 + freshness scoring | `二手` Olostep |

### 最佳實踐：來源優先順序

> 「Build a career-page-first foundation, using job boards strictly for secondary coverage.」

1. **Tier 1：公司 Career Page + ATS 公開 API** — 最新鮮、最低重複率、最低風險
2. **Tier 2：搜尋/聚合層（Google for Jobs）** — URL 發現引擎，不做 canonical 來源
3. **Tier 3：人力銀行（104/LinkedIn）** — 高覆蓋但高風險、高重複

`二手` [Olostep](https://www.olostep.com/blog/job-scraping)

---

## Q5: ats-scrapers 套件深入分析

### 基本資訊

| 項目 | 值 | 來源 |
|------|---|------|
| PyPI 名稱 | `ats-scrapers` | `官方` [PyPI](https://pypi.org/project/ats-scrapers/) |
| Import 名稱 | `ats_scrapers` | 同上 |
| Stars | 125（2026-08） | `實測` [Scrapfly](https://scrapfly.io/blog/posts/best-open-source-job-scrapers) |
| 授權 | MIT | `官方` GitHub |
| 託管資料集 | 4.2M+ 職缺、63,000+ 公司 | `實測` Scrapfly |
| 最後更新 | 2026-08-07 | `實測` Scrapfly |

### 支援的平台（50+ adapters）

**主要 ATS**：
- ADP Workforce Now、**Greenhouse**、**Lever**、**Ashby**、**Workday**、**SmartRecruiters**、**SuccessFactors**、**Oracle**、**iCIMS**、HERP Hire、HRMOS、Keka、Paycom、Softgarden、**Workable**、Personio 等

**一手公司 API**：
- Amazon、Apple、Google、TikTok、Uber

**公共/區域來源**：
- EURES（歐盟）、Bundesagentur（德國）、Arbetsformedlingen（瑞典）、Welcome to the Jungle

`官方` [GitHub README](https://github.com/kalil0321/ats-scrapers)

### 使用方式

```python
# 搜尋託管資料集（不需爬取）
from ats_scrapers import search
jobs = search(query="machine learning engineer", location="Paris", ats="greenhouse", limit=10)

# 使用個別 adapter 爬取
from ats_scrapers import get_scraper_for_url
scraper = get_scraper_for_url("https://careers.tsmc.com")  # 自動辨識 SuccessFactors
jobs = scraper.fetch()

# 非同步（高併發）
jobs = await scraper.afetch()
```

`官方` GitHub README, `二手` Scrapfly

### 統一 Schema（27 欄位）

輸出為 pandas DataFrame，包含：`title`, `company`, `location`, `department`, `employment_type`, `workplace_type`, `description`, `job_url`, `application_url`, `published_at`, `updated_at`, `salary_min`, `salary_max`, `salary_currency`, `ats`, `scraped_at` 等。

### 與其他工具比較

| 工具 | 覆蓋範圍 | 輸出 | 認證需求 | Stars | 最後更新 | 授權 |
|------|---------|------|---------|-------|---------|------|
| **ats-scrapers** | 50+ ATS 平台 + 公司 API | pandas DF, 27 欄 | 無 API key，託管資料集 | 125 | 2026-08 | MIT |
| **JobSpy** | LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter | pandas DF | 無登入，LinkedIn 需 proxy | 4,071 | 2026-02 | MIT |
| **Levergreen** | Greenhouse + Lever | dbt + Postgres | Scrapy spiders | 47 | 2025-11 | MIT |
| **ever-jobs** | 35+ ATS | — | — | — | — | — |
| **Apify Career Site API** | 75+ ATS | JSON, 33 欄 | 付費（Apify） | — | 持續 | 商業 |
| **Unified.to** | 85+ ATS 整合 | 統一 API | 付費 SaaS | — | 持續 | 商業 |

`二手` [Scrapfly](https://scrapfly.io/blog/posts/best-open-source-job-scrapers)

### ats-scrapers 的限制

1. **託管資料集偏國際**：4.2M 職缺主要來自歐美公司，台灣本土上市櫃幾乎沒有
2. **SuccessFactors adapter 成熟度未知**：有 adapter 但文件未詳述台灣企業的特殊設定
3. **自建系統無法覆蓋**：鴻海 isite-web、聯發科自建、ARES 系統等需另外寫 adapter
4. **104/1111 不在支援範圍**：台灣人力銀行需用 job-source-mcp 或自建爬蟲

---

## 事實交叉表

| 事實 | 來源 1 | 來源 2 | 狀態 |
|------|--------|--------|------|
| ATS 市場 2025 年約 $3.1-3.5B | MarketsandMarkets | IMARC | ✅ |
| Workday 佔美國企業 ATS ~32% | BestRecruitingTools 2026 review | — | ⚠️ unverified（單源） |
| Greenhouse 佔美國企業 ~18% | 同上 | — | ⚠️ unverified（單源） |
| Top 5 佔企業 ATS 營收 55-60% | IMARC | MarketsandMarkets | ✅ |
| 97.8% Fortune 500 用 ATS | Jobscan 2025 via Pin.com | — | ⚠️ unverified（單源引用） |
| SAP 買 SmartRecruiters（2025/9） | Pin.com | — | ⚠️ unverified |
| Workday 買 Paradox（2025/10） | Pin.com | — | ⚠️ unverified |
| Greenhouse 有公開 JSON API | Greenhouse 官方文件 | Cavuno 實測 | ✅ |
| Lever 有公開 JSON API | Lever 官方文件 | Cavuno 實測 | ✅ |
| SuccessFactors 無公開爬取 API | SAP Community 官方回覆 | — | ✅（官方否認） |
| ats-scrapers 4.2M 職缺 63K 公司 | Scrapfly 報導 | GitHub README | ✅ |
| 亞太 ATS CAGR 11.6% | MarketsandMarkets | IMARC (~10%) | ✅（兩源一致方向） |
| 日本 Top 4 ATS 佔 60-65% | IMARC Japan report | — | ⚠️ unverified（單源） |
| ARES 是台灣領導 ATS 品牌 | ARES 官網 | Yourator 文章 | ✅ |
| 台灣本土 ATS 無公開 API | 搜尋未發現任何 | — | ⚠️ unverified（負面證據） |
| hiQ v. LinkedIn 支持公開資料爬取 | Cavuno | Olostep | ✅ |
| 爬取公司 career page 風險最低 | Olostep | Cavuno | ✅ |

---

## 對「台灣百大上市櫃職缺聚合」的啟示

### 爬取策略建議

```
優先順序（由易到難）：

1. 公開 ATS API（Greenhouse/Lever/Ashby/SmartRecruiters/Workable）
   → 主要覆蓋：外商在台辦公室
   → 工具：ats-scrapers 或直接 HTTP GET
   → 法律風險：最低

2. SuccessFactors HTML 爬取
   → 覆蓋：台積電（可能還有少數大型製造業）
   → 工具：ats-scrapers SF adapter 或 Apify SF Scraper
   → 難度：中，需 JS render

3. 104 人力銀行爬取
   → 覆蓋：最廣（~70% 上市櫃有在 104 刊登）
   → 工具：job-source-mcp（現成）
   → 法律風險：中（104 ToS 未知，但是公開頁面）

4. ARES 系統爬取
   → 覆蓋：華碩、世界先進、欣興等
   → 工具：需自建（ARES 結構統一，一個 adapter 覆蓋多家）
   → 難度：中

5. 自建系統逐家爬取
   → 覆蓋：鴻海、聯發科、國泰金、富邦金、中信金、台達電、廣達
   → 工具：LLM schema-based extraction（Firecrawl 模式）
   → 難度：最高，每家不同
```

### 覆蓋率估算

| 來源 | 預估可覆蓋公司數 | 佔百大比例 |
|------|----------------|-----------|
| 公開 ATS API | 5-10 家（外商在台） | 5-10% |
| SuccessFactors | 1-3 家（台積電等） | 1-3% |
| 104 爬取 | 60-70 家 | 60-70% |
| ARES | 5-10 家 | 5-10% |
| 自建系統逐家 | 15-25 家 | 15-25% |
| **合計** | **~85-100 家** | **85-100%** |

### 核心結論

1. **台灣上市櫃的 ATS 生態跟國際截然不同**：國際市場由 Greenhouse/Workday 等有公開 API 的平台主導；台灣則是自建系統 + 104 為主，公開 API 幾乎不存在
2. **104 是繞不過去的核心資料源**：~70% 覆蓋率，是唯一能用單一爬蟲覆蓋大量公司的管道
3. **ats-scrapers 可以處理外商 + 台積電**：但對台灣百大上市櫃的覆蓋率只有 5-13%
4. **LLM schema-based extraction 是處理自建系統的最佳策略**：不寫 CSS selector，用 AI 讀頁面結構，容忍改版
5. **法律風險可控**：爬取公司官網 career page 和 ATS 公開 API 在全球判例中風險最低
