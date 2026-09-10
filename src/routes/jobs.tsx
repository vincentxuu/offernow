import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import Fuse from 'fuse.js'
import { getJobs } from '#/lib/data'
import type { Job } from '#/lib/types'

export const Route = createFileRoute('/jobs')({
  loader: () => getJobs(),
  component: JobsPage,
})

const SOURCES = ['全部', 'linkedin', 'indeed'] as const

function JobsPage() {
  const jobs = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [source, setSource] = useState<string>('全部')
  const [showCount, setShowCount] = useState(50)

  const fuse = useMemo(
    () =>
      new Fuse(jobs, {
        keys: [
          { name: 'title', weight: 3 },
          { name: 'company_name', weight: 2 },
          { name: 'location', weight: 1 },
        ],
        threshold: 0.3,
        includeScore: true,
      }),
    [jobs],
  )

  const filtered = useMemo(() => {
    let list: Job[]

    if (search.trim()) {
      list = fuse.search(search.trim()).map((r) => r.item)
    } else {
      list = [...jobs]
    }

    if (source !== '全部') {
      list = list.filter((j) => j.source === source)
    }

    return list
  }, [jobs, search, source, fuse])

  const companyCount = new Set(filtered.map((j) => j.stock_id)).size

  if (jobs.length === 0) {
    return (
      <main className="page-wrap px-4 py-16 text-center">
        <h1 className="mb-4 font-display text-2xl font-bold text-[var(--text-heading)]">
          職缺搜尋
        </h1>
        <p className="mb-2 text-[var(--text-body)]">
          職缺資料正在收集中，請稍後再來。
        </p>
        <p className="text-sm text-[var(--text-muted)]">
          我們正在從 LinkedIn、Indeed 等平台收集台灣上市櫃公司的職缺。
        </p>
        <Link
          to="/"
          className="mt-6 inline-block text-sm font-medium text-[var(--text-body)] hover:text-[var(--text-heading)]"
        >
          ← 先看看公司資料
        </Link>
      </main>
    )
  }

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <section className="mb-6">
        <h1 className="mb-1 font-display text-2xl font-bold text-[var(--text-heading)]">
          職缺搜尋
        </h1>
        <p className="text-sm text-[var(--text-muted)]">
          跨平台聚合，一次搜尋 LinkedIn + Indeed 的台灣上市櫃職缺
        </p>
      </section>

      {/* Search */}
      <div className="mb-4 max-w-2xl">
        <input
          type="text"
          placeholder="搜尋職缺標題、公司名、地點..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3 text-sm text-[var(--text-heading)] shadow-[var(--shadow)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--accent)]"
        />
      </div>

      {/* Source chips */}
      <div className="mb-4 flex gap-2">
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => { setSource(s); setShowCount(50) }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              source === s
                ? 'border border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--text-heading)]'
                : 'border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:border-[var(--accent)]'
            }`}
          >
            {s === '全部' ? '全部' : s === 'linkedin' ? 'LinkedIn' : 'Indeed'}
          </button>
        ))}
      </div>

      {/* Count */}
      <p className="mb-4 text-xs text-[var(--text-muted)]">
        共 {filtered.length} 筆職缺，來自 {companyCount} 家公司
        {search.trim() ? ` · 搜尋「${search.trim()}」` : ''}
      </p>

      {/* Job List */}
      <div className="space-y-2">
        {filtered.slice(0, showCount).map((job, i) => (
          <JobRow key={`${job.stock_id}-${job.title}-${i}`} job={job} />
        ))}
      </div>

      {filtered.length > showCount && (
        <button
          onClick={() => setShowCount((c) => c + 50)}
          className="mt-6 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] py-2 text-sm font-medium text-[var(--text-body)] transition hover:border-[var(--accent)]"
        >
          載入更多（還有 {filtered.length - showCount} 筆）
        </button>
      )}

      {filtered.length === 0 && (
        <p className="mt-12 text-center text-sm text-[var(--text-muted)]">
          找不到符合條件的職缺。試試其他關鍵字？
        </p>
      )}
    </main>
  )
}

function JobRow({ job }: { job: Job }) {
  const salaryStr =
    job.salary_min || job.salary_max
      ? `${job.salary_min?.toLocaleString() ?? '?'} – ${job.salary_max?.toLocaleString() ?? '?'}`
      : null

  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3 transition hover:border-[var(--accent)] hover:shadow-[var(--shadow)]">
      {/* Company initial */}
      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--bg-elevated)] text-xs font-bold text-[var(--text-heading)]">
        {job.company_name.charAt(0)}
      </div>

      {/* Main content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-[var(--text-heading)] hover:text-[var(--accent)]"
            >
              {job.title}
            </a>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-[var(--text-muted)]">
              <Link
                to="/company/$stockId"
                params={{ stockId: job.stock_id }}
                className="font-medium text-[var(--text-body)] hover:text-[var(--text-heading)]"
              >
                {job.company_name}
              </Link>
              {job.location && <span>· {job.location}</span>}
              {job.date_posted && job.date_posted !== 'None' && (
                <span>· {job.date_posted}</span>
              )}
            </div>
          </div>

          <div className="flex flex-shrink-0 items-center gap-2">
            {salaryStr && (
              <span className="text-xs font-medium text-[var(--text-heading)]">
                {salaryStr}
              </span>
            )}
            <SourceBadge source={job.source} />
          </div>
        </div>
      </div>
    </div>
  )
}

function SourceBadge({ source }: { source: string }) {
  if (source === 'linkedin') {
    return (
      <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[#0a66c21a] text-[#0a66c2]">
        LinkedIn
      </span>
    )
  }
  if (source === 'indeed') {
    return (
      <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[#6c3baa1a] text-[#6c3baa]">
        Indeed
      </span>
    )
  }
  return (
    <span className="rounded px-1.5 py-0.5 text-[10px] font-semibold bg-[var(--bg-elevated)] text-[var(--text-muted)]">
      {source}
    </span>
  )
}
