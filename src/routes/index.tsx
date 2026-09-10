import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { getCompanies, INDUSTRIES } from '#/lib/data'
import { CompanyCard } from '#/components/CompanyCard'
import { Stat } from '#/components/Stat'

export const Route = createFileRoute('/')({
  loader: () => getCompanies(),
  component: HomePage,
})

function HomePage() {
  const companies = Route.useLoaderData()
  const [search, setSearch] = useState('')
  const [industry, setIndustry] = useState('全部')
  const [sortBy, setSortBy] = useState<'salary' | 'name' | 'eps'>('salary')
  const [showCount, setShowCount] = useState(60)

  const totalCompanies = companies.length
  const totalWithSalary = companies.filter((c) => c.salary_median_k !== null).length

  const filtered = useMemo(() => {
    let list = companies.filter((c) => c.salary_median_k !== null)

    if (industry !== '全部') {
      list = list.filter((c) => c.industry === industry)
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.short_name.toLowerCase().includes(q) ||
          c.stock_id.includes(q) ||
          c.industry.toLowerCase().includes(q),
      )
    }

    list.sort((a, b) => {
      if (sortBy === 'salary') return (b.salary_median_k ?? 0) - (a.salary_median_k ?? 0)
      if (sortBy === 'eps') return (b.eps ?? 0) - (a.eps ?? 0)
      return a.short_name.localeCompare(b.short_name, 'zh-TW')
    })

    return list
  }, [companies, search, industry, sortBy])

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <section className="mb-8 text-center">
        <h1 className="mb-2 font-display text-3xl font-extrabold tracking-tight text-[var(--text-heading)] sm:text-4xl">
          看得到公司全貌的職缺平台
        </h1>
        <p className="mx-auto max-w-lg text-sm text-[var(--text-muted)]">
          薪資中位數、營收成長、EPS — 台灣 {totalCompanies.toLocaleString()} 家上市櫃公司的真實面貌，一眼看懂。
        </p>
        <div className="mx-auto mt-5 flex max-w-md justify-center gap-8">
          <Stat value={totalCompanies.toLocaleString()} label="上市櫃公司" />
          <Stat value={totalWithSalary.toLocaleString()} label="有薪資資料" />
          <Stat value="114" label="年度資料" />
        </div>
      </section>

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
              onChange={(e) => setSortBy(e.target.value as 'salary' | 'name' | 'eps')}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-2 py-1 text-xs text-[var(--text-body)]"
            >
              <option value="salary">薪資排序</option>
              <option value="eps">EPS 排序</option>
              <option value="name">名稱排序</option>
            </select>
          </div>
        </div>
      </div>

      <div className="mx-auto mb-6 flex max-w-3xl flex-wrap justify-center gap-2">
        {INDUSTRIES.map((ind) => (
          <button
            key={ind}
            onClick={() => { setIndustry(ind); setShowCount(60) }}
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
