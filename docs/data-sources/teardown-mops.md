# Service Teardown: MOPS 公開資訊觀測站（薪資揭露）

> 拆解日期：2026-09-10
> 目標：mopsov.twse.com.tw/mops/web/t100sb15
> 要回答的問題：POST 表單結構？Response 格式？可爬取性？
> 對照目標：作為薪資資料來源

---

## L1 — UI 層

### 查詢表單
- **市場別**：上市（sii）/ 上櫃（otc）— combobox
- **年度**：民國年（預設 114）— textbox
- **產業類別**：33 個選項（水泥/食品/塑膠/.../半導體/電腦/光電/.../金融/其他）— combobox，空白查全部
- **排序方式**：證券代號 / 薪資平均數 / 薪資中位數 / 平均數變動% / 中位數變動% / 男/女性各指標 — radio button
- **排列順序**：由小到大 / 由大到小 — radio button
- **CSV 下載按鈕**：有！檔名格式 `t100sb15_{timestamp}.csv`

`實測`

---

## L3 — 網路層

### 核心 API

```
POST /mops/web/ajax_t100sb15
Content-Type: application/x-www-form-urlencoded

encodeURIComponent=1&step=1&firstin=1&TYPEK=sii&RYEAR=114&code=01
```

**參數：**

| 參數 | 值 | 說明 |
|------|---|------|
| `TYPEK` | `sii` / `otc` | 上市 / 上櫃 |
| `RYEAR` | `114` | 民國年 |
| `code` | `01` / 空白 | 產業代碼（空白=全部） |
| `step` | `1` | 固定值 |
| `firstin` | `1` | 固定值 |
| `encodeURIComponent` | `1` | 固定值 |

**產業代碼對照**（從 combobox 反推）：

| code | 產業 | code | 產業 |
|------|------|------|------|
| 01 | 水泥工業 | 24 | 半導體業 |
| 02 | 食品工業 | 25 | 電腦及週邊設備業 |
| 03 | 塑膠工業 | 26 | 光電業 |
| 04 | 紡織纖維 | 27 | 通信網路業 |
| 05 | 電機機械 | 28 | 電子零組件業 |
| 06 | 電器電纜 | 29 | 電子通路業 |
| 20 | 化學工業 | 30 | 資訊服務業 |
| 21 | 生技醫療業 | 31 | 其他電子業 |
| ... | ... | 32 | 金融保險業 |

**Response**：HTML table（非 JSON），需要 parse。

### 輔助端點

| 端點 | 用途 |
|------|------|
| `POST /server-java/AjaxCheck` | 驗證 token（查詢前自動觸發） |
| `POST /server-java/t105sb02` | CSV 下載 |

`實測`

---

## L4 — Response Schema（31 欄位）

### 非擔任主管職務之全時員工資訊（核心 9 欄）

| 欄位 | 台泥範例值 | 說明 |
|------|-----------|------|
| 產業類別 | 水泥工業 | |
| **公司代號** | **1101** | **股票代號，可串 TWSE/104** |
| 公司名稱 | 台泥 | 簡稱 |
| 員工薪資總額(仟元) | 1,205,896 | |
| 員工人數-年度平均(人) | 1,212 | |
| 員工薪資-平均數 114 年 | 995 | 仟元/人 |
| 員工薪資-平均數 113 年 | 1,003 | 前一年對照 |
| 平均數調整變動(%) | -0.80% | |
| **員工薪資-中位數 114 年** | **895** | **仟元/人，核心指標** |
| 員工薪資-中位數 113 年 | 877 | 前一年對照 |
| 中位數調整變動(%) | 2.05% | |
| 每股盈餘(元/股) | -1.60 | EPS |

### 性別薪資資訊（115 年度新增，12 欄）

| 欄位 | 說明 |
|------|------|
| 男性員工薪資-平均數 114/113 年 | 資本額 100 億以上才揭露 |
| 男性員工-平均數調整變動(%) | |
| 女性員工薪資-平均數 114/113 年 | |
| 女性員工-平均數調整變動(%) | |
| 男性員工薪資-中位數 114/113 年 | |
| 男性員工-中位數調整變動(%) | |
| 女性員工薪資-中位數 114/113 年 | |
| 女性員工-中位數調整變動(%) | |

> 嘉泥等小公司顯示「不適用」— 資本額未達 100 億門檻

### 同業公司資訊（2 欄）

| 欄位 | 水泥業範例 |
|------|-----------|
| 同業薪資平均數 | 915 仟元/人 |
| 同業平均 EPS | 0.13 元/股 |

### 薪資統計篩選指標（5 欄）

| 欄位 | 值 | 說明 |
|------|---|------|
| 平均數未達 50 萬 | Y/N | 低薪旗標 |
| EPS 優於同業但薪資低於同業 | Y/N | 獲利好但給薪低 |
| EPS 成長但薪資減少 | Y/N | 賺更多但給更少 |
| 經營績效與薪酬關聯性說明 | 文字 | 公司自述 |
| 具體改善措施說明 | 文字 | 公司自述 |

`實測` — 從 HTML response 完整解析

---

## L5 — 爬取可行性評估

### 優勢
- **不需登入**：直接 POST 即可取得資料
- **有 CSV 下載**：`/server-java/t105sb02` + filename 參數
- **結構穩定**：HTML table 結構清楚，31 欄固定
- **公司代號就是股票代號**：完美串接 TWSE API 和 104 薪資 API

### 挑戰
- **Response 是 HTML 不是 JSON**：需要 HTML parser（BeautifulSoup / cheerio）
- **AjaxCheck 驗證**：查詢前會打 `/server-java/AjaxCheck`，可能需要帶 session cookie
- **每次只查一個產業**：要查全部需送 33+ 次請求（或 code 留空查全部）
- **年度更新**：每年 6 月底才更新，一年只需爬一次

### 建議爬取策略

```python
# 最簡單的方式：直接 POST 查全部（code 留空）
import requests
from bs4 import BeautifulSoup

for market in ['sii', 'otc']:  # 上市 + 上櫃
    resp = requests.post(
        'https://mopsov.twse.com.tw/mops/web/ajax_t100sb15',
        data={
            'encodeURIComponent': 1,
            'step': 1,
            'firstin': 1,
            'TYPEK': market,
            'RYEAR': 114,
            'code': ''  # 空白 = 全部產業
        }
    )
    soup = BeautifulSoup(resp.text, 'html.parser')
    rows = soup.find_all('tr')
    # parse table rows...

# 或者直接用 CSV 下載（如果 endpoint 不需要 session）
```

---

## L6 — 對照分析

### 資料串接鏈（完整驗證）

```
MOPS 公司代號 (1101)
  = TWSE OpenAPI 公司代號
  = 104 薪資 API exchangeId (1101)

三個資料來源用同一個股票代號串接，零成本 JOIN。
```

### MOPS vs 104 薪資 API 比較

| 面向 | MOPS | 104 薪資 API |
|------|------|-------------|
| **覆蓋** | 全部上市櫃（~1,800 家） | TOP 155 家 |
| **格式** | HTML table（需 parse） | JSON（直接用） |
| **欄位** | 31 欄（含性別、同業、EPS） | 12 欄（精簡） |
| **年度對照** | 有（114/113 年） | 無 |
| **性別薪資** | 有（100 億以上） | 無 |
| **薪資統計指標** | 有（低薪/獲利 vs 薪資旗標） | 無 |
| **公司自述** | 有（改善措施說明） | 無 |
| **更新頻率** | 年（6 月底） | 年（跟 MOPS 同步） |

**結論**：MOPS 資料更完整（全部公司 + 性別 + 統計指標 + 公司自述），但需要 HTML parse。104 薪資 API 是精簡版（JSON 好用但只有 TOP 155）。**兩者應該都爬**：MOPS 當完整資料源，104 當快速索引。

---

## 已完成項目

| 層 | 項目 | 方法 |
|---|------|------|
| L1 | 查詢表單結構（市場/年度/產業/排序） | Playwright snapshot |
| L3 | POST API 參數完整記錄 | Network request 擷取 |
| L3 | Response HTML 結構分析 | Response body 擷取 |
| L4 | 31 欄位完整 schema | HTML 解析 |
| L5 | 爬取可行性 + 建議策略 | 分析 |
| L6 | MOPS vs 104 薪資 API 比較 | 分析 |

## 沒拿到的

- CSV 下載端點是否需要 session cookie（需實測）
- AjaxCheck 的具體驗證機制
- code 留空是否真的回傳全部公司（需實測）
- 歷年資料（RYEAR=113, 112 等）是否仍可查詢

## 殘留清單

無

---

## 原始擷取路徑

- `.playwright-mcp/mops-salary-snapshot.md`
- `.playwright-mcp/mops-query-network.md`
- `.playwright-mcp/mops-salary-response.html`
