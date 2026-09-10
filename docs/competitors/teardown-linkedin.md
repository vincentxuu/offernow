# Service Teardown: LinkedIn 台灣職缺

> 拆解日期：2026-09-10
> 目標：linkedin.com/jobs
> 要回答的問題：台灣上市櫃公司的 LinkedIn 職缺量？Guest API 結構？跟 104 的覆蓋差異？
> 對照目標：作為第二資料來源

---

## L1 — UI 層

### 公開搜尋頁（Guest，不需登入）
- URL 格式：`/jobs/search/?keywords=...&location=Taiwan`
- 篩選器（Guest 版精簡）：Date posted / Company / Easy Apply / Under 10 applicants
- 更多篩選需登入才能展開
- 每頁約 50 筆職缺

### 職缺卡片結構
- 職缺標題（如 Software Developer）
- 公司名稱 + 連結到公司頁面
- 地點（如 Taichung City, Taiwan）
- 時間（如 2 weeks ago）
- 申請人數提示（如 Be among the first 25 applicants）
- 點擊展開 → 完整 JD 在右側面板

`實測`

---

## L2 — 台灣上市櫃公司職缺量

| 公司 | LinkedIn 職缺 | 搜尋關鍵字 |
|------|-------------|-----------|
| **鴻海** | **11,000+** | 鴻海 |
| **台積電** | **7,000+** | TSMC |
| **聯發科** | **4,000+** | MediaTek |
| **Software Engineer (Taiwan)** | **2,000+** | software engineer |
| **國泰金控** | **1,000+** | 國泰金控 |

**注意**：LinkedIn 的數字可能包含子公司、關聯公司和已過期未下架的職缺。實際有效職缺需要篩選。但即便打折，LinkedIn 的台灣上市櫃職缺量仍然遠超 104。

**意義**：LinkedIn 不是「台灣資料稀疏」— 至少在大型上市櫃公司，LinkedIn 的職缺覆蓋率可能比 104 更高（因為不需企業付費上架）。

`實測`

---

## L3 — 網路層

### Guest API（不需登入）

```
GET /jobs-guest/jobs/api/jobPosting/{jobId}
```

- **不需驗證**即可打
- Response 是 **HTML fragment**（不是 JSON）
- 包含：職缺標題、公司名、地點、時間、申請人數、完整 JD
- URL 中有 `refId` 和 `trackingId` 追蹤參數

### 其他 API

| 端點 | 用途 |
|------|------|
| `GET /litms/api/metadata/user` | 用戶元資料 |
| `POST /jobs-guest/api/ingraphs/gauge` | 監控指標 |
| `POST /jobs-guest/api/ingraphs/counter` | 計數器 |
| `POST /litms/api/events/ext-tag-load` | 事件追蹤 |
| `POST /litms/api/events/tms-load` | 標籤管理 |

### 技術觀察
- **SSR（Server-Side Rendering）**：職缺列表在伺服器端渲染（SEO 友善）
- **Tealium** 標籤管理 + Google Ads/DoubleClick + Protechts.net 反作弊
- **大量廣告追蹤**：Google Remarketing、DoubleClick Activity 等
- **搜尋結果 URL 支援 company ID 篩選**：`f_C={companyId}`

`實測`

---

## L4 — 爬取可行性

### 優勢
- **Guest API 存在**：`/jobs-guest/jobs/api/jobPosting/{id}` 不需登入
- **搜尋結果 SSR**：HTML 可直接 parse，不需 JS rendering
- **JobSpy 已驗證**（4.3K stars）：`scrape_jobs("software engineer", site_name="linkedin")` 一行搞定
- **job-source-mcp 也有 LinkedIn adapter**

### 風險
- **反爬強**：LinkedIn 積極反爬，rate limit 嚴格
- **hiQ v. LinkedIn 判例雖支持公開資料爬取**，但 LinkedIn 持續在技術和法律上對抗
- **Guest 搜尋結果有限**：未登入只能看到部分結果，完整搜尋需登入
- **Company ID 不等於股票代號**：需要建立 LinkedIn companyId ↔ 股票代號的 mapping

### 建議策略

```
優先度：LinkedIn 作為第二來源（104 是第一）

策略 1（低風險）：
  用 job-source-mcp 的 LinkedIn adapter
  → 已有人維護，爬取頻率適中

策略 2（中風險）：
  用 JobSpy 批量爬取
  → 一行程式碼，但需注意 rate limit

策略 3（零風險）：
  不直接爬 LinkedIn，而是從公司官網爬
  → 很多上市櫃公司的官網職缺跟 LinkedIn 同步
  → 繞過 LinkedIn 反爬，直接從源頭拿
```

---

## L5 — LinkedIn vs 104 覆蓋比較

| 面向 | LinkedIn | 104 |
|------|----------|-----|
| **台灣上市櫃公司職缺量** | 極多（鴻海 11K、台積電 7K） | 中等（zone=16 共 1,280 家） |
| **企業上架成本** | 免費 | 付費（$4,200/月起） |
| **資料結構** | HTML fragment（Guest API） | JSON（結構化 API） |
| **爬取難度** | 高（反爬嚴格） | 中（無明顯反爬） |
| **法律風險** | 中-高 | 中 |
| **薪資資料** | 無（或極少） | 有（串 MOPS） |
| **搜尋篩選** | Guest 版精簡、需登入完整 | 完整（zone/產業/地區） |
| **職缺品質** | 可能含子公司/過期 | 企業主動管理 |
| **獨特價值** | 覆蓋率高、國際公司多 | 結構化 API、薪資串接 |

### 結論

**LinkedIn 是不可忽略的第二來源**，但策略不同於 104：
- **104**：結構化 API，直接爬，作為主要來源
- **LinkedIn**：覆蓋率高但爬取難，作為補充來源，優先用已有開源工具（job-source-mcp / JobSpy）

---

## L6 — 對照分析

### LinkedIn 在我們產品中的角色

| 用途 | 說明 |
|------|------|
| **補齊 104 缺口** | 未在 104 刊登的上市櫃公司，LinkedIn 可能有 |
| **跨來源去重** | 同一職缺出現在 LinkedIn + 104 → 去重並標記來源 |
| **國際公司覆蓋** | 台灣有辦公室的外商在 LinkedIn 刊登更完整 |
| **職缺量異常偵測** | LinkedIn 職缺暴增/暴減可能是擴編/裁員信號 |

### Company ID Mapping 問題

LinkedIn 用自己的 `companyId`（如 `f_C=1940`），不是股票代號。需要建立 mapping：

```
方案 1：手動建立百大上市櫃的 LinkedIn companyId
方案 2：用公司名稱搜尋 LinkedIn company page，爬取 companyId
方案 3：用 LinkedIn 的 Company Search API（需 OAuth）
```

對 1,800+ 家上市櫃公司，方案 2 最務實（一次性爬取建立 mapping table）。

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | Guest 搜尋 UI 結構 | Playwright snapshot |
| L2 | 台灣上市櫃公司職缺量抽樣 | 搜尋實測 |
| L3 | Guest API 端點 + response 格式 | Network requests |
| L4 | 爬取可行性評估 | 分析 |
| L5 | LinkedIn vs 104 覆蓋比較 | 分析 |
| L6 | 產品角色定位 | 分析 |

## 沒拿到的

- Guest API 的 rate limit 門檻
- LinkedIn companyId ↔ 股票代號的完整 mapping
- 登入後的完整搜尋 API（Voyager API）
- 職缺數量的準確性（是否含子公司/過期）

## 殘留清單

無

---

## 原始擷取路徑

- `.playwright-mcp/linkedin-search-snapshot.md`
- `.playwright-mcp/linkedin-search-network.md`
- `.playwright-mcp/linkedin-job-api-response.html`
