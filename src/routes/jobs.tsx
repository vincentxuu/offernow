import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import Fuse from 'fuse.js'
import { getJobs } from '#/utils/jobs.functions'
import { getCompanies, INDUSTRIES } from '#/utils/companies.functions'
import type { Job, Company } from '#/utils/types'

export const Route = createFileRoute('/jobs')({
  loader: async () => {
    const [jobs, companies] = await Promise.all([getJobs(), getCompanies()])
    const companyMap: Record<string, Company> = {}
    for (const c of companies) companyMap[c.stock_id] = c
    return { jobs, companyMap }
  },
  component: JobsPage,
})

const SOURCES = ['全部', '104', 'linkedin', 'indeed'] as const
const JOB_TYPES = ['全部', '遠端/混合', 'AI 相關'] as const

const REMOTE_KEYWORDS = ['remote work', 'remote position', 'remote job', 'remote role', 'fully remote', 'work remotely', 'remote-first', '遠端工作', '遠端辦公', '遠距工作', '遠距辦公', 'work from home', 'wfh', '在家工作', 'hybrid work', '混合辦公', '混合工作', '居家辦公', '居家工作', '彈性工作地點', '遠端/現場', '現場/遠端']
const AI_KEYWORDS = ['ai', '人工智慧', 'machine learning', 'deep learning', 'nlp', 'llm', 'data scientist', '機器學習', '深度學習', 'ml engineer', 'ai engineer']
const CITIES = ['全部', '台北', '新北', '新竹', '桃園', '苗栗', '台中', '台南', '高雄'] as const

const CITY_ALIASES: Record<string, string[]> = {
  '台北': ['台北', 'Taipei', 'TPE'],
  '新北': ['新北', 'New Taipei', 'TPQ', '三重', '板橋', '中和', '永和', '土城', '汐止', '林口', '淡水', '蘆洲', '樹林'],
  '新竹': ['新竹', 'Hsinchu', 'Zhubei', '竹北', '竹東'],
  '桃園': ['桃園', 'Taoyuan', '中壢', '龜山', '楊梅'],
  '苗栗': ['苗栗', 'Miaoli', '竹南', '頭份'],
  '台中': ['台中', 'Taichung'],
  '台南': ['台南', 'Tainan', '善化', '新營'],
  '高雄': ['高雄', 'Kaohsiung', '楠梓', '前鎮'],
}

type CompanyGroup = {
  stockId: string
  company: Company | undefined
  jobs: Job[]
}

function JobsPage() {
  const { jobs, companyMap } = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [source, setSource] = useState<string>('全部')
  const [industry, setIndustry] = useState<string>('全部')
  const [city, setCity] = useState<string>('全部')
  const [jobType, setJobType] = useState<string>('全部')

  const fuse = useMemo(
    () => new Fuse(jobs, {
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
      const wordBoundary = (text: string, term: string) => {
        const i = text.toLowerCase().indexOf(term)
        if (i === -1) return false
        const before = i === 0 || /[\s\-_/(),.]/.test(text[i - 1])
        const after = i + term.length >= text.length || /[\s\-_/(),.]/.test(text[i + term.length])
        return before && after
      }

      if (q.length <= 3) {
        list = jobs.filter(
          (j) =>
            wordBoundary(j.title, q) ||
            wordBoundary(j.company_name, q),
        )
      } else {
        list = fuse.search(q).map((r) => r.item)
      }
    } else {
      list = [...jobs]
    }

    if (source !== '全部') list = list.filter((j) => j.source === source)
    if (jobType === '遠端/混合') {
      list = list.filter((j) => {
        if (j.job_type === 'remote') return true
        const text = ((j.title || '') + ' ' + (j.location || '') + ' ' + (j.description || '')).toLowerCase()
        return REMOTE_KEYWORDS.some((kw) => text.includes(kw))
      })
    } else if (jobType === 'AI 相關') {
      list = list.filter((j) => {
        const text = ((j.title || '') + ' ' + (j.description || '')).toLowerCase()
        return AI_KEYWORDS.some((kw) => text.includes(kw))
      })
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
        <h1 className="mb-4 font-display text-2xl font-bold text-[var(--text-heading)]">職缺搜尋</h1>
        <p className="text-[var(--text-body)]">職缺資料正在收集中，請稍後再來。</p>
      </main>
    )
  }

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <h1 className="mb-1 font-display text-2xl font-bold text-[var(--text-heading)]">職缺搜尋</h1>
      <p className="mb-6 text-sm text-[var(--text-muted)]">
        跨平台聚合 LinkedIn + Indeed，按公司分組，一眼看懂薪資和擴編狀況
      </p>

      <div className="mb-4 max-w-xl">
        <input
          type="text"
          placeholder="搜尋職缺標題、公司名、地點..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3 text-sm text-[var(--text-heading)] shadow-[var(--shadow)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
        />
      </div>

      {/* Filters */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">類型</span>
        {JOB_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setJobType(t)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              jobType === t
                ? 'bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--text-heading)]'
                : 'bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">來源</span>
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => setSource(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              source === s
                ? 'bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--text-heading)]'
                : 'bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)]'
            }`}
          >
            {s === '全部' ? '全部' : s === 'linkedin' ? 'LinkedIn' : s === 'indeed' ? 'Indeed' : '104'}
          </button>
        ))}
      </div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">地區</span>
        {CITIES.map((c) => (
          <button
            key={c}
            onClick={() => setCity(c)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              city === c
                ? 'bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--text-heading)]'
                : 'bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)]'
            }`}
          >
            {c}
          </button>
        ))}
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-[var(--text-muted)]">產業</span>
        {INDUSTRIES.map((ind) => (
          <button
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
  const salaryWan = company?.salary_median_k ? (company.salary_median_k / 10).toFixed(0) : null
  const changePct = company?.salary_median_change_pct
  const initial = (company?.short_name || group.jobs[0]?.company_name || '?').charAt(0)
  const name = company?.short_name || group.jobs[0]?.company_name || group.stockId

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
      {/* Company header — click to toggle */}
      <button
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
            <span className="text-[11px] text-[var(--text-muted)]">{group.stockId}</span>
            {company?.industry && (
              <span className="hidden text-[11px] text-[var(--text-muted)] sm:inline">· {company.industry}</span>
            )}
          </div>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2">
          {salaryWan && (
            <span className="text-sm tabular-nums text-[var(--accent)]">
              <span className="hidden text-[10px] font-normal text-[var(--text-muted)] sm:inline">年薪中位 </span>
              <span className="font-bold">{salaryWan}萬</span>
            </span>
          )}
          {changePct !== null && changePct !== undefined && (
            <span className={`rounded px-1 py-px text-[10px] font-semibold ${
              changePct > 0
                ? 'bg-[var(--green-soft)] text-[var(--green-positive)]'
                : changePct < 0
                  ? 'bg-[var(--red-soft)] text-[var(--red-negative)]'
                  : 'text-[var(--text-muted)]'
            }`}>
              {changePct > 0 ? '▲' : changePct < 0 ? '▼' : ''}年增{Math.abs(changePct).toFixed(1)}%
            </span>
          )}
          <span className="text-xs text-[var(--text-muted)]">{jobs.length} 缺</span>
          <span className="text-xs text-[var(--text-muted)]">{open ? '▾' : '▸'}</span>
        </div>
      </button>

      {/* Job list — collapsed by default */}
      {open && jobs.map((job, i) => {
        const clean = (s: string | null | undefined) => {
          if (!s || s === 'None' || s === 'nan' || s === 'NaN') return null
          return s.replace(/, Taiwan/gi, '').replace(/, TW/gi, '').replace(/, TPE/gi, '').replace(/, TPQ/gi, '').trim() || null
        }
        const loc = clean(job.location)
        const dateShort = job.date_posted && job.date_posted !== 'None' && job.date_posted !== 'nan'
          ? job.date_posted.slice(5) : null

        return (
          <a
            key={`${job.title}-${i}`}
            href={job.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`flex items-center gap-3 px-4 py-2.5 no-underline transition hover:bg-[var(--bg-elevated)] ${
              i % 2 === 1 ? 'bg-[var(--bg)]' : ''
            }`}
          >
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-[var(--text-heading)]">{job.title}</div>
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

function SourceBadge({ source }: { source: string }) {
  if (source === 'linkedin') {
    return <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[#0a66c21a] text-[#0a66c2]">LinkedIn</span>
  }
  if (source === 'indeed') {
    return <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[#6c3baa1a] text-[#6c3baa]">Indeed</span>
  }
  return <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[var(--bg-elevated)] text-[var(--text-muted)]">{source}</span>
}
