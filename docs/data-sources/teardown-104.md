# Service Teardown: 104 人力銀行

> 拆解日期：2026-09-10
> 目標：104.com.tw
> 要回答的問題：上市櫃篩選的 API 結構？薪資排行資料怎麼取？職缺搜尋 API schema？
> 對照目標：作為台灣百大上市櫃職缺聚合的主要資料來源

---

## L1 — UI 層

### 找公司（上市櫃篩選）
- URL：`/company/search?zone=16`
- 頁面標題：「找上市上櫃相關徵才公司、企業｜104找公司」
- 快捷標籤列：供住宿 / 中高齡友善 / 外商徵才中 / 上市櫃免經驗 / **百萬年薪企業**
- 三個搜尋模式切換：AI推薦 / 找工作 / 找公司

### 薪資排行頁
- URL：`/company/salary/top`
- 頁面標題：「上市櫃公司薪資中位數排行｜年薪百萬企業公開」
- 資料來源標註：證交所公開資訊觀測站

`實測`

---

## L3 — 網路層（核心 API）

### 三大核心 API

#### 1. 公司列表 API

```
GET /company/ajax/list?zone=16&features=1&pageSize=18
```

**Response schema：**

```json
{
  "data": [{ /* 公司物件 */ }],
  "metadata": {
    "pagination": {
      "count": 18,
      "total": 1280,       // ← 上市櫃公司總數
      "currentPage": 1,
      "lastPage": 72
    }
  }
}
```

**公司物件欄位：**

| 欄位 | 範例值 | 說明 |
|------|--------|------|
| `encodedCustNo` | `auxx12g` | 104 內部公司 ID（URL 用） |
| `name` | `華碩電腦股份有限公司` | 公司全名 |
| `areaDesc` | `台北市北投區` | 公司所在地 |
| `logo` | `https://static.104.com.tw/...` | 公司 logo |
| `industryNo` | `1001003001` | 產業代碼 |
| `industryDesc` | `電腦及其週邊設備製造業` | 產業名稱 |
| `capitalDesc` | `資本額370億` | 資本額 |
| `employeeCountDesc` | `員工數暫不提供` | 員工數 |
| `profile` | （長字串） | 公司簡介 |
| `jobCount` | `607` | **104 上的職缺數** |
| `mainScore` | `4.5` | 公司評分 |
| `tagNames` | `["員工認股", "三節獎金", ...]` | 福利標籤 |
| `jobCats` | `[{no, role, desc}, ...]` | 主要職缺類別 |
| `labels` | `["foreigners@...", "digital_talent@..."]` | 系統標籤 |
| `zone` | `{"上市櫃": "..."}` | zone 篩選標記 |

`實測` — API response 直接擷取

#### 2. 薪資排行 API

```
GET /company/ajax/salary/top100
```

**Response：155 家公司的薪資資料**

| 欄位 | 範例值 | 說明 |
|------|--------|------|
| `exchangeId` | `5274` | **股票代號**（可串 TWSE API！） |
| `encodedCustNo` | `cmna4ww` | 104 內部公司 ID |
| `name` | `信驊科技股份有限公司` | 公司全名 |
| `nickName` | `信驊` | 簡稱 |
| `logo` | URL | 公司 logo |
| `isAlwaysOn` | `true` | 是否持續刊登 |
| `jobCount` | `31` | 104 上的職缺數 |
| `industryCode` | `1` | 產業代碼 |
| `industryMean` | `258` | 產業平均薪資（萬） |
| `mean` | `593.4` | 全員工平均年薪（萬） |
| `meanNonSupervisor` | `561.7` | 非主管平均年薪（萬） |
| `medianNonSupervisor` | `453.7` | **非主管年薪中位數（萬）** |

**關鍵發現**：`exchangeId` 是股票代號，可以直接串 TWSE OpenAPI！

**其他薪資端點**：
- `GET /company/ajax/salary/top3` — TOP 3 公司
- `GET /company/ajax/salary/industry/codeMap` — 產業代碼對照表

`實測` — API response 直接擷取

#### 3. 職缺搜尋 API

```
GET /jobs/search/api/jobs?keyword=software%20engineer&order=15&pagesize=20&zone=16
```

**Response：22 筆職缺（JSON array）**

| 欄位 | 範例值 | 說明 |
|------|--------|------|
| `jobNo` | `6320428` | 職缺編號 |
| `jobName` | `資深/技術支援工程師 Technical Support Engineer` | 職缺標題 |
| `custName` | `普安科技股份有限公司` | 公司名稱 |
| `custNo` | `84166074000` | 公司統編 |
| `custLogo` | URL | 公司 logo |
| `coIndustryDesc` | `電腦系統整合服務業` | 產業 |
| `description` | （長字串） | 職缺描述 |
| `descSnippet` | （帶 highlight） | 搜尋結果摘要 |
| `jobNameSnippet` | `...[[[Engineer]]]` | 標題 highlight |
| `jobAddrNoDesc` | `新北市中和區` | 工作地點 |
| `jobAddress` | `中山路三段102號8樓` | 詳細地址 |
| `lat` / `lon` | `25.005` / `121.477` | GPS 座標 |
| `salaryHigh` / `salaryLow` | `0` / `0` | 薪資範圍（0=面議） |
| `appearDate` | `20260908` | 刊登日期 |
| `jobType` | `1` | 工作類型 |
| `optionEdu` | `[4, 5, 6]` | 學歷要求 |
| `major` | `["資訊工程相關", ...]` | 科系要求 |
| `employeeCount` | `450` | 公司員工數 |
| `tags` | `{"zone": {"desc": "上市上櫃", "param": 16}}` | **zone=16 就是上市櫃標記** |
| `jobCat` | `[2010002002, ...]` | 職務類別代碼 |
| `labels` | `["foreigners@...", ...]` | 系統標籤 |
| `languageRequirements` | `[{language, ability}]` | 語言要求 |
| `link` | `{"job": "...", "cust": "..."}` | 職缺/公司頁面連結 |
| `interactionRecord` | `{lastProcessedResumeDesc, ...}` | HR 回應速度 |
| `hasHrBehavior` | `true` | HR 是否活躍 |

`實測` — API response 直接擷取

### 輔助 API

| 端點 | 用途 |
|------|------|
| `GET /company/ajax/list/menu` | 篩選選單（產業/地區/zone 等） |
| `GET /jobs/search/ajax/function-tree/industry` | 產業分類樹 |
| `GET /jobs/search/ajax/function-tree/area` | 地區分類樹 |
| `GET /jobs/main/ajax/KeywordSuggest/mixSearch?kw=...` | 關鍵字建議 |
| `GET /api/companies/{id}/similar` | 相似公司推薦 |

### 需登入的 API（401 Unauthorized）

| 端點 | 用途 |
|------|------|
| `GET /api/user/resumes` | 使用者履歷 |
| `GET /jobs/search/api/recommend-job-filters` | AI 推薦篩選 |
| `GET /api/tag-service/tags-exist` | A/B test 標籤 |
| `POST /api/digital-talent/personal-tags/intersection` | 個人標籤比對 |

`實測`

---

## L4 — 資料結構關鍵發現

### zone 參數對照

```
zone=16  → 上市上櫃
zone=4,5 → 外商（從「外商徵才中」連結反推）
```

### 公司 ID 串接鏈

```
104 encodedCustNo (auxx12g)
    ↕ 可透過薪資 API 取得
exchangeId (股票代號, e.g. 5274)
    ↕ 可串接
TWSE OpenAPI (公司基本資料/股價/營收)
    ↕ 可串接
MOPS (薪資中位數)
```

**這是最大的技術發現**：104 薪資 API 的 `exchangeId` 直接就是股票代號，完美串接 TWSE OpenAPI。

### 職缺去重策略

104 的 `custNo`（公司統編）可以跟公司官網職缺做去重配對：
- 同公司統編 + 相似職缺標題 → 判斷為同一職缺
- 104 有 `description` 全文，可以用 LLM 做語意比對

`推測`

---

## L5 — 邊界層

### 已觀察到的限制
- **大量 GA / 廣告追蹤**：Google Analytics (3 個 TID)、Google Ads (2 個 AW ID)、Emarsys、Scarab Research — 104 重度依賴廣告營收
- **未登入可用搜尋 API**：公司列表、職缺搜尋、薪資排行都不需登入
- **無明顯 rate limiting**：在正常瀏覽中未觸發任何阻擋（但爬蟲可能會）
- **搜尋結果每頁 20 筆**：有分頁，可用 `pagesize` 和 `page` 參數
- **zone=16 上市櫃共 1,280 家公司**：確認數字

### 法律風險評估
- 104 的 robots.txt 和 ToS 可能限制自動化爬取
- **建議策略**：用已有的開源 `job-source-mcp` 而非直接爬，或先確認 ToS

---

## L6 — 對照分析（作為資料來源的可行性）

### 104 作為主要資料來源的優勢

| 面向 | 評估 |
|------|------|
| **覆蓋率** | ⭐⭐⭐⭐ 1,280/1,800+ 家上市櫃（~70%） |
| **API 品質** | ⭐⭐⭐⭐⭐ 完整結構化 JSON，schema 清晰 |
| **薪資資料** | ⭐⭐⭐⭐⭐ 直接有股票代號 + 非主管中位數，可串 TWSE |
| **職缺詳情** | ⭐⭐⭐⭐ 完整 JD + 地點 + 薪資 + 學歷 + 語言要求 |
| **更新頻率** | ⭐⭐⭐⭐ 企業自行更新，通常即時 |
| **法律風險** | ⚠️ 需確認 ToS，建議用間接方式 |

### 建議的資料管線

```
第一層（核心覆蓋，~70%）：
  104 /company/ajax/list?zone=16  →  取得 1,280 家上市櫃公司
  104 /jobs/search/api/jobs?zone=16&keyword=...  →  各公司職缺
  104 /company/ajax/salary/top100  →  薪資中位數 + 股票代號

第二層（串接公開資料）：
  exchangeId → TWSE OpenAPI  →  市值、營收、產業分類
  exchangeId → MOPS  →  完整薪資揭露（更多公司、更多欄位）

第三層（補齊缺口，~30%）：
  未在 104 刊登的上市櫃公司 → 爬官網（ats-scrapers）
  同一職缺跨平台 → 用 custNo + 職缺標題做去重
```

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | 上市櫃篩選 UI | Playwright snapshot |
| L1 | 薪資排行頁 UI | Playwright snapshot |
| L3 | 公司列表 API schema（zone=16） | API response 擷取 |
| L3 | 薪資排行 API schema（top100） | API response 擷取 |
| L3 | 職缺搜尋 API schema | API response 擷取 |
| L3 | 輔助 API 盤點 | Network requests |
| L4 | 公司 ID 串接鏈（encodedCustNo → exchangeId → TWSE） | 資料分析 |
| L5 | 登入限制、追蹤系統 | 觀察 |
| L6 | 資料來源可行性評估 | 分析 |

## 待深入項目

| 項目 | 需要條件 | 說明 |
|------|---------|------|
| 職缺詳情 API | 單一職缺 URL 的 API | 看 /job/{id} 的完整 response |
| robots.txt / ToS 分析 | 讀取 robots.txt | 確認爬取合規性 |
| Rate limiting 測試 | 批量請求 | 確認頻率限制 |
| 分頁完整性 | 跑完 72 頁 | 確認 1,280 家都能取得 |

## 沒拿到的

- 單一職缺詳情頁的 API response（本輪只看搜尋結果）
- robots.txt 的限制內容
- 實際 rate limiting 門檻
- 需登入的 API 的 response schema（AI 推薦、個人化功能）

## 殘留清單

無

---

## 原始擷取路徑

- `.playwright-mcp/104-company-search-snapshot.md`
- `.playwright-mcp/104-company-search-network.md`
- `.playwright-mcp/104-company-list-api-response.json`（公司列表 API）
- `.playwright-mcp/104-salary-network.md`
- `.playwright-mcp/104-salary-top100-response.json`（薪資排行 API）
- `.playwright-mcp/104-job-search-network.md`
- `.playwright-mcp/104-job-search-api-response.json`（職缺搜尋 API）
