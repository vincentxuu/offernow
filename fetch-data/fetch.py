"""
104 人力銀行職缺合規爬蟲
========================
- 使用 104 前端公開 JSON API（非 HTML 解析）
- 遵守合理請求頻率（每次請求間隔 2 秒）
- 僅爬取公開可見資料
- 用途：個人求職分析

API Endpoints:
  搜尋: https://www.104.com.tw/jobs/search/list
  詳情: https://www.104.com.tw/job/ajax/content/{job_id}
"""

import requests
import time
import json
import csv
import random
from datetime import datetime
from pathlib import Path


class Job104Scraper:
    """合規爬取 104 人力銀行職缺"""

    BASE_SEARCH_URL = "https://www.104.com.tw/jobs/search/api/jobs"
    BASE_DETAIL_URL = "https://www.104.com.tw/job/ajax/content/{job_id}"

    # 常用地區代碼
    AREAS = {
        "台北市": "6001001000",
        "新北市": "6001002000",
        "桃園市": "6001005000",
        "新竹市": "6001006000",
        "新竹縣": "6001006000",
        "台中市": "6001008000",
        "彰化縣": "6001010000",
        "台南市": "6001014000",
        "高雄市": "6001016000",
    }

    # 排序方式
    ORDER = {
        "符合度": 1,
        "日期": 2,
        "經歷": 3,
        "學歷": 4,
        "應徵人數": 7,
        "待遇": 8,
    }

    # 經歷要求
    EXPERIENCE = {
        "不拘": 1,
        "1年以下": 2,
        "1-3年": 3,
        "3-5年": 4,
        "5-10年": 5,
        "10年以上": 6,
    }

    def __init__(self, delay: float = 2.0):
        """
        Args:
            delay: 每次請求之間的等待秒數（合規用途，預設 2 秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Job104Scraper/1.0 (Personal Job Search Analysis)",
            "Referer": "https://www.104.com.tw/jobs/search/",
            "Accept": "application/json, text/plain, */*",
        })

    def _wait(self):
        """請求間隔，避免對伺服器造成負擔（加入隨機延遲）"""
        jitter = random.uniform(0.5, 1.5)  # 隨機 0.5~1.5 倍
        time.sleep(self.delay * jitter)

    # ──────────────────────────────────────
    #  搜尋職缺
    # ──────────────────────────────────────
    def search(
        self,
        keyword: str,
        area: str | list[str] | None = None,
        order: str = "日期",
        experience: str | None = None,
        page: int = 1,
        max_pages: int | None = None,  # None = 爬到最後一頁
        filter_name: list[str] | None = None,
        filter_skills: list[str] | None = None,
    ) -> list[dict]:
        """
        搜尋 104 職缺

        Args:
            keyword:      搜尋關鍵字，例如 "Python", "AI Agent"
            area:         地區，可用中文名稱或代碼，支援 list 多選
            order:        排序方式（符合度/日期/經歷/學歷/應徵人數/待遇）
            experience:   經歷要求（不拘/1年以下/1-3年/3-5年/5-10年/10年以上）
            page:         起始頁碼
            max_pages:    最多爬取幾頁
            filter_name:  過濾職缺名稱，需包含任一關鍵字
            filter_skills: 過濾技能/描述，需包含任一關鍵字

        Returns:
            職缺列表 (list of dict)
        """
        # 處理地區參數
        area_code = None
        if area:
            if isinstance(area, str):
                area = [area]
            codes = []
            for a in area:
                codes.append(self.AREAS.get(a, a))  # 支援直接傳代碼
            area_code = ",".join(codes)

        all_jobs = []
        current_page = page
        pages_fetched = 0

        while True:
            # 檢查是否超過 max_pages 限制
            if max_pages and pages_fetched >= max_pages:
                print(f"📌 已達 max_pages 限制 ({max_pages})")
                break

            params = {
                "ro": 0,           # 0: 全部, 1: 全職
                "kwop": 7,         # 關鍵字搜尋模式
                "keyword": keyword,
                "order": self.ORDER.get(order, 2),
                "asc": 0,          # 0: 降序
                "page": current_page,
                "mode": "s",       # s: 列表模式
                "jobsource": "2018indexpoc",
            }

            if area_code:
                params["area"] = area_code
            if experience:
                exp_val = self.EXPERIENCE.get(experience)
                if exp_val:
                    params["s5"] = exp_val

            print(f"📡 搜尋第 {current_page} 頁: keyword={keyword}")
            try:
                resp = self.session.get(self.BASE_SEARCH_URL, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                print(f"❌ 請求失敗: {e}")
                break
            except json.JSONDecodeError:
                print("❌ 回傳非 JSON 格式，可能被封鎖或 API 已變更")
                break

            job_list = data.get("data", [])
            if not job_list:
                print("📭 已無更多結果")
                break

            metadata = data.get("metadata", {}).get("pagination", {})
            total = metadata.get("total", "?")
            print(f"   找到 {total} 筆，本頁 {len(job_list)} 筆")

            for job in job_list:
                parsed = self._parse_search_item(job)
                all_jobs.append(parsed)

            # 檢查是否還有下一頁
            total_pages = metadata.get("lastPage", current_page)
            if current_page >= total_pages:
                break

            current_page += 1
            pages_fetched += 1
            self._wait()

        # 交叉過濾
        if filter_name or filter_skills:
            filtered = []
            for job in all_jobs:
                job_name = job.get("job_name", "").lower()
                skills_text = " ".join([
                    job.get("description", ""),
                    " ".join(job.get("skills", [])),
                ]).lower()

                # 檢查職缺名稱（若有設定）
                name_match = True
                if filter_name:
                    name_match = any(kw.lower() in job_name for kw in filter_name)

                # 檢查技能/描述（若有設定）
                skills_match = True
                if filter_skills:
                    skills_match = any(kw.lower() in skills_text for kw in filter_skills)

                # 兩者都要符合（AND）
                if name_match and skills_match:
                    filtered.append(job)

            filters_desc = []
            if filter_name:
                filters_desc.append(f"名稱含 {filter_name}")
            if filter_skills:
                filters_desc.append(f"技能含 {filter_skills}")
            print(f"\n✅ 共取得 {len(all_jobs)} 筆，過濾後 {len(filtered)} 筆（{' AND '.join(filters_desc)}）")
            return filtered

        print(f"\n✅ 共取得 {len(all_jobs)} 筆職缺")
        return all_jobs

    # 經驗代碼對照
    PERIOD_MAP = {
        0: "不拘",
        1: "1年以下",
        2: "1-3年",
        3: "3-5年",
        4: "5-10年",
        5: "10年以上",
    }

    def _parse_search_item(self, item: dict) -> dict:
        """解析搜尋結果中的單筆職缺"""
        job_id = item.get("jobNo", "")

        # 組合薪資描述
        salary_low = item.get("salaryLow", 0)
        salary_high = item.get("salaryHigh", 0)
        if salary_low and salary_high:
            salary = f"{salary_low:,} ~ {salary_high:,}"
        elif salary_low:
            salary = f"{salary_low:,} 以上"
        else:
            salary = "面議"

        # 解析技能要求
        pc_skills = item.get("pcSkills", [])
        skills = [s.get("description", "") for s in pc_skills if isinstance(s, dict)]

        # 解析福利標籤
        tags_raw = item.get("tags", {})
        if isinstance(tags_raw, dict):
            # 取出有描述的標籤
            tags = [v.get("desc", "") for v in tags_raw.values() if v.get("desc")]
        elif isinstance(tags_raw, list):
            tags = [t if isinstance(t, str) else t.get("desc", "") for t in tags_raw]
        else:
            tags = []

        # 經驗要求轉換
        period_code = item.get("period", 0)
        experience = self.PERIOD_MAP.get(period_code, str(period_code))

        # HR 回覆率
        hr_reply_rate = item.get("hrBehaviorPR", 0)

        return {
            "job_id": job_id,
            "job_name": item.get("jobName", ""),
            "company": item.get("custName", ""),
            "industry": item.get("coIndustryDesc", ""),
            "employee_count": item.get("employeeCount", 0),
            "salary": salary,
            "salary_low": salary_low,
            "salary_high": salary_high,
            "area": item.get("jobAddrNoDesc", ""),
            "address": item.get("jobAddress", ""),
            "mrt": item.get("mrtDesc", ""),
            "experience": experience,
            "skills": skills,
            "description": item.get("description", ""),
            "tags": tags,
            "remote_work": item.get("remoteWorkType", 0),
            "hr_reply_rate": f"{hr_reply_rate * 100:.0f}%" if hr_reply_rate else "N/A",
            "appeared_date": item.get("appearDate", ""),
            "apply_count": item.get("applyCnt", 0),
            "link": f"https://www.104.com.tw/job/{job_id}" if job_id else "",
        }

    # ──────────────────────────────────────
    #  取得職缺詳情
    # ──────────────────────────────────────
    def get_detail(self, job_id: str) -> dict | None:
        """
        取得單筆職缺的詳細資訊

        Args:
            job_id: 職缺 ID（從搜尋結果取得）

        Returns:
            詳細資訊 dict，失敗回傳 None
        """
        url = self.BASE_DETAIL_URL.format(job_id=job_id)

        # 詳情 API 的 Referer 需指向該職缺頁面
        headers = {
            "Referer": f"https://www.104.com.tw/job/{job_id}",
        }

        print(f"📋 取得職缺詳情: {job_id}")
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", {})
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"❌ 取得詳情失敗: {e}")
            return None

        self._wait()

        header = data.get("header", {})
        condition = data.get("condition", {})
        welfare = data.get("welfare", {})

        return {
            "job_id": job_id,
            "job_name": header.get("jobName", ""),
            "company": header.get("custName", ""),
            "salary": data.get("jobDetail", {}).get("salaryDesc", ""),
            "address": data.get("jobDetail", {}).get("addressRegion", "")
                       + data.get("jobDetail", {}).get("addressDetail", ""),
            "job_description": data.get("jobDetail", {}).get("jobDescription", ""),
            "experience": condition.get("workExp", ""),
            "education": ", ".join(
                [e.get("desc", "") for e in condition.get("edu", [])]
            ),
            "skills": [s.get("description", "") for s in condition.get("skill", [])],
            "specialties": [s.get("description", "") for s in condition.get("specialty", [])],
            "welfare": welfare.get("welfare", ""),
            "legal_tag": welfare.get("legalTag", ""),
            "industry": header.get("indCatDesc", ""),
            "management_count": condition.get("manageResp", ""),
            "appeared_date": header.get("appearDate", ""),
            "link": f"https://www.104.com.tw/job/{job_id}",
        }

    # ──────────────────────────────────────
    #  批次取得詳情
    # ──────────────────────────────────────
    def get_details_batch(self, jobs: list[dict], max_count: int = 10) -> list[dict]:
        """
        對搜尋結果批次取得詳細資訊

        Args:
            jobs:      search() 回傳的職缺列表
            max_count: 最多取幾筆詳情（避免請求過多）

        Returns:
            詳細資訊列表
        """
        details = []
        for i, job in enumerate(jobs[:max_count]):
            detail = self.get_detail(job["job_id"])
            if detail:
                details.append(detail)
            print(f"   進度: {i + 1}/{min(len(jobs), max_count)}")
        return details

    # ──────────────────────────────────────
    #  輸出
    # ──────────────────────────────────────
    def to_csv(self, jobs: list[dict], filename: str = "104_jobs.csv"):
        """將結果存為 CSV"""
        if not jobs:
            print("⚠️  沒有資料可輸出")
            return

        # 處理 list 欄位
        rows = []
        for job in jobs:
            row = {}
            for k, v in job.items():
                row[k] = ", ".join(str(x) for x in v) if isinstance(v, list) else v
            rows.append(row)

        keys = rows[0].keys()
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)

        print(f"💾 已儲存至 {filename}（共 {len(rows)} 筆）")

    def to_json(self, jobs: list[dict], filename: str = "104_jobs.json"):
        """將結果存為 JSON"""
        if not jobs:
            print("⚠️  沒有資料可輸出")
            return

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"💾 已儲存至 {filename}（共 {len(jobs)} 筆）")


# ══════════════════════════════════════════
#  使用範例
# ══════════════════════════════════════════
def _print_summary(jobs: list[dict], title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    for i, job in enumerate(jobs[:10], 1):
        print(f"\n[{i}] {job['job_name']}")
        print(f"    公司: {job['company']} ({job['industry']})")
        print(f"    規模: {job['employee_count']} 人")
        print(f"    薪資: {job['salary']}")
        print(f"    地點: {job['area']} | {job['mrt']}")
        print(f"    經驗: {job['experience']}")
        print(f"    技能: {', '.join(job['skills'][:6])}")
        print(f"    HR回覆率: {job['hr_reply_rate']}")
        print(f"    連結: {job['link']}")


def _print_stats(jobs: list[dict]):
    print("\n" + "=" * 60)
    print("統計")
    print("=" * 60)
    with_salary = [j for j in jobs if j['salary_low'] > 0]
    if with_salary:
        avg_low = sum(j['salary_low'] for j in with_salary) / len(with_salary)
        avg_high = sum(j['salary_high'] for j in with_salary) / len(with_salary)
        print(f"有標示薪資: {len(with_salary)}/{len(jobs)} 筆")
        print(f"平均薪資範圍: {avg_low:,.0f} ~ {avg_high:,.0f}")


if __name__ == "__main__":
    scraper = Job104Scraper(delay=3.0)

    all_jobs = []

    # ── 搜尋 Node.js 相關職缺 ──
    print("=" * 60)
    print("搜尋: Node.js 後端/全端職缺")
    print("=" * 60)

    nodejs_jobs = scraper.search(
        keyword="nodejs 後端 全端",
        area=["台北市", "新北市"],
        order="日期",
        max_pages=None,
        filter_name=["後端", "全端", "backend", "full"],
        filter_skills=["node", "nodejs"],
    )
    _print_summary(nodejs_jobs, "Node.js 職缺摘要")
    all_jobs.extend(nodejs_jobs)

    # ── 搜尋 AI 相關職缺 ──
    print("\n" + "=" * 60)
    print("搜尋: AI 相關職缺")
    print("=" * 60)

    ai_searches = [
        {"keyword": "AI 人工智慧 機器學習", "filter_name": ["AI", "人工智慧", "機器學習", "machine learning", "engineer"], "filter_skills": ["ai", "llm", "machine learning", "deep learning", "python"]},
        {"keyword": "LLM AI agent 生成式AI", "filter_name": ["AI", "LLM", "agent", "prompt", "engineer"], "filter_skills": ["llm", "openai", "langchain", "ai agent", "rag"]},
    ]

    for search_params in ai_searches:
        jobs = scraper.search(
            area=["台北市", "新北市"],
            order="日期",
            max_pages=None,
            **search_params,
        )
        all_jobs.extend(jobs)

    # 去重複
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] not in seen:
            seen.add(job["job_id"])
            unique_jobs.append(job)

    print(f"\n📊 合併後共 {len(unique_jobs)} 筆（去重複）")

    # ── 輸出檔案 ──
    if unique_jobs:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = Path(__file__).parent / "data"
        archive_dir = data_dir / "archive"
        data_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)
        scraper.to_csv(unique_jobs, str(archive_dir / f"104_jobs_search_{ts}.csv"))
        scraper.to_json(unique_jobs, str(archive_dir / f"104_jobs_search_{ts}.json"))
        scraper.to_csv(unique_jobs, str(data_dir / "104_jobs_search.csv"))
        scraper.to_json(unique_jobs, str(data_dir / "104_jobs_search.json"))
        _print_stats(unique_jobs)