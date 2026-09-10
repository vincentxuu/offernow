# Service Teardown: TWSE / TPEx OpenAPI

> 拆解日期：2026-09-10
> 目標：openapi.twse.com.tw（上市）、www.tpex.org.tw/openapi（上櫃）
> 方法：curl 直接打 API 端點

---

## 總覽

| | 上市（TWSE） | 上櫃（TPEx） |
|---|---|---|
| **公司數** | 1,094 家 | 890 家 |
| **合計** | **1,984 家上市櫃公司** |
| **API 基礎 URL** | `openapi.twse.com.tw/v1` | `www.tpex.org.tw/openapi/v1` |
| **認證** | 免費、免註冊、免 key | 同左 |
| **格式** | JSON array | JSON array |
| **日期格式** | 民國年（`1150909` = 2026-09-09） | 同左 |
| **Rate limit headers** | 無（無 X-RateLimit 等 header） | 同左 |
| **Content-Disposition** | `attachment;filename=*.json`（可當檔案下載） | 無 |

---

## 端點 Schema

### 1. 上市公司基本資料 `t187ap03_L`

```
GET https://openapi.twse.com.tw/v1/opendata/t187ap03_L
→ 200, 1.3MB, 1,094 筆
```

| 欄位 | 型別 | 範例 | 說明 |
|------|------|------|------|
| `出表日期` | string | `"1150909"` | 民國年 YYYMMDD |
| `公司代號` | string | `"1101"` | **股票代號（= 104 的 exchangeId）** |
| `公司名稱` | string | `"臺灣水泥股份有限公司"` | 全名 |
| `公司簡稱` | string | `"台泥"` | 簡稱 |
| `外國企業註冊地國` | string | `"－ "` | 本國為 `－` |
| `產業別` | string | `"01"` | 產業代碼（數字） |
| `住址` | string | | 公司地址 |
| `營利事業統一編號` | string | `"11913502"` | **統編（可串 104 的 custNo）** |
| `董事長` | string | `"張安平"` | |
| `總經理` | string | `"程耀輝"` | |
| `發言人` / `代理發言人` | string | | |
| `成立日期` | string | `"19501229"` | 西元年 YYYYMMDD |
| `上市日期` | string | `"19620209"` | 西元年 YYYYMMDD |
| `實收資本額` | string | `"77231817420"` | 新台幣（元） |
| `已發行普通股數或TDR原股發行股數` | string | `"7523181742"` | 股數 |
| `英文簡稱` | string | `"TCC"` | |
| `網址` | string | | 公司官網 |
| `電子郵件信箱` | string | | |

### 2. 上櫃公司基本資料 `mopsfin_t187ap03_O`

```
GET https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O
→ 200, 1.0MB, 890 筆
```

| 欄位 | 型別 | 範例 | 對應 TWSE 欄位 |
|------|------|------|---------------|
| `Date` | string | `"1150909"` | `出表日期` |
| `SecuritiesCompanyCode` | string | `"1240"` | `公司代號` |
| `CompanyName` | string | `"茂生農經股份有限公司"` | `公司名稱` |
| `CompanyAbbreviation` | string | `"茂生農經"` | `公司簡稱` |
| `SecuritiesIndustryCode` | string | `"33"` | `產業別` |
| `Address` | string | | `住址` |
| `UnifiedBusinessNo.` | string | `"18795706"` | `營利事業統一編號` |
| `Chairman` | string | | `董事長` |
| `Paidin.Capital.NTDollars` | string | | `實收資本額` |
| `IssueShares` | string | | `已發行普通股數...` |
| `Symbol` | string | `"MORNSUN"` | `英文簡稱` |
| `WebAddress` | string | | `網址` |

**關鍵差異**：TWSE 用中文欄位名、TPEx 用英文欄位名。內容相同但 key 完全不同，需做 mapping。

### 3. 上市公司每月營收 `t187ap05_L`

```
GET https://openapi.twse.com.tw/v1/opendata/t187ap05_L
→ 200, 604KB, 1,085 筆
```

| 欄位 | 範例 | 說明 |
|------|------|------|
| `資料年月` | `"11507"` | 民國年 YYYMM（115 年 7 月） |
| `公司代號` | `"1101"` | 股票代號 |
| `公司名稱` | `"台泥"` | 簡稱 |
| `產業別` | `"水泥工業"` | **這裡有產業中文名！** |
| `營業收入-當月營收` | `"13744103"` | 仟元 |
| `營業收入-上月營收` | `"13382706"` | 仟元 |
| `營業收入-去年當月營收` | `"13535929"` | 仟元 |
| `營業收入-上月比較增減(%)` | `"2.70"` | |
| `營業收入-去年同月增減(%)` | `"1.54"` | |
| `累計營業收入-當月累計營收` | `"85211435"` | 仟元 |

**注意**：每月營收 API 的 `產業別` 有中文名（如「半導體業」「水泥工業」），但基本資料 API 的 `產業別` 是數字代碼。

### 4. 全市場每日收盤行情 `STOCK_DAY_ALL`

```
GET https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
→ 200, 319KB, 1,382 筆（含 ETF）
```

| 欄位 | 範例 | 說明 |
|------|------|------|
| `Date` | `"1150909"` | 民國年 |
| `Code` | `"2330"` | 股票代號 |
| `Name` | `"台積電"` | 簡稱 |
| `ClosingPrice` | `"1010.00"` | 收盤價 |
| `Change` | `"-30.0000"` | 漲跌 |
| `TradeVolume` | `"47651328"` | 成交量（股） |
| `TradeValue` | `"48564973729"` | 成交金額 |
| `OpeningPrice` / `HighestPrice` / `LowestPrice` | | 開高低 |

### 5. 上櫃每日收盤 `tpex_mainboard_daily_close_quotes`

```
GET https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
→ 200, 4.3MB, 11,020 筆（含多日？或含所有證券類型）
```

| 欄位 | 範例 | 說明 |
|------|------|------|
| `Date` | `"1150909"` | 民國年 |
| `SecuritiesCompanyCode` | `"5274"` | 股票代號 |
| `CompanyName` | `"信驊"` | 簡稱 |
| `Close` | `"3365.00"` | 收盤價 |
| `Change` | `"+5.00"` | 漲跌（帶正負號字串） |
| `Capitals` | `"1710413270"` | **實收資本額** |
| `TradingShares` / `TransactionAmount` | | 量/額 |

---

## 串接鏈驗證

```
TWSE 公司代號 "2330"
  = 104 薪資 API exchangeId "2330"
  = MOPS 查詢參數
  ✅ 直接一對一串接，無需 mapping

TWSE 統編 "22099131" (台積電)
  ≈ 104 職缺 API custNo (需前補 0 或格式對齊)
  ⚠️ 需驗證格式是否完全一致

上市 1,094 家 + 上櫃 890 家 = 1,984 家
  vs 104 zone=16 列出 1,280 家
  → 104 覆蓋率 ~64%（低於先前估計的 70%）
```

**信驊（5274）是上櫃**，所以在 TWSE API 找不到，要查 TPEx API。104 的 `exchangeId` 不區分上市上櫃，但 TWSE/TPEx 是兩套分開的 API，需要兩邊都查。

---

## 產業代碼 → 中文名稱

基本資料 API 的 `產業別` 是數字代碼，需對照。營收 API 直接有中文名。33 個產業包括：

半導體業、光電業、電腦及週邊設備業、電子零組件業、通信網路業、電子通路業、資訊服務業、其他電子業、水泥工業、食品工業、塑膠工業、紡織纖維、電機機械、電器電纜、化學工業、生技醫療業、玻璃陶瓷、造紙工業、鋼鐵工業、橡膠工業、汽車工業、建材營造、航運業、觀光餐旅、金融保險業、貿易百貨、油電燃氣業、綠能環保、數位雲端、運動休閒、居家生活、存託憑證、其他

---

## 「百大」排名方式

API 本身不提供排名。可自行計算：

| 排名依據 | 計算方式 | 資料來源 |
|---------|---------|---------|
| **市值** | 收盤價 × 已發行股數 | STOCK_DAY_ALL × t187ap03_L |
| **營收** | 累計營業收入 | t187ap05_L |
| **資本額** | 實收資本額 | t187ap03_L |
| **薪資** | 非主管中位數 | 104 salary/top100 或 MOPS |

最合理的「百大」= **市值前 100**（需每日計算：收盤價 × 發行股數）。

---

## 對我們的價值

| 端點 | 用途 | 更新頻率 |
|------|------|---------|
| 基本資料 | 公司名單 + 統編 + 官網 + 產業 + 資本額 | 不定期（可週抓） |
| 每月營收 | 營收趨勢 + 產業中文名 | 每月 |
| 每日收盤 | 市值計算 + 股價 | 每日 |
| 104 salary/top100 | 薪資中位數 + exchangeId | 每年 6 月 |

**技術結論**：全部免費、免 key、JSON 格式、curl 即可取得。唯一麻煩是上市/上櫃兩套 API 欄位命名不同，需寫 mapping layer。日期全是民國年需轉換。
