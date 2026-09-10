import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import companiesData from '../../scripts/data/companies_with_salary.json'

type Company = {
  stock_id: string
  name: string
  short_name: string
  industry: string
  market: string
  salary_median_k: number | null
  salary_mean_k: number | null
  salary_median_change_pct: number | null
  employee_count: number | null
  eps: number | null
  capital: string
}

const companies = companiesData as Company[]

const INDUSTRIES = [
  '全部',
  '半導體業',
  '電子零組件業',
  '金融保險業',
  '光電業',
  '電腦及週邊設備業',
  '生技醫療業',
  '通信網路業',
  '資訊服務業',
]

const withSalary = companies.filter((c) => c.salary_median_k !== null)
const totalCompanies = companies.length
const totalWithSalary = withSalary.length

export const Route = createFileRoute('/')({ component: HomePage })

function HomePage() {
  const [search, setSearch] = useState('')
  const [industry, setIndustry] = useState('全部')
  const [sortBy, setSortBy] = useState<'salary' | 'name' | 'eps'>('salary')

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
  }, [search, industry, sortBy])

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      {/* Hero */}
      <section className="mb-8 text-center">
        <h1
          className="mb-2 text-3xl font-extrabold tracking-tight text-[var(--text-heading)] sm:text-4xl"
          style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}
        >
          看得到公司全貌的職缺平台
        </h1>
        <p className="mx-auto max-w-lg text-sm text-[var(--text-muted)]">
          薪資中位數、營收成長、EPS — 台灣 {totalCompanies.toLocaleString()} 家上市櫃公司的真實面貌，一眼看懂。
        </p>

        {/* Stats */}
        <div className="mx-auto mt-5 flex max-w-md justify-center gap-8">
          <Stat value={totalCompanies.toLocaleString()} label="上市櫃公司" />
          <Stat value={totalWithSalary.toLocaleString()} label="有薪資資料" />
          <Stat value="114" label="年度資料" />
        </div>
      </section>

      {/* Search */}
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

      {/* Industry chips */}
      <div className="mx-auto mb-6 flex max-w-3xl flex-wrap justify-center gap-2">
        {INDUSTRIES.map((ind) => (
          <button
            key={ind}
            onClick={() => setIndustry(ind)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              industry === ind
                ? 'bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--text-heading)]'
                : 'bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--text-body)]'
            }`}
          >
            {ind}
          </button>
        ))}
      </div>

      {/* Result count */}
      <p className="mb-4 text-center text-xs text-[var(--text-muted)]">
        {filtered.length} 家公司
        {industry !== '全部' ? ` · ${industry}` : ''}
        {search.trim() ? ` · 搜尋「${search.trim()}」` : ''}
      </p>

      {/* Company Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.slice(0, 60).map((c) => (
          <CompanyCard key={c.stock_id} company={c} />
        ))}
      </div>

      {filtered.length > 60 && (
        <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
          顯示前 60 筆，共 {filtered.length} 家公司。使用搜尋或篩選縮小範圍。
        </p>
      )}

      {filtered.length === 0 && (
        <p className="mt-12 text-center text-sm text-[var(--text-muted)]">
          找不到符合條件的公司。試試其他關鍵字？
        </p>
      )}
    </main>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div
        className="text-xl font-bold text-[var(--text-heading)]"
        style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontVariantNumeric: 'tabular-nums' }}
      >
        {value}
      </div>
      <div className="text-xs text-[var(--text-muted)]">{label}</div>
    </div>
  )
}

function CompanyCard({ company: c }: { company: Company }) {
  const salaryWan = c.salary_median_k ? (c.salary_median_k / 10).toFixed(1) : null
  const changePct = c.salary_median_change_pct
  const initial = (c.short_name || c.name).charAt(0)
  const marketLabel = c.market === 'listed' ? '上市' : '上櫃'

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-[var(--shadow)] transition hover:border-[var(--accent)] hover:shadow-[var(--shadow-lg)]">
      {/* Header */}
      <div className="mb-3 flex items-center gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--bg-elevated)] text-sm font-bold text-[var(--text-heading)]"
          style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}
        >
          {initial}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-[var(--text-heading)]" style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}>
            {c.short_name || c.name}
          </div>
          <div className="text-xs text-[var(--text-muted)]">
            {c.industry} · {marketLabel} · {c.stock_id}
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="mb-3 grid grid-cols-2 gap-2">
        <MetricBox
          label="薪資中位數"
          value={salaryWan ? `${salaryWan} 萬` : '—'}
          sub={changePct !== null ? (
            <Badge value={changePct} suffix="%" />
          ) : undefined}
        />
        <MetricBox
          label="EPS"
          value={c.eps !== null ? `${c.eps}` : '—'}
          sub="元/股"
        />
        <MetricBox
          label="員工數"
          value={c.employee_count ? c.employee_count.toLocaleString() : '—'}
          sub="人"
        />
        <MetricBox
          label="平均薪資"
          value={c.salary_mean_k ? `${(c.salary_mean_k / 10).toFixed(1)} 萬` : '—'}
        />
      </div>
    </div>
  )
}

function MetricBox({
  label,
  value,
  sub,
}: {
  label: string
  value: string
  sub?: React.ReactNode
}) {
  return (
    <div className="rounded-lg bg-[var(--bg-elevated)] px-3 py-2">
      <div className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
        {label}
      </div>
      <div
        className="text-base font-bold text-[var(--text-heading)]"
        style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontVariantNumeric: 'tabular-nums' }}
      >
        {value}
      </div>
      {sub && (
        <div className="text-[10px] text-[var(--text-muted)]">{sub}</div>
      )}
    </div>
  )
}

function Badge({ value, suffix = '' }: { value: number; suffix?: string }) {
  const isPositive = value > 0
  const isNegative = value < 0
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
        isPositive
          ? 'bg-[var(--green-soft)] text-[var(--green-positive)]'
          : isNegative
            ? 'bg-[var(--red-soft)] text-[var(--red-negative)]'
            : 'text-[var(--text-muted)]'
      }`}
    >
      {isPositive ? '▲' : isNegative ? '▼' : ''} {Math.abs(value).toFixed(1)}{suffix}
    </span>
  )
}
