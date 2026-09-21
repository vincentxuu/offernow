import {
  ChevronDown,
  ChevronRight,
  TrendingDown,
  TrendingUp,
} from '@sketchyicons/react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useEffect, useMemo, useRef, useState } from 'react'
import { getCompanies, INDUSTRIES } from '#/utils/companies.functions'
import type { JobFilters } from '#/utils/jobs.functions'
import { getFilterCounts, getJobsPage } from '#/utils/jobs.functions'
import type { Company, Job } from '#/utils/types'

export const Route = createFileRoute('/jobs')({
  loader: async () => {
    const [firstPage, companies, filterCounts] = await Promise.all([
      getJobsPage({ data: { dateRange: '7天', limit: 50 } }),
      getCompanies(),
      getFilterCounts(),
    ])
    const companyMap: Record<string, Company> = {}
    for (const c of companies) companyMap[c.stock_id] = c
    return { firstPage, companyMap, filterCounts }
  },
  component: JobsPage,
})

const SOURCES = [
  '全部',
  '104',
  'linkedin',
  'indeed',
  'yourator',
  'hackernews',
  'arcdev',
  'wwr',
  'remoteok',
  'cakeresume',
  'justremote',
  'remotive',
  'dynamitejobs',
  'careervault',
  'himalayas',
  'workingnomads',
] as const

const SOURCE_LABELS: Record<string, string> = {
  全部: '所有來源',
  '104': '104',
  linkedin: 'LinkedIn',
  indeed: 'Indeed',
  yourator: 'Yourator',
  hackernews: 'HN Hiring',
  arcdev: 'Arc.dev',
  wwr: 'WWR',
  remoteok: 'RemoteOK',
  cakeresume: 'CakeResume',
  justremote: 'JustRemote',
  remotive: 'Remotive',
  dynamitejobs: 'Dynamite',
  careervault: 'CareerVault',
  himalayas: 'Himalayas',
  workingnomads: 'WorkingNomads',
}

const JOB_TYPES = ['全部', '遠端/混合', '全球遠端'] as const
const CITIES = [
  '全部',
  '台北',
  '新北',
  '新竹',
  '桃園',
  '苗栗',
  '台中',
  '台南',
  '高雄',
] as const
const DISTRICTS: Record<string, string[]> = {
  台北: [
    '中正',
    '大同',
    '中山',
    '松山',
    '大安',
    '萬華',
    '信義',
    '士林',
    '北投',
    '內湖',
    '南港',
    '文山',
  ],
  新北: [
    '板橋',
    '三重',
    '中和',
    '永和',
    '新店',
    '土城',
    '蘆洲',
    '樹林',
    '鶯歌',
    '三峽',
    '淡水',
    '汐止',
    '五股',
    '泰山',
    '林口',
    '八里',
    '新莊',
  ],
  新竹: ['東區', '北區', '香山', '竹北', '竹東'],
  桃園: ['桃園', '中壢', '龜山', '楊梅'],
  苗栗: ['苗栗', '竹南', '頭份', '銅鑼'],
  台中: [
    '中區',
    '西區',
    '北區',
    '南區',
    '東區',
    '北屯',
    '西屯',
    '南屯',
    '豐原',
    '大里',
    '太平',
  ],
  台南: ['中西區', '東區', '南區', '北區', '安平', '永康', '新營', '善化'],
  高雄: ['苓雅', '前金', '三民', '左營', '楠梓', '鼓山', '前鎮', '鳳山'],
}

const DATE_RANGES = ['全部', '3天', '7天', '14天', '30天'] as const
const MARKETS = ['全部', 'listed', 'otc'] as const
const MARKET_LABELS: Record<string, string> = {
  全部: '上市櫃',
  listed: '上市',
  otc: '上櫃',
}
const SALARY_OPTIONS = [
  { label: '不限', value: 0 },
  { label: '3 萬以上', value: 30000 },
  { label: '4 萬以上', value: 40000 },
  { label: '5 萬以上', value: 50000 },
  { label: '6 萬以上', value: 60000 },
  { label: '8 萬以上', value: 80000 },
  { label: '10 萬以上', value: 100000 },
  { label: '15 萬以上', value: 150000 },
]

const PAGE_SIZE = 50

function useDebounce(value: string, ms: number) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return debounced
}

function JobsPage() {
  const { firstPage, companyMap, filterCounts } = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [source, setSource] = useState<string>('全部')
  const [industry, setIndustry] = useState<string>('全部')
  const [cities, setCities] = useState<string[]>([])
  const [districts, setDistricts] = useState<string[]>([])
  const [jobType, setJobType] = useState<string>('全部')
  const [dateRange, setDateRange] = useState<string>('7天')
  const [market, setMarket] = useState<string>('全部')
  const [salaryMin, setSalaryMin] = useState<number>(0)
  const [expanding, setExpanding] = useState(false)

  const debouncedSearch = useDebounce(search, 300)

  const sourceCountMap = useMemo(() => {
    const map: Record<string, number> = {}
    for (const s of filterCounts.sources) map[s.name] = s.count
    return map
  }, [filterCounts])

  const filters: JobFilters = useMemo(
    () => ({
      source: source !== '全部' ? source : undefined,
      search: debouncedSearch || undefined,
      cities: cities.length > 0 ? cities : undefined,
      districts: districts.length > 0 ? districts : undefined,
      jobType: jobType !== '全部' ? jobType : undefined,
      industry: industry !== '全部' ? industry : undefined,
      market: market !== '全部' ? market : undefined,
      salaryMin: salaryMin > 0 ? salaryMin : undefined,
      dateRange: dateRange !== '全部' ? dateRange : undefined,
      expanding: expanding || undefined,
    }),
    [
      source,
      debouncedSearch,
      cities,
      districts,
      jobType,
      industry,
      market,
      salaryMin,
      dateRange,
      expanding,
    ],
  )

  const isDefaultFilters =
    dateRange === '7天' &&
    !filters.source &&
    !filters.search &&
    !filters.cities &&
    !filters.districts &&
    !filters.jobType &&
    !filters.industry &&
    !filters.market &&
    !filters.salaryMin &&
    !filters.expanding

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } =
    useInfiniteQuery({
      queryKey: ['jobs', filters],
      queryFn: async ({ pageParam = 0 }) => {
        return getJobsPage({
          data: { ...filters, offset: pageParam, limit: PAGE_SIZE },
        })
      },
      initialPageParam: 0,
      getNextPageParam: (lastPage) =>
        lastPage.hasMore ? lastPage.offset + lastPage.jobs.length : undefined,
      initialData: isDefaultFilters
        ? { pages: [firstPage], pageParams: [0] }
        : undefined,
      enabled: true,
    })

  const sentinelRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage()
        }
      },
      { rootMargin: '400px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const allJobs = useMemo(
    () => data?.pages.flatMap((p) => p.jobs) ?? [],
    [data],
  )
  const total = data?.pages[0]?.total ?? 0

  const groups = useMemo(() => {
    const map = new Map<string, Job[]>()
    for (const j of allJobs) {
      const arr = map.get(j.stock_id) || []
      arr.push(j)
      map.set(j.stock_id, arr)
    }
    const result: CompanyGroup[] = []
    for (const [stockId, groupJobs] of map) {
      result.push({ stockId, company: companyMap[stockId], jobs: groupJobs })
    }
    result.sort(
      (a, b) =>
        (b.company?.salary_median_k ?? 0) - (a.company?.salary_median_k ?? 0),
    )
    return result
  }, [allJobs, companyMap])

  const loadedCount = allJobs.length

  const activeFilterTags: { label: string; clear: () => void }[] = []
  if (dateRange !== '全部' && dateRange !== '7天')
    activeFilterTags.push({
      label: `近 ${dateRange}`,
      clear: () => setDateRange('7天'),
    })
  if (dateRange === '全部')
    activeFilterTags.push({
      label: '不限時間',
      clear: () => setDateRange('7天'),
    })
  if (jobType !== '全部')
    activeFilterTags.push({ label: jobType, clear: () => setJobType('全部') })
  if (cities.length > 0)
    activeFilterTags.push({
      label: cities.join('、'),
      clear: () => {
        setCities([])
        setDistricts([])
      },
    })
  if (districts.length > 0)
    activeFilterTags.push({
      label: districts.join('、'),
      clear: () => setDistricts([]),
    })
  if (industry !== '全部')
    activeFilterTags.push({ label: industry, clear: () => setIndustry('全部') })
  if (source !== '全部')
    activeFilterTags.push({
      label: SOURCE_LABELS[source] || source,
      clear: () => setSource('全部'),
    })
  if (market !== '全部')
    activeFilterTags.push({
      label: MARKET_LABELS[market],
      clear: () => setMarket('全部'),
    })
  if (salaryMin > 0)
    activeFilterTags.push({
      label: `≥ ${(salaryMin / 10000).toFixed(0)} 萬`,
      clear: () => setSalaryMin(0),
    })
  if (expanding)
    activeFilterTags.push({ label: '擴編中', clear: () => setExpanding(false) })

  const clearAll = () => {
    setSearch('')
    setSource('全部')
    setIndustry('全部')
    setCities([])
    setDistricts([])
    setJobType('全部')
    setDateRange('7天')
    setMarket('全部')
    setSalaryMin(0)
    setExpanding(false)
  }

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <h1 className="mb-1 font-display text-2xl font-bold text-[var(--text-heading)]">
        職缺搜尋
      </h1>
      <p className="mb-4 text-sm text-[var(--text-muted)]">
        跨平台聚合 {filterCounts.total.toLocaleString()}{' '}
        筆職缺，按公司分組，一眼看懂薪資和擴編狀況
      </p>

      {/* Search */}
      <input
        type="text"
        placeholder="搜尋職缺、公司、地點..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-3 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-heading)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
      />

      {/* Filter row 1: common quick filters */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {DATE_RANGES.map((d) => (
            <option key={d} value={d}>
              {d === '全部' ? '不限時間' : `近 ${d}`}
            </option>
          ))}
        </select>
        <MultiSelect
          label="縣市"
          options={CITIES.filter((c) => c !== '全部')}
          selected={cities}
          onChange={(next) => {
            setCities(next)
            setDistricts((current) =>
              current.filter((d) =>
                next.some((c) => DISTRICTS[c]?.includes(d)),
              ),
            )
          }}
        />
        <MultiSelect
          label="區域"
          options={[...new Set(cities.flatMap((c) => DISTRICTS[c] || []))]}
          selected={districts}
          onChange={setDistricts}
          disabled={cities.length === 0}
        />
        <select
          value={salaryMin}
          onChange={(e) => setSalaryMin(Number(e.target.value))}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {SALARY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.value === 0 ? '月薪不限' : o.label}
            </option>
          ))}
        </select>
        <select
          value={jobType}
          onChange={(e) => setJobType(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {JOB_TYPES.map((t) => (
            <option key={t} value={t}>
              {t === '全部' ? '工作型態' : t}
            </option>
          ))}
        </select>
      </div>

      {/* Filter row 2: advanced */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {s === '全部'
                ? '所有來源'
                : `${SOURCE_LABELS[s]} (${(sourceCountMap[s] ?? 0).toLocaleString()})`}
            </option>
          ))}
        </select>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {INDUSTRIES.map((ind) => (
            <option key={ind} value={ind}>
              {ind === '全部' ? '所有產業' : ind}
            </option>
          ))}
        </select>
        <select
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-1.5 text-xs text-[var(--text-body)]"
        >
          {MARKETS.map((m) => (
            <option key={m} value={m}>
              {MARKET_LABELS[m]}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setExpanding(!expanding)}
          className={`rounded-lg border px-2 py-1.5 text-xs font-medium transition ${
            expanding
              ? 'border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--text-heading)]'
              : 'border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:border-[var(--accent)]'
          }`}
        >
          擴編中
        </button>
      </div>

      {/* Active filter tags */}
      {activeFilterTags.length > 0 && (
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-[var(--text-muted)]">篩選：</span>
          {activeFilterTags.map((tag) => (
            <button
              key={tag.label}
              type="button"
              onClick={tag.clear}
              className="group flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--text-heading)] transition hover:bg-[var(--accent)]"
            >
              {tag.label}
              <span className="text-[10px] opacity-50 group-hover:opacity-100">
                ✕
              </span>
            </button>
          ))}
          {activeFilterTags.length > 1 && (
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--text-heading)]"
            >
              清除全部
            </button>
          )}
        </div>
      )}

      {/* Result count */}
      <p className="mb-4 text-xs text-[var(--text-muted)]">
        {isLoading
          ? '載入中...'
          : `共 ${total.toLocaleString()} 筆職缺，已載入 ${loadedCount.toLocaleString()} 筆，${groups.length} 家公司`}
      </p>

      {/* Job groups */}
      <div className="space-y-4">
        {groups.map((g) => (
          <CompanyJobGroup key={g.stockId} group={g} />
        ))}
      </div>

      <div
        ref={sentinelRef}
        className="py-8 text-center text-sm text-[var(--text-muted)]"
      >
        {isFetchingNextPage
          ? '載入更多職缺中...'
          : hasNextPage
            ? ''
            : loadedCount > 0
              ? '已顯示全部職缺'
              : isLoading
                ? '載入中...'
                : '沒有符合條件的職缺'}
      </div>
    </main>
  )
}

type CompanyGroup = {
  stockId: string
  company: Company | undefined
  jobs: Job[]
}

function CompanyJobGroup({ group }: { group: CompanyGroup }) {
  const [open, setOpen] = useState(false)
  const { company, jobs } = group
  const salaryWan = company?.salary_median_k
    ? (company.salary_median_k / 10).toFixed(0)
    : null
  const changePct = company?.salary_median_change_pct
  const initial = (
    company?.short_name ||
    group.jobs[0]?.company_name ||
    '?'
  ).charAt(0)
  const name =
    company?.short_name || group.jobs[0]?.company_name || group.stockId
  const marketLabel =
    company?.market === 'listed'
      ? '上市'
      : company?.market === 'otc'
        ? '上櫃'
        : null

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 bg-[var(--bg-elevated)] px-4 py-2.5 text-left transition hover:bg-[var(--border)]"
      >
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--bg-surface)] text-xs font-bold text-[var(--text-heading)]">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Link
              to="/company/$stockId"
              params={{ stockId: group.stockId }}
              className="text-sm font-bold text-[var(--text-heading)] hover:text-[var(--accent)]"
              onClick={(e) => e.stopPropagation()}
            >
              {name}
            </Link>
            <span className="text-[11px] text-[var(--text-muted)]">
              {group.stockId}
            </span>
            {marketLabel && (
              <span className="rounded bg-[var(--bg-surface)] px-1 py-px text-[10px] text-[var(--text-muted)]">
                {marketLabel}
              </span>
            )}
            {company?.industry && (
              <span className="hidden text-[11px] text-[var(--text-muted)] sm:inline">
                · {company.industry}
              </span>
            )}
          </div>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2">
          {salaryWan && (
            <span className="text-sm tabular-nums text-[var(--accent)]">
              <span className="hidden text-[10px] font-normal text-[var(--text-muted)] sm:inline">
                年薪中位{' '}
              </span>
              <span className="font-bold">{salaryWan}萬</span>
            </span>
          )}
          {changePct !== null && changePct !== undefined && (
            <span
              className={`rounded px-1 py-px text-[10px] font-semibold ${
                changePct > 0
                  ? 'bg-[var(--green-soft)] text-[var(--green-positive)]'
                  : changePct < 0
                    ? 'bg-[var(--red-soft)] text-[var(--red-negative)]'
                    : 'text-[var(--text-muted)]'
              }`}
            >
              {changePct > 0 ? (
                <TrendingUp size={12} className="inline" />
              ) : changePct < 0 ? (
                <TrendingDown size={12} className="inline" />
              ) : null}
              年增{Math.abs(changePct).toFixed(1)}%
            </span>
          )}
          {company?.job_count_trend === 'expanding' && (
            <span className="rounded bg-[var(--green-soft)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--green-positive)]">
              擴編中
            </span>
          )}
          {company?.job_count_trend === 'shrinking' && (
            <span className="rounded bg-[var(--red-soft)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--red-negative)]">
              縮編中
            </span>
          )}
          <span className="text-xs text-[var(--text-muted)]">
            {jobs.length} 缺
          </span>
          <span className="text-xs text-[var(--text-muted)]">
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        </div>
      </button>

      {open &&
        jobs.map((job, i) => {
          const clean = (s: string | null | undefined) => {
            if (!s || s === 'None' || s === 'nan' || s === 'NaN') return null
            return (
              s
                .replace(/, Taiwan/gi, '')
                .replace(/, TW/gi, '')
                .replace(/, TPE/gi, '')
                .replace(/, TPQ/gi, '')
                .trim() || null
            )
          }
          const loc = clean(job.location)
          const dateShort =
            job.date_posted &&
            job.date_posted !== 'None' &&
            job.date_posted !== 'nan'
              ? job.date_posted.slice(5)
              : null
          const salaryText =
            job.salary_min && job.salary_min > 0
              ? job.salary_max && job.salary_max > job.salary_min
                ? `${(job.salary_min / 1000).toFixed(0)}K–${(job.salary_max / 1000).toFixed(0)}K`
                : `${(job.salary_min / 1000).toFixed(0)}K+`
              : null

          return (
            <a
              key={job.id || `${job.title}-${i}`}
              href={`/go/${job.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center gap-3 px-4 py-2.5 no-underline transition hover:bg-[var(--bg-elevated)] ${
                i % 2 === 1 ? 'bg-[var(--bg)]' : ''
              }`}
            >
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-[var(--text-heading)]">
                  {job.title}
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  <span>{loc || '台灣'}</span>
                  {dateShort && <span>{dateShort}</span>}
                  {salaryText && (
                    <span className="text-[var(--accent)]">{salaryText}</span>
                  )}
                </div>
              </div>
              <SourceBadge source={job.source} />
            </a>
          )
        })}
    </div>
  )
}

const SOURCE_STYLES: Record<
  string,
  { bg: string; text: string; label: string }
> = {
  '104': { bg: 'bg-[#e535351a]', text: 'text-[#e53535]', label: '104' },
  linkedin: { bg: 'bg-[#0a66c21a]', text: 'text-[#0a66c2]', label: 'LinkedIn' },
  indeed: { bg: 'bg-[#6c3baa1a]', text: 'text-[#6c3baa]', label: 'Indeed' },
  yourator: { bg: 'bg-[#00b8941a]', text: 'text-[#00b894]', label: 'Yourator' },
  hackernews: { bg: 'bg-[#ff66001a]', text: 'text-[#ff6600]', label: 'HN' },
  arcdev: { bg: 'bg-[#6c5ce71a]', text: 'text-[#6c5ce7]', label: 'Arc' },
  wwr: { bg: 'bg-[#2d6cdf1a]', text: 'text-[#2d6cdf]', label: 'WWR' },
  remoteok: { bg: 'bg-[#0d9b6e1a]', text: 'text-[#0d9b6e]', label: 'RemoteOK' },
  cakeresume: { bg: 'bg-[#00bcd41a]', text: 'text-[#00bcd4]', label: 'Cake' },
  justremote: {
    bg: 'bg-[#4a90d91a]',
    text: 'text-[#4a90d9]',
    label: 'JustRemote',
  },
  remotive: { bg: 'bg-[#e535351a]', text: 'text-[#e53535]', label: 'Remotive' },
  dynamitejobs: {
    bg: 'bg-[#f5a6231a]',
    text: 'text-[#f5a623]',
    label: 'Dynamite',
  },
  careervault: {
    bg: 'bg-[#34495e1a]',
    text: 'text-[#34495e]',
    label: 'CareerVault',
  },
  himalayas: {
    bg: 'bg-[#1a73e81a]',
    text: 'text-[#1a73e8]',
    label: 'Himalayas',
  },
  workingnomads: {
    bg: 'bg-[#e67e221a]',
    text: 'text-[#e67e22]',
    label: 'WNomads',
  },
}

function SourceBadge({ source }: { source: string }) {
  const style = SOURCE_STYLES[source]
  if (style) {
    return (
      <span
        className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${style.bg} ${style.text}`}
      >
        {style.label}
      </span>
    )
  }
  return (
    <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[var(--bg-elevated)] text-[var(--text-muted)]">
      {source}
    </span>
  )
}

function MultiSelect({
  label,
  options,
  selected,
  onChange,
  disabled = false,
}: {
  label: string
  options: string[]
  selected: string[]
  onChange: (values: string[]) => void
  disabled?: boolean
}) {
  return (
    <details className="relative">
      <summary
        className={`cursor-pointer list-none rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-2 text-xs text-[var(--text-body)] ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
      >
        {selected.length > 0
          ? `${label}：${selected.join('、')}`
          : `選擇${label}`}
      </summary>
      {!disabled && (
        <div className="absolute left-0 top-full z-10 mt-1 max-h-64 min-w-36 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] p-2 shadow-lg">
          {options.map((option) => (
            <label
              key={option}
              className="flex cursor-pointer items-center gap-2 px-2 py-1.5 text-xs text-[var(--text-body)] hover:bg-[var(--bg-surface)]"
            >
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={(event) =>
                  onChange(
                    event.target.checked
                      ? [...selected, option]
                      : selected.filter((value) => value !== option),
                  )
                }
              />
              {option}
            </label>
          ))}
        </div>
      )}
    </details>
  )
}
