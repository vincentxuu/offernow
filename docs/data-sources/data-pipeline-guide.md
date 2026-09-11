# OfferNow 資料管線操作指南

> 更新日期：2026-09-10

## 資料來源總覽

| # | 資料來源 | 端點 | 認證 | 更新頻率 | 腳本 |
|---|---------|------|------|---------|------|
| 1 | TWSE 上市公司基本資料 | `openapi.twse.com.tw/v1/opendata/t187ap03_L` | 免費免 key | 即時 | `fetch-companies.py` |
| 2 | TPEx 上櫃公司基本資料 | `tpex.org.tw/openapi/v1/mopsfin_t187ap03_O` | 免費免 key | 即時 | `fetch-companies.py` |
| 3 | TWSE 月營收 | `openapi.twse.com.tw/v1/opendata/t187ap05_L` | 免費免 key | 每月 10 號 | `fetch-companies.py` |
| 4 | TPEx 月營收 | `tpex.org.tw/openapi/v1/mopsfin_t187ap05_O` | 免費免 key | 每月 10 號 | `fetch-companies.py` |
| 5 | TWSE 每日收盤 | `openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` | 免費免 key | 每日 | `fetch-companies.py` |
| 6 | TPEx 每日收盤 | `tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes` | 免費免 key | 每日 | `fetch-companies.py` |
| 7 | MOPS 薪資揭露（31 欄） | `POST mopsov.twse.com.tw/mops/web/ajax_t100sb15` | 免費免 key | 每年 6 月底 | `fetch-mops-full.py` |
| 8 | 104 公司列表 + 職缺 | `104.com.tw/company/ajax/list` + `/jobs/search/api/jobs` | **需 Cloudflare cookie** | 即時 | `fetch-104-playwright.py` |
| 9 | LinkedIn 職缺 | JobSpy 或 Guest API | **有反爬限制** | 即時 | `fetch-jobs.py` |

## 重要注意事項

### 104 — 需要 Playwright 拿 cookie

**104 的 API 存在且完整**，但直接用 curl/requests 會被 Cloudflare 擋（403）。

正確流程：
```
1. Playwright 開瀏覽器 → 訪問 104.com.tw → 通過 Cloudflare challenge
2. 從瀏覽器拿到 cookie（cf_clearance 等）
3. 用拿到的 cookie + requests 打 104 API
4. API 端點跟 teardown 驗證過的一模一樣
```

**不是 API 不能用，是需要先過 Cloudflare 的門。**

API 端點：
- 公司列表：`GET /company/ajax/list?zone=16&features=1&pageSize=100&page={n}`
- 薪資排行：`GET /company/ajax/salary/top100`
- 職缺搜尋：`GET /jobs/search/api/jobs?keyword=&order=15&pagesize=100&zone=16&page={n}`
- 關鍵字建議：`GET /jobs/main/ajax/KeywordSuggest/mixSearch?kw=...`

### TPEx — SSL 憑證問題

TPEx（櫃買中心）的 SSL 憑證缺 Subject Key Identifier，Python 的 urllib 會報 `CERTIFICATE_VERIFY_FAILED`。

解法：
```python
import ssl
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# 只對 tpex.org.tw 用寬鬆的 SSL context
ctx = _ssl_ctx if "tpex.org.tw" in url else None
with urlopen(req, timeout=30, context=ctx) as resp: ...
```

### TWSE vs TPEx 欄位名差異

同一個資料，TWSE 用中文欄位名，TPEx 用英文欄位名：

| 資料 | TWSE 欄位 | TPEx 欄位 |
|------|----------|----------|
| 公司代號 | `公司代號` | `SecuritiesCompanyCode` |
| 公司名稱 | `公司名稱` | `CompanyName` |
| 產業 | `產業別` | `IndustryCategory` |
| 已發行股數 | `已發行普通股數或TDR原股發行股數` | `IssuedShares` |

**程式碼裡需要對兩套 API 分別處理欄位名。**

### 日期格式 — 民國年

所有證交所/櫃買的日期都是民國年：
- `1150909` = 2026-09-09
- `19870221` = 成立日期（已是西元年格式，8 碼）
- 營收期間 `11408` = 114 年 8 月

### MOPS — POST 表單，非 JSON

MOPS 薪資揭露不是 REST API，是 POST 表單回傳 HTML table：

```python
data = urlencode({
    "encodeURIComponent": 1,
    "step": 1,
    "firstin": 1,
    "TYPEK": "sii",  # sii=上市, otc=上櫃
    "RYEAR": 114,     # 民國年
    "code": "",       # 空白=全部產業
}).encode()

resp = urlopen(Request(url, data=data, headers=...))
# resp 是 HTML，需要 parse table
```

### LinkedIn — 關鍵字搜尋有大量雜訊

JobSpy 用關鍵字搜尋，搜「Aspeed Technology」會回傳 JD 裡提到 Aspeed 的其他公司職缺（如 Lenovo）。

**RapidFuzz 過濾後 187 → 26 筆（86% 是雜訊）。**

長期解法：
1. 建立 LinkedIn Company ID mapping（stock_id → f_C 參數）
2. 用 `f_C={companyId}` 做精確公司搜尋
3. 或改用 ats-scrapers 直接爬公司官網

### 市值計算

```
市值（億）= 收盤價 × 已發行股數 / 100,000,000
```

- 上市公司：TWSE 基本資料有 `已發行普通股數`，收盤價從 `STOCK_DAY_ALL` 取
- 上櫃公司：TPEx 基本資料的股數欄位不一定有，部分公司缺市值

### 串接 Key

**所有資料源用同一個 key 串接：股票代號**

```
TWSE 公司代號 (2330)
= TPEx SecuritiesCompanyCode (5274)
= MOPS 公司代號 (2330)
= 104 exchangeId (2330)（薪資 API 回傳）
```

104 另有 `encodedCustNo`（如 `auxx12g`），用於公司頁面 URL。

## 腳本執行順序

```bash
# 1. 抓取所有公開資料（TWSE + TPEx + MOPS）
python3 scripts/fetch-companies.py

# 2. 抓取 MOPS 完整 31 欄位（性別薪資、旗標、自述）
python3 scripts/fetch-mops-full.py

# 3. 抓取 104 職缺（需要 Playwright）
python3 scripts/fetch-104-playwright.py

# 4. 抓取 LinkedIn/Indeed 職缺
python3 scripts/fetch-jobs.py

# 5. 過濾 LinkedIn 雜訊
python3 scripts/filter-jobs.py

# 6. 生成 AI 洞察（需要 API key）
OPENROUTER_API_KEY=sk-or-... npx tsx scripts/generate-insights.ts

# 7. 重新 seed D1
python3 scripts/db/seed.py
pnpm wrangler d1 execute offernow-db --local --file scripts/db/seed.sql
pnpm wrangler d1 execute offernow-db --remote --file scripts/db/seed.sql

# 8. 部署
pnpm run deploy
```

## 資料檔案

| 檔案 | 內容 | 大小 |
|------|------|------|
| `scripts/data/companies.json` | 公司基本資料（TWSE + TPEx） | ~800K |
| `scripts/data/salaries.json` | MOPS 薪資（基本欄位） | ~720K |
| `scripts/data/mops_full.json` | MOPS 完整 31 欄位 | ~2M |
| `scripts/data/companies_with_salary.json` | 合併後的完整資料 | ~2M |
| `scripts/data/jobs.json` | 職缺（LinkedIn + Indeed + 104） | 變動 |
| `scripts/data/104_companies.json` | 104 公司列表 | 變動 |
| `scripts/data/linkedin_jobs.json` | LinkedIn 職缺數 | ~10K |
| `scripts/data/insights.json` | AI 洞察備份 | ~50K |

## CSS / UI 注意事項

### 全域連結色

全域 `a` 的 color 放在 `@layer base` 裡，這樣 Tailwind utility class 可以覆蓋：

```css
@layer base {
  a { color: var(--text-body); text-decoration: none; }
  a:hover { color: var(--text-heading); }
}
```

**不要**把 `a` 的樣式放在 `@layer` 外面，否則會蓋掉所有 Tailwind 的 `text-` class。

### 按鈕式連結的文字色

有背景色的 CTA 連結（如橘黃色按鈕），用 Tailwind class 設定文字色：
```html
<a class="bg-[var(--accent)] text-[#1a2e1a]">按鈕文字</a>
```

因為 `@layer base` 的 `a { color }` 特異度低於 Tailwind utilities，所以 `text-[#1a2e1a]` 會生效。

### 對比度檢查

改色之前用 WebAIM Contrast Checker 或 Python 腳本驗證 WCAG AA（4.5:1）：

```python
def contrast_ratio(fg_hex, bg_hex):
    # ... 算 relative luminance 和對比度
    # 所有 text-muted 在 bg-elevated 上必須 >= 4.5
```

目前的 token 值都通過 AA。

### 104 Playwright 超時排查

**症狀**：`Page.goto: Timeout 30000ms exceeded`

**根本原因**：
1. `wait_until: "networkidle"` — 104 有大量廣告追蹤（GA4 × 3、Google Ads × 2、Emarsys、Scarab Research），永遠不會真正 network idle
2. Cloudflare challenge 需要 10-15 秒完成

**正確設定**：
```python
page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 不用 networkidle
time.sleep(10)           # 等基本載入
page.wait_for_timeout(15000)  # 等 Cloudflare challenge
```

**不要用**：
- `wait_until="networkidle"` — 會卡死
- `timeout=30000` — 太短，Cloudflare 可能需要 15 秒
- `sleep(5)` — 太短，Cloudflare challenge 可能還沒完成
