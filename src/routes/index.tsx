import { createFileRoute } from '@tanstack/react-router'
import Fuse from 'fuse.js'
import { useMemo, useState } from 'react'
import { CompanyCard } from '#/components/CompanyCard'
import { Stat } from '#/components/Stat'
import type { IndustryTrend } from '#/utils/companies.functions'
import {
  getCompanies,
  getIndustryTrends,
  INDUSTRIES,
} from '#/utils/companies.functions'
import type { Company } from '#/utils/types'

export const Route = createFileRoute('/')({
  loader: async () => {
    const [companies, trends] = await Promise.all([
      getCompanies(),
      getIndustryTrends(),
    ])
    return { companies, trends }
  },
  component: HomePage,
})

function HomePage() {
  const { companies, trends } = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [industry, setIndustry] = useState('全部')
  const [sortBy, setSortBy] = useState<'salary' | 'name' | 'eps' | 'marketCap'>(
    'salary',
  )
  const [showCount, setShowCount] = useState(60)

  const totalCompanies = companies.length
  const totalWithSalary = companies.filter(
    (c) => c.salary_median_k !== null,
  ).length

  const fuse = useMemo(
    () =>
      new Fuse(
        companies.filter((c) => c.salary_median_k !== null),
        {
          keys: [
            { name: 'short_name', weight: 3 },
            { name: 'name', weight: 2 },
            { name: 'stock_id', weight: 2 },
            { name: 'industry', weight: 1 },
          ],
          threshold: 0.3,
          includeScore: true,
        },
      ),
    [companies],
  )

  const filtered = useMemo(() => {
    let list: Company[]

    if (search.trim()) {
      list = fuse.search(search.trim()).map((r) => r.item)
    } else {
      list = companies.filter((c) => c.salary_median_k !== null)
    }

    if (industry === '百大（市值）') {
      list = list
        .filter((c) => c.market_cap != null && c.market_cap > 0)
        .sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0))
        .slice(0, 100)
    } else if (industry !== '全部') {
      list = list.filter((c) => c.industry === industry)
    }

    if (!search.trim() && industry !== '百大（市值）') {
      list.sort((a, b) => {
        if (sortBy === 'salary')
          return (b.salary_median_k ?? 0) - (a.salary_median_k ?? 0)
        if (sortBy === 'eps') return (b.eps ?? 0) - (a.eps ?? 0)
        if (sortBy === 'marketCap')
          return (b.market_cap ?? 0) - (a.market_cap ?? 0)
        return a.short_name.localeCompare(b.short_name, 'zh-TW')
      })
    }

    return list
  }, [companies, search, industry, sortBy, fuse])

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <section className="mb-8 text-center">
        <h1 className="mb-2 font-display text-3xl font-extrabold tracking-tight text-[var(--text-heading)] sm:text-4xl">
          看得到公司全貌的職缺平台
        </h1>
        <p className="mx-auto max-w-lg text-sm text-[var(--text-muted)]">
          薪資中位數、營收成長、EPS — 台灣 {totalCompanies.toLocaleString()}{' '}
          家上市櫃公司的真實面貌，一眼看懂。
        </p>
        <div className="mx-auto mt-5 flex max-w-md justify-center gap-8">
          <Stat value={totalCompanies.toLocaleString()} label="上市櫃公司" />
          <Stat value={totalWithSalary.toLocaleString()} label="有薪資資料" />
          <Stat value="114" label="年度資料" />
        </div>
      </section>

      {trends.length > 0 && <IndustryTrendsBar trends={trends} />}

      <div className="mx-auto mb-4 max-w-xl">
        <div className="flex overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
          <input
            type="text"
            placeholder="搜尋公司名稱、股票代號、產業..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 border-none bg-transparent px-4 py-3 text-sm text-[var(--text-heading)] outline-none placeholder:text-[var(--text-muted)]"
          />
          <div className="flex items-center gap-2 pr-3">
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(
                  e.target.value as 'salary' | 'name' | 'eps' | 'marketCap',
                )
              }
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-2 py-1 text-xs text-[var(--text-body)]"
            >
              <option value="salary">薪資排序</option>
              <option value="eps">EPS 排序</option>
              <option value="marketCap">市值排序</option>
              <option value="name">名稱排序</option>
            </select>
          </div>
        </div>
      </div>

      <div className="mx-auto mb-6 flex max-w-3xl flex-wrap justify-center gap-2">
        {[...INDUSTRIES, '百大（市值）'].map((ind) => (
          <button
            type="button"
            key={ind}
            onClick={() => {
              setIndustry(ind)
              setShowCount(60)
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              industry === ind
                ? 'border border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--text-heading)]'
                : 'border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--text-body)]'
            }`}
          >
            {ind}
          </button>
        ))}
      </div>

      <p className="mb-4 text-center text-xs text-[var(--text-muted)]">
        {filtered.length} 家公司
        {industry !== '全部' ? ` · ${industry}` : ''}
        {search.trim() ? ` · 搜尋「${search.trim()}」` : ''}
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.slice(0, showCount).map((c) => (
          <CompanyCard key={c.stock_id} company={c} />
        ))}
      </div>

      {filtered.length > showCount && (
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => setShowCount((n) => n + 60)}
            className="rounded-xl border border-[var(--accent)] bg-[var(--accent-soft)] px-6 py-2.5 text-sm font-semibold text-[var(--text-heading)] transition hover:bg-[var(--accent)] hover:text-[#00473e]"
          >
            載入更多（還有 {filtered.length - showCount} 家）
          </button>
        </div>
      )}

      {filtered.length === 0 && (
        <p className="mt-12 text-center text-sm text-[var(--text-muted)]">
          找不到符合條件的公司。試試其他關鍵字？
        </p>
      )}
    </main>
  )
}

function IndustryTrendsBar({ trends }: { trends: IndustryTrend[] }) {
  const meaningful = trends.filter((t) => t.total_jobs > 0)
  if (meaningful.length === 0) return null

  return (
    <section className="mx-auto mb-6 max-w-4xl">
      <h2 className="mb-3 text-center font-display text-sm font-bold tracking-wide text-[var(--text-heading)]">
        產業職缺動態
      </h2>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {meaningful.map((t) => (
          <div
            key={t.industry}
            className="flex min-w-[160px] shrink-0 flex-col rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-3 shadow-[var(--shadow)]"
          >
            <span className="mb-1 text-xs font-semibold text-[var(--text-heading)] truncate">
              {t.industry}
            </span>
            <span className="font-display text-lg font-bold tabular-nums text-[var(--text-heading)]">
              {t.total_jobs.toLocaleString()}
              <span className="ml-1 text-xs font-normal text-[var(--text-muted)]">
                缺
              </span>
            </span>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-muted)]">
                {t.company_count} 家公司
              </span>
              {t.delta !== 0 && (
                <span
                  className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                    t.delta > 0
                      ? 'bg-[var(--green-soft)] text-[var(--green-positive)]'
                      : 'bg-[var(--red-soft)] text-[var(--red-negative)]'
                  }`}
                >
                  {t.delta > 0 ? '▲' : '▼'} {Math.abs(t.delta).toLocaleString()}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
