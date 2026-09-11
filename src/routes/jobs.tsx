import { createFileRoute, Link } from '@tanstack/react-router'
import Fuse from 'fuse.js'
import { useMemo, useState } from 'react'
import { getCompanies, INDUSTRIES } from '#/utils/companies.functions'
import { getJobs } from '#/utils/jobs.functions'
import type { Company, Job } from '#/utils/types'

export const Route = createFileRoute('/jobs')({
  loader: async () => {
    const [jobs, companies] = await Promise.all([getJobs(), getCompanies()])
    const companyMap: Record<string, Company> = {}
    for (const c of companies) companyMap[c.stock_id] = c
    return { jobs, companyMap }
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
] as const
const JOB_TYPES = [
  '全部',
  '遠端/混合',
  '全球遠端',
  'AI 相關',
  '擴編中',
] as const

const REMOTE_KEYWORDS = [
  'remote work',
  'remote position',
  'remote job',
  'remote role',
  'fully remote',
  'work remotely',
  'remote-first',
  '遠端工作',
  '遠端辦公',
  '遠距工作',
  '遠距辦公',
  'work from home',
  'wfh',
  '在家工作',
  'hybrid work',
  '混合辦公',
  '混合工作',
  '居家辦公',
  '居家工作',
  '彈性工作地點',
  '遠端/現場',
  '現場/遠端',
]
const AI_KEYWORDS = [
  'ai',
  '人工智慧',
  'machine learning',
  'deep learning',
  'nlp',
  'llm',
  'data scientist',
  '機器學習',
  '深度學習',
  'ml engineer',
  'ai engineer',
]
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

const CITY_ALIASES: Record<string, string[]> = {
  台北: ['台北', 'Taipei', 'TPE'],
  新北: [
    '新北',
    'New Taipei',
    'TPQ',
    '三重',
    '板橋',
    '中和',
    '永和',
    '土城',
    '汐止',
    '林口',
    '淡水',
    '蘆洲',
    '樹林',
  ],
  新竹: ['新竹', 'Hsinchu', 'Zhubei', '竹北', '竹東'],
  桃園: ['桃園', 'Taoyuan', '中壢', '龜山', '楊梅'],
  苗栗: ['苗栗', 'Miaoli', '竹南', '頭份'],
  台中: ['台中', 'Taichung'],
  台南: ['台南', 'Tainan', '善化', '新營'],
  高雄: ['高雄', 'Kaohsiung', '楠梓', '前鎮'],
}

type CompanyGroup = {
  stockId: string
  company: Company | undefined
  jobs: Job[]
}

function buildJobPostingJsonLd(job: Job, company: Company | undefined) {
  const jsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'JobPosting',
    title: job.title,
    ...(job.date_posted &&
      job.date_posted !== 'None' &&
      job.date_posted !== 'nan' && { datePosted: job.date_posted }),
    ...(job.description && { description: job.description }),
    ...(job.job_url && { url: job.job_url }),
    hiringOrganization: {
      '@type': 'Organization',
      name: company?.name || job.company_name,
      ...(company?.address && {
        address: { '@type': 'PostalAddress', streetAddress: company.address },
      }),
    },
    jobLocation: {
      '@type': 'Place',
      address: {
        '@type': 'PostalAddress',
        addressLocality: job.location || '台灣',
        addressCountry: 'TW',
      },
    },
    ...(job.job_type === 'global_remote' && { jobLocationType: 'TELECOMMUTE' }),
  }
  if (job.salary_min || job.salary_max) {
    jsonLd.baseSalary = {
      '@type': 'MonetaryAmount',
      currency: 'TWD',
      value: {
        '@type': 'QuantitativeValue',
        ...(job.salary_min && { minValue: job.salary_min }),
        ...(job.salary_max && { maxValue: job.salary_max }),
        unitText: 'MONTH',
      },
    }
  }
  return jsonLd
}

function JobsPage() {
  const { jobs, companyMap } = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [source, setSource] = useState<string>('全部')
  const [industry, setIndustry] = useState<string>('全部')
  const [city, setCity] = useState<string>('全部')
  const [jobType, setJobType] = useState<string>('全部')

  const fuse = useMemo(
    () =>
      new Fuse(jobs, {
        keys: [
          { name: 'title', weight: 3 },
          { name: 'company_name', weight: 2 },
          { name: 'location', weight: 1 },
        ],
        threshold: 0.3,
      }),
    [jobs],
  )

  const groups = useMemo(() => {
    const q = search.trim().toLowerCase()
    let list: Job[]

    if (q) {
      const isCJK = /[一-鿿㐀-䶿぀-ゟ゠-ヿ가-힯]/.test(q)

      const wordBoundary = (text: string, term: string) => {
        const i = text.toLowerCase().indexOf(term)
        if (i === -1) return false
        const before = i === 0 || /[\s\-_/(),.]/.test(text[i - 1])
        const after =
          i + term.length >= text.length ||
          /[\s\-_/(),.]/.test(text[i + term.length])
        return before && after
      }

      const containsText = (text: string, term: string) =>
        text.toLowerCase().includes(term)

      if (q.length <= 3) {
        const match = isCJK ? containsText : wordBoundary
        list = jobs.filter((j) => match(j.title, q) || match(j.company_name, q))
      } else {
        list = fuse.search(q).map((r) => r.item)
      }
    } else {
      list = [...jobs]
    }

    if (source !== '全部') list = list.filter((j) => j.source === source)
    if (jobType === '遠端/混合') {
      list = list.filter((j) => {
        if (j.job_type === 'remote' || j.job_type === 'global_remote')
          return true
        const text = (
          (j.title || '') +
          ' ' +
          (j.location || '') +
          ' ' +
          (j.description || '')
        ).toLowerCase()
        return REMOTE_KEYWORDS.some((kw) => text.includes(kw))
      })
    } else if (jobType === '全球遠端') {
      list = list.filter((j) => j.job_type === 'global_remote')
    } else if (jobType === 'AI 相關') {
      list = list.filter((j) => {
        const text = (
          (j.title || '') +
          ' ' +
          (j.description || '')
        ).toLowerCase()
        return AI_KEYWORDS.some((kw) => text.includes(kw))
      })
    } else if (jobType === '擴編中') {
      list = list.filter(
        (j) => companyMap[j.stock_id]?.job_count_trend === 'expanding',
      )
    }
    if (city !== '全部') {
      const aliases = CITY_ALIASES[city] || [city]
      list = list.filter((j) => {
        const loc = (j.location || '').toLowerCase()
        return aliases.some((a) => loc.includes(a.toLowerCase()))
      })
    }
    if (industry !== '全部') {
      const indKey = industry.replace('業', '')
      list = list.filter((j) => {
        const ci = companyMap[j.stock_id]?.industry
        if (!ci) return false
        const ciKey = ci.replace('業', '')
        return ci.includes(indKey) || indKey.includes(ciKey)
      })
    }

    const map = new Map<string, Job[]>()
    for (const j of list) {
      const arr = map.get(j.stock_id) || []
      arr.push(j)
      map.set(j.stock_id, arr)
    }

    const result: CompanyGroup[] = []
    for (const [stockId, groupJobs] of map) {
      result.push({ stockId, company: companyMap[stockId], jobs: groupJobs })
    }

    result.sort((a, b) => {
      const sa = a.company?.salary_median_k ?? 0
      const sb = b.company?.salary_median_k ?? 0
      return sb - sa
    })

    return result
  }, [jobs, search, source, industry, city, jobType, fuse, companyMap])

  const totalJobs = groups.reduce((s, g) => s + g.jobs.length, 0)

  if (jobs.length === 0) {
    return (
      <main className="page-wrap px-4 py-16 text-center">
        <h1 className="mb-4 font-display text-2xl font-bold text-[var(--text-heading)]">
          職缺搜尋
        </h1>
        <p className="text-[var(--text-body)]">
          職缺資料正在收集中，請稍後再來。
        </p>
      </main>
    )
  }

  // biome-ignore lint/correctness/useHookAtTopLevel: JSON-LD memo depends on filtered data
  const jobPostingsJsonLd = useMemo(() => {
    const allJobs = groups.flatMap((g) => g.jobs.slice(0, 5)).slice(0, 50)
    return allJobs.map((job) =>
      buildJobPostingJsonLd(job, companyMap[job.stock_id]),
    )
  }, [groups, companyMap])

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      {jobPostingsJsonLd.length > 0 && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(jobPostingsJsonLd),
          }}
        />
      )}
      <h1 className="mb-1 font-display text-2xl font-bold text-[var(--text-heading)]">
        職缺搜尋
      </h1>
      <p className="mb-6 text-sm text-[var(--text-muted)]">
        跨平台聚合 LinkedIn + Indeed，按公司分組，一眼看懂薪資和擴編狀況
      </p>

      {/* Search + Filters — one compact row */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          type="text"
          placeholder="搜尋職缺、公司、地點..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[200px] flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-[var(--text-heading)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
        />
        <select
          value={jobType}
          onChange={(e) => setJobType(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-2 text-xs text-[var(--text-body)]"
        >
          {JOB_TYPES.map((t) => (
            <option key={t} value={t}>
              {t === '全部' ? '所有類型' : t}
            </option>
          ))}
        </select>
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-2 text-xs text-[var(--text-body)]"
        >
          {CITIES.map((c) => (
            <option key={c} value={c}>
              {c === '全部' ? '所有地區' : c}
            </option>
          ))}
        </select>
        <select
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-2 text-xs text-[var(--text-body)]"
        >
          {INDUSTRIES.map((ind) => (
            <option key={ind} value={ind}>
              {ind === '全部' ? '所有產業' : ind}
            </option>
          ))}
        </select>
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-2 py-2 text-xs text-[var(--text-body)]"
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {
                {
                  全部: '所有來源',
                  '104': '104',
                  linkedin: 'LinkedIn',
                  indeed: 'Indeed',
                  yourator: 'Yourator',
                  hackernews: 'HN Hiring',
                  arcdev: 'Arc.dev',
                  wwr: 'WWR',
                  remoteok: 'RemoteOK',
                }[s]
              }
            </option>
          ))}
        </select>
      </div>

      {/* Active filters indicator */}
      {(jobType !== '全部' ||
        city !== '全部' ||
        industry !== '全部' ||
        source !== '全部') && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-xs text-[var(--text-muted)]">篩選中：</span>
          {jobType !== '全部' && (
            <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--text-heading)]">
              {jobType}
            </span>
          )}
          {city !== '全部' && (
            <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--text-heading)]">
              {city}
            </span>
          )}
          {industry !== '全部' && (
            <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--text-heading)]">
              {industry}
            </span>
          )}
          {source !== '全部' && (
            <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--text-heading)]">
              {source}
            </span>
          )}
          <button
            type="button"
            onClick={() => {
              setJobType('全部')
              setCity('全部')
              setIndustry('全部')
              setSource('全部')
            }}
            className="text-xs text-[var(--text-muted)] hover:text-[var(--text-heading)]"
          >
            清除全部
          </button>
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-center gap-2" hidden>
        {INDUSTRIES.map((ind) => (
          <button
            type="button"
            key={ind}
            onClick={() => setIndustry(ind)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              industry === ind
                ? 'bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--text-heading)]'
                : 'bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)]'
            }`}
          >
            {ind}
          </button>
        ))}
      </div>

      <p className="mb-4 text-xs text-[var(--text-muted)]">
        {totalJobs} 筆職缺，{groups.length} 家公司
      </p>

      <div className="space-y-4">
        {groups.map((g) => (
          <CompanyJobGroup key={g.stockId} group={g} />
        ))}
      </div>
    </main>
  )
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

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
      {/* Company header — click to toggle */}
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
              {changePct > 0 ? '▲' : changePct < 0 ? '▼' : ''}年增
              {Math.abs(changePct).toFixed(1)}%
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
            {open ? '▾' : '▸'}
          </span>
        </div>
      </button>

      {/* Job list — collapsed by default */}
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
                <div className="mt-0.5 text-xs text-[var(--text-muted)]">
                  {loc || '台灣'}
                  {dateShort && <span className="ml-2">{dateShort}</span>}
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
  linkedin: { bg: 'bg-[#0a66c21a]', text: 'text-[#0a66c2]', label: 'LinkedIn' },
  indeed: { bg: 'bg-[#6c3baa1a]', text: 'text-[#6c3baa]', label: 'Indeed' },
  yourator: { bg: 'bg-[#00b8941a]', text: 'text-[#00b894]', label: 'Yourator' },
  hackernews: { bg: 'bg-[#ff66001a]', text: 'text-[#ff6600]', label: 'HN' },
  arcdev: { bg: 'bg-[#6c5ce71a]', text: 'text-[#6c5ce7]', label: 'Arc' },
  wwr: { bg: 'bg-[#2d6cdf1a]', text: 'text-[#2d6cdf]', label: 'WWR' },
  remoteok: { bg: 'bg-[#0d9b6e1a]', text: 'text-[#0d9b6e]', label: 'RemoteOK' },
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
