#!/usr/bin/env python3
"""
LinkedIn 公司 ID 映射腳本（一次性）
====================================
為台灣上市櫃公司建立 stock_id ↔ linkedin_company_id 映射。

策略（優先順序）：
1. 已知 slug → 直接訪問 /company/{slug}/ 抓 ID
2. 英文名（NAME_MAP）→ LinkedIn 公司搜尋頁
3. 中文全名 → LinkedIn 公司搜尋頁（fallback）

用法：
    uv run scripts/fetch-linkedin-company-ids.py
    uv run scripts/fetch-linkedin-company-ids.py --limit 50
    uv run scripts/fetch-linkedin-company-ids.py --dry-run
    uv run scripts/fetch-linkedin-company-ids.py --resume
"""

import json
import re
import time
import random
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import URLError, HTTPError

DATA_DIR = Path(__file__).parent / "data"
COMPANIES_FILE = DATA_DIR / "companies_with_salary.json"
MAPPING_FILE = DATA_DIR / "linkedin_company_mapping.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
}

# Short name → (English search name, known LinkedIn slug)
# slug is the URL path component: linkedin.com/company/{slug}
SLUG_MAP: dict[str, tuple[str, str | None]] = {
    "台積電":       ("TSMC", "tsmc"),
    "鴻海":         ("Foxconn", "foxconn"),
    "聯發科":       ("MediaTek", "mediatek"),
    "台達電":       ("Delta Electronics", "delta-electronics"),
    "華碩":         ("ASUS", "asustek"),
    "廣達":         ("Quanta Computer", "quanta-computer"),
    "瑞昱":         ("Realtek", "realtek-semiconductor-corp"),
    "聯詠":         ("Novatek", "novatek-microelectronics-corp"),
    "日月光投控":   ("ASE Group", "ase-group"),
    "中華電":       ("Chunghwa Telecom", "chunghwa-telecom"),
    "國泰金":       ("Cathay Financial", "cathay-financial-holdings"),
    "富邦金":       ("Fubon Financial", "fubon-financial-holding-co.-ltd."),
    "中信金":       ("CTBC Financial", "ctbc-financial-holding"),
    "玉山金":       ("E.SUN Financial", "e.sun-financial-holding-co.-ltd."),
    "元大金":       ("Yuanta Financial", "yuanta-financial-holding-co-ltd"),
    "台新金":       ("Taishin Financial", "taishin-financial-holding"),
    "兆豐金":       ("Mega Financial", "mega-financial-holding-co.-ltd."),
    "第一金":       ("First Financial", "first-financial-holding"),
    "華南金":       ("Hua Nan Financial", "hua-nan-financial-holdings"),
    "開發金":       ("China Development Financial", "china-development-financial"),
    "新光金":       ("Shin Kong Financial", "shin-kong-financial-holding"),
    "合庫金":       ("TCB Bank", "taiwan-cooperative-financial-holding"),
    "友達":         ("AUO", "auo"),
    "群創":         ("Innolux", "innolux-corporation"),
    "緯創":         ("Wistron", "wistron"),
    "仁寶":         ("Compal", "compal-electronics"),
    "和碩":         ("Pegatron", "pegatron"),
    "英業達":       ("Inventec", "inventec"),
    "技嘉":         ("GIGABYTE", "gigabyte"),
    "微星":         ("MSI", "maboroshi-group"),  # MSI is ambiguous, try slug
    "宏碁":         ("Acer", "aaboroshi"),  # placeholder, search-based
    "大立光":       ("Largan Precision", "largan-precision"),
    "統一":         ("Uni-President", "uni-president-enterprises-corporation"),
    "台塑":         ("Formosa Plastics", "formosa-plastics-corporation"),
    "南亞":         ("Nan Ya Plastics", "nan-ya-plastics-corporation"),
    "台化":         ("Formosa Chemicals", "formosa-chemicals-and-fibre-corporation"),
    "長榮":         ("Evergreen Marine", "evergreen-marine-corp"),
    "陽明":         ("Yang Ming Marine", "yang-ming-marine-transport-corp"),
    "萬海":         ("Wan Hai Lines", "wan-hai-lines-ltd"),
    "台泥":         ("Taiwan Cement", "taiwan-cement-corporation"),
    "遠東新":       ("Far Eastern New Century", "far-eastern-new-century-corporation"),
    "中鋼":         ("China Steel", "china-steel-corporation"),
    "正新":         ("Cheng Shin Rubber", "cheng-shin-rubber"),
    "研華":         ("Advantech", "advantech"),
    "可成":         ("Catcher Technology", "catcher-technology"),
    "智邦":         ("Accton Technology", "accton-technology-corporation"),
    "矽力-KY":     ("Silergy", "silergy-corp"),
    "信驊":         ("Aspeed Technology", "aspeed-technology"),
    "祥碩":         ("ASMedia Technology", "asmedia-technology"),
    "力旺":         ("eMemory Technology", "ememory-technology"),
    "世芯-KY":     ("Alchip Technologies", "alchip-technologies"),
    "創意":         ("GUC", "global-unichip-corp"),
    "群聯":         ("Phison Electronics", "phison-electronics"),
    "環球晶":       ("GlobalWafers", "globalwafers"),
    "穩懋":         ("WIN Semiconductors", "win-semiconductors"),
    "光寶科":       ("Lite-On Technology", "lite-on-technology"),
    "緯穎":         ("Wiwynn", "wiwynn"),
    "奇鋐":         ("Asia Vital Components", "asia-vital-components"),
    "欣興":         ("Unimicron", "unimicron"),
    "景碩":         ("Kinsus", "kinsus-interconnect-technology"),
    "南電":         ("Nanya PCB", "nanya-pcb"),
    "力成":         ("Powertech Technology", "powertech-technology"),
    "京元電子":     ("King Yuan Electronics", "king-yuan-electronics"),
    "矽品":         ("SPIL", "siliconware-precision-industries-co-ltd"),
    "頎邦":         ("Chipbond", "chipbond-technology-corporation"),
    "台光電":       ("TUC", None),
    "健鼎":         ("Tripod Technology", "tripod-technology-corporation"),
    "華通":         ("Compeq", "compeq-manufacturing"),
    "嘉澤":         ("Lotes", "lotes-co-ltd"),
    "致茂":         ("Chroma ATE", "chroma-ate"),
    "漢唐":         ("CTCI Advanced Systems", None),
    "台灣大":       ("Taiwan Mobile", "taiwan-mobile"),
    "遠傳":         ("Far EasTone", "far-eastone-telecommunications"),
    "聯強":         ("Synnex Technology", "synnex-technology-international"),
    "大聯大":       ("WPG Holdings", "wpg-holdings"),
    "鼎翰":         ("TSC Auto ID", None),
    "中租-KY":     ("Chailease", "chailease-holding"),
    # Additional major companies
    "聯電":         ("UMC", "umc"),
    "南亞科":       ("Nanya Technology", "nanya-technology-corporation"),
    "旺宏":         ("Macronix", "macronix"),
    "華邦電":       ("Winbond", "winbond-electronics"),
    "力積電":       ("PSMC", None),
    "世界":         ("Vanguard International Semiconductor", "vanguard-international-semiconductor"),
    "聯華":         ("LHDC", None),
    "鴻準":         ("Foxconn Technology", None),
    "臻鼎-KY":     ("Zhen Ding Technology", "zhen-ding-technology-holding"),
    "聯茂":         ("ITEQ", None),
    "雙鴻":         ("Auras Technology", "auras-technology"),
    "川湖":         ("King Slide", "king-slide-works"),
    "上銀":         ("HIWIN", "hiwin"),
    "卜蜂":         ("CPF Thailand", None),
    "巨大":         ("Giant", "giant-bicycles"),
    "裕隆":         ("Yulon Motor", "yulon-motor"),
    "和泰車":       ("Hotai Motor", "hotai-motor"),
    "豐泰":         ("Feng Tay", "feng-tay-enterprise"),
    "寶成":         ("Pou Chen", "pou-chen-corporation"),
    "儒鴻":         ("Eclat Textile", "eclat-textile"),
    "聚陽":         ("Makalot Industrial", "makalot-industrial"),
    "台半":         ("TSC", None),
    "穎崴":         ("Keyarrow", None),
    "信邦":         ("Sinbon", "sinbon-electronics"),
    "亞德客-KY":   ("AirTAC", "airtac-international-group"),
    "漢翔":         ("AIDC", "aidc-aerospace-industrial-development-corporation"),
    "全家":         ("FamilyMart", "familymart-taiwan"),
    "統一超":       ("7-Eleven Taiwan", "president-chain-store-corporation"),
    "momo":         ("momo.com", "momo-com-inc"),
    "富邦媒":       ("momo.com", "momo-com-inc"),
    "網家":         ("PChome", "pchome-online"),
    "三陽工業":     ("SYM", "sanyang-motor"),
    "光洋科":       ("UMAT", None),
    "新日興":       ("Shin Zu Shing", "shin-zu-shing"),
}


def fetch_html(url: str) -> str | None:
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"    ✗ {e}")
        return None


def extract_company_id(html: str) -> str | None:
    """Extract numeric company ID from LinkedIn page HTML."""
    for pattern in [
        r'urn:li:(?:fs_normalized)?[Cc]ompany:(\d+)',
        r'"companyId"\s*:\s*(\d+)',
        r'data-company-id="(\d+)"',
        r'"objectUrn"\s*:\s*"urn:li:company:(\d+)"',
        r'"company[Ii]d"\s*:\s*"?(\d+)"?',
        r'/voyager/api/.*company/(\d+)',
    ]:
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    return None


def extract_company_slug_from_search(html: str, search_name: str) -> str | None:
    """Extract the most relevant company slug from a LinkedIn company search page.

    Looks for /company/{slug} links and picks the one whose visible text
    best matches the search name.
    """
    from collections import Counter
    matches = re.findall(
        r'href="https?://[a-z.]*linkedin\.com/company/([^/?"\s]+)',
        html,
    )
    if not matches:
        return None

    slug_counts = Counter(matches)
    # Filter out common noise slugs
    noise = {"linkedin", "about", "life", "jobs", "people", "posts", "insights"}
    candidates = [(s, c) for s, c in slug_counts.most_common(10) if s not in noise]
    if candidates:
        return candidates[0][0]
    return None


def try_direct_slug(slug: str) -> str | None:
    """Fetch /company/{slug}/ and extract numeric ID."""
    url = f"https://www.linkedin.com/company/{slug}/"
    html = fetch_html(url)
    if not html:
        return None
    return extract_company_id(html)


def try_company_search(name: str) -> tuple[str | None, str | None]:
    """Search LinkedIn for a company by name, return (slug, company_id)."""
    url = f"https://www.linkedin.com/search/results/companies/?keywords={quote(name)}"
    html = fetch_html(url)
    if not html:
        return None, None

    slug = extract_company_slug_from_search(html, name)
    if not slug:
        return None, None

    time.sleep(1.5 + random.random())

    company_id = try_direct_slug(slug)
    return slug, company_id


def try_jobs_search(name: str) -> tuple[str | None, str | None]:
    """Search LinkedIn jobs filtered by company name, extract company slug + ID.

    Uses `f_C` (company filter) approach: first find the company slug from
    a broader search, then use it.
    """
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={quote(name)}&location=Taiwan&f_TPR=r2592000"
    )
    html = fetch_html(url)
    if not html:
        return None, None

    # Look for company links in job cards
    matches = re.findall(
        r'href="https?://[a-z.]*linkedin\.com/company/([^/?"\s]+)',
        html,
    )
    if not matches:
        return None, None

    from collections import Counter
    slug_counts = Counter(matches)
    noise = {"linkedin"}
    candidates = [(s, c) for s, c in slug_counts.most_common(5) if s not in noise]
    if not candidates:
        return None, None

    slug = candidates[0][0]
    time.sleep(1.0 + random.random())
    company_id = try_direct_slug(slug)
    return slug, company_id


def resolve_company(short_name: str, full_name: str) -> tuple[str | None, str | None, str]:
    """Try multiple strategies to find a company's LinkedIn ID.

    Returns (slug, company_id, method_used).
    """
    entry = SLUG_MAP.get(short_name)
    en_name = entry[0] if entry else None
    known_slug = entry[1] if entry else None

    # Strategy 1: Known slug → direct fetch
    if known_slug:
        cid = try_direct_slug(known_slug)
        if cid:
            return known_slug, cid, "slug"
        # Slug might be wrong, fall through

    # Strategy 2: English name → company search
    if en_name:
        time.sleep(2.0 + random.random())
        slug, cid = try_company_search(en_name)
        if cid:
            return slug, cid, "en_search"
        if slug:
            return slug, None, "en_search(slug_only)"

    # Strategy 3: Chinese full name → company search
    time.sleep(2.0 + random.random())
    slug, cid = try_company_search(full_name)
    if cid:
        return slug, cid, "zh_search"
    if slug:
        return slug, None, "zh_search(slug_only)"

    # Strategy 4: English name → jobs search (last resort)
    if en_name:
        time.sleep(2.0 + random.random())
        slug, cid = try_jobs_search(en_name)
        if cid:
            return slug, cid, "en_jobs"

    return None, None, "not_found"


def main():
    parser = argparse.ArgumentParser(description="Fetch LinkedIn company IDs")
    parser.add_argument("--limit", type=int, default=200,
                        help="Number of top companies to process (default: 200)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't write back to companies JSON")
    parser.add_argument("--resume", action="store_true",
                        help="Skip companies already mapped")
    args = parser.parse_args()

    print("=" * 60)
    print("OfferNow — LinkedIn Company ID Mapping")
    print("=" * 60)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    with_salary = [c for c in companies if c.get("salary_median_k") is not None]
    with_salary.sort(key=lambda x: x["salary_median_k"], reverse=True)
    targets = with_salary[:args.limit]

    mapping: dict[str, dict] = {}
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, encoding="utf-8") as f:
            mapping = json.load(f)
        print(f"Loaded existing mapping: {len(mapping)} entries")

    print(f"Processing top {len(targets)} companies by salary…\n")

    stats = {"slug": 0, "en_search": 0, "zh_search": 0, "en_jobs": 0, "slug_only": 0, "failed": 0, "skipped": 0}

    for i, company in enumerate(targets):
        stock_id = company["stock_id"]
        short_name = company.get("short_name") or company.get("name", "")
        full_name = company.get("name", short_name)

        if args.resume and stock_id in mapping and mapping[stock_id].get("company_id"):
            stats["skipped"] += 1
            continue

        print(f"  [{i+1}/{len(targets)}] {short_name} ({stock_id})", end=" ", flush=True)

        slug, company_id, method = resolve_company(short_name, full_name)

        if company_id:
            print(f"→ {slug} (ID:{company_id}) [{method}]")
            mapping[stock_id] = {
                "slug": slug,
                "company_id": company_id,
                "method": method,
                "short_name": short_name,
            }
            stats[method.split("(")[0]] = stats.get(method.split("(")[0], 0) + 1
        elif slug:
            print(f"→ {slug} (slug only) [{method}]")
            mapping[stock_id] = {
                "slug": slug,
                "company_id": None,
                "method": method,
                "short_name": short_name,
            }
            stats["slug_only"] += 1
        else:
            print(f"→ not found")
            stats["failed"] += 1

        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        time.sleep(2.0 + random.random() * 2)

    total_with_id = sum(1 for m in mapping.values() if m.get("company_id"))
    print(f"\n{'=' * 60}")
    print(f"Results: {total_with_id} with ID, {stats['slug_only']} slug-only, {stats['failed']} failed, {stats['skipped']} skipped")
    print(f"By method: slug={stats['slug']}, en_search={stats['en_search']}, zh_search={stats.get('zh_search',0)}, en_jobs={stats.get('en_jobs',0)}")
    print(f"Mapping saved to {MAPPING_FILE}")

    if not args.dry_run:
        updated = 0
        for company in companies:
            sid = company["stock_id"]
            if sid in mapping and mapping[sid].get("company_id"):
                company["linkedin_company_id"] = mapping[sid]["company_id"]
                updated += 1

        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        print(f"Updated {updated} companies in {COMPANIES_FILE}")
    else:
        print("(dry-run: not modified)")

    if total_with_id:
        print(f"\n--- Sample Mapped ---")
        for sid, m in list((s, m) for s, m in mapping.items() if m.get("company_id"))[:10]:
            print(f"  {m['short_name']} ({sid}) → {m['slug']} (ID:{m['company_id']}) [{m.get('method','')}]")

    print("Done!")


if __name__ == "__main__":
    main()
