import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { getCompanies, INDUSTRIES } from '#/utils/companies.functions'
import { Badge } from '#/components/Badge'
import type { Company } from '#/utils/types'

export const Route = createFileRoute('/salary')({
  loader: () => getCompanies(),
  component: SalaryRankingPage,
})

function formatMarketCap(cap: number | null): string {
  if (!cap) return '—'
  if (cap >= 10000) return `${(cap / 10000).toFixed(1)}兆`
  if (cap >= 1000) return `${(cap / 1000).toFixed(1)}K億`
  return `${cap.toFixed(0)}億`
}

function SalaryRankingPage() {
  const companies = Route.useLoaderData()
  const [industry, setIndustry] = useState('全部')
  const [sortCol, setSortCol] = useState<'median' | 'mean' | 'eps' | 'employees' | 'marketCap' | 'vsIndustry' | 'revenueYoY' | 'jobs'>('median')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [hiringOnly, setHiringOnly] = useState(false)

  const ranked = useMemo(() => {
    let list = companies.filter((c) => c.salary_median_k !== null)

    if (industry !== '全部') {
      list = list.filter((c) => c.industry === industry)
    }

    if (hiringOnly) {
      list = list.filter((c) => (c.job_count_104 ?? 0) + (c.job_count_linkedin ?? 0) > 0)
    }

    list.sort((a, b) => {
      let av: number, bv: number
      switch (sortCol) {
        case 'median': av = a.salary_median_k ?? 0; bv = b.salary_median_k ?? 0; break
        case 'mean': av = a.salary_mean_k ?? 0; bv = b.salary_mean_k ?? 0; break
        case 'eps': av = a.eps ?? 0; bv = b.eps ?? 0; break
        case 'employees': av = a.employee_count ?? 0; bv = b.employee_count ?? 0; break
        case 'marketCap': av = a.market_cap ?? 0; bv = b.market_cap ?? 0; break
        case 'vsIndustry': av = a.salary_vs_industry_pct ?? 0; bv = b.salary_vs_industry_pct ?? 0; break
        case 'revenueYoY': av = a.revenue_yoy_pct ?? -9999; bv = b.revenue_yoy_pct ?? -9999; break
        case 'jobs': av = (a.job_count_104 ?? 0) + (a.job_count_linkedin ?? 0); bv = (b.job_count_104 ?? 0) + (b.job_count_linkedin ?? 0); break
      }
      return sortDir === 'desc' ? bv - av : av - bv
    })

    return list.slice(0, 100)
  }, [companies, industry, sortCol, sortDir, hiringOnly])

  const toggleSort = (col: typeof sortCol) => {
    if (sortCol === col) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortCol(col)
      setSortDir('desc')
    }
  }

  const sortIndicator = (col: typeof sortCol) => {
    if (sortCol !== col) return ''
    return sortDir === 'desc' ? ' ↓' : ' ↑'
  }

  return (
    <main className="page-wrap px-4 pb-12 pt-8">
      <section className="mb-8">
        <h1 className="mb-2 font-display text-2xl font-extrabold text-[var(--text-heading)] sm:text-3xl">
          薪資排行
        </h1>
        <p className="text-sm text-[var(--text-muted)]">
          台灣上市櫃公司非主管全時員工薪資中位數排行（114 年度，資料來源：MOPS）
        </p>
      </section>

      <div className="mb-6 flex flex-wrap gap-2">
        {INDUSTRIES.map((ind) => (
          <button
            key={ind}
            onClick={() => setIndustry(ind)}
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

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <button
          onClick={() => setHiringOnly((v) => !v)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition ${
            hiringOnly
              ? 'border border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--text-heading)]'
              : 'border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--text-body)]'
          }`}
        >
          只看招募中
        </button>
        <span className="text-xs text-[var(--text-muted)]">
          顯示前 100 名{industry !== '全部' ? ` · ${industry}` : ''}{hiringOnly ? ' · 招募中' : ''} · 共 {ranked.length} 家公司
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-[var(--shadow)]">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <Th>#</Th>
              <Th>公司</Th>
              <ThSort active={sortCol === 'median'} onClick={() => toggleSort('median')}>
                薪資中位數{sortIndicator('median')}
              </ThSort>
              <Th>年增</Th>
              <ThSort active={sortCol === 'vsIndustry'} onClick={() => toggleSort('vsIndustry')}>
                同業比較{sortIndicator('vsIndustry')}
              </ThSort>
              <ThSort active={sortCol === 'eps'} onClick={() => toggleSort('eps')}>
                EPS{sortIndicator('eps')}
              </ThSort>
              <ThSort active={sortCol === 'marketCap'} onClick={() => toggleSort('marketCap')}>
                市值{sortIndicator('marketCap')}
              </ThSort>
              <ThSort active={sortCol === 'revenueYoY'} onClick={() => toggleSort('revenueYoY')}>
                營收年增{sortIndicator('revenueYoY')}
              </ThSort>
              <ThSort active={sortCol === 'jobs'} onClick={() => toggleSort('jobs')}>
                職缺{sortIndicator('jobs')}
              </ThSort>
              <ThSort active={sortCol === 'employees'} onClick={() => toggleSort('employees')}>
                員工數{sortIndicator('employees')}
              </ThSort>
            </tr>
          </thead>
          <tbody>
            {ranked.map((c, i) => (
              <RankRow key={c.stock_id} company={c} rank={i + 1} />
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="border-b border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
      {children}
    </th>
  )
}

function ThSort({ children, active, onClick }: { children: React.ReactNode; active: boolean; onClick: () => void }) {
  return (
    <th
      className={`cursor-pointer select-none border-b border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider transition hover:text-[var(--text-heading)] ${active ? 'text-[var(--text-heading)]' : 'text-[var(--text-muted)]'}`}
      onClick={onClick}
    >
      {children}
    </th>
  )
}

function RankRow({ company: c, rank }: { company: Company; rank: number }) {
  const initial = (c.short_name || c.name).charAt(0)
  const vsInd = c.salary_vs_industry_pct
  const jobTotal = (c.job_count_104 ?? 0) + (c.job_count_linkedin ?? 0)
  const revenueYoY = c.revenue_yoy_pct
  const isGrowingAndHiring = jobTotal > 0 && revenueYoY !== null && revenueYoY !== undefined && revenueYoY > 0
  return (
    <tr className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-elevated)]">
      <td className="px-3 py-3">
        <span className={`font-display font-bold tabular-nums ${rank <= 3 ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'}`}>
          {rank}
        </span>
      </td>
      <td className="px-3 py-3">
        <Link to="/company/$stockId" params={{ stockId: c.stock_id }} className="flex items-center gap-2 no-underline">
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md bg-[var(--bg-elevated)] font-display text-[10px] font-bold text-[var(--text-heading)]">
            {initial}
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-sm font-semibold text-[var(--text-heading)]">
              {c.short_name || c.name}
              {isGrowingAndHiring && (
                <span className="rounded bg-[var(--accent-soft)] px-1 py-px text-[9px] font-bold text-[var(--accent)]" title="營收成長且正在招募">成長招募中</span>
              )}
            </div>
            <div className="text-[10px] text-[var(--text-muted)]">{c.industry} · {c.stock_id}</div>
          </div>
        </Link>
      </td>
      <td className="px-3 py-3">
        <span className="font-display font-bold tabular-nums text-[var(--text-heading)]">
          {c.salary_median_k ? `${(c.salary_median_k / 10).toFixed(1)} 萬` : '—'}
        </span>
      </td>
      <td className="px-3 py-3">
        {c.salary_median_change_pct !== null ? (
          <Badge value={c.salary_median_change_pct} suffix="%" />
        ) : (
          <span className="text-[var(--text-muted)]">—</span>
        )}
      </td>
      <td className="px-3 py-3 text-xs tabular-nums">
        {vsInd !== null && vsInd !== undefined ? (
          <span className={vsInd > 0 ? 'text-[var(--green-positive)]' : vsInd < 0 ? 'text-[var(--red-negative)]' : 'text-[var(--text-muted)]'}>
            {vsInd > 0 ? '+' : ''}{vsInd.toFixed(0)}%
          </span>
        ) : '—'}
      </td>
      <td className="px-3 py-3 tabular-nums text-sm text-[var(--text-body)]">
        {c.eps !== null ? c.eps : '—'}
      </td>
      <td className="px-3 py-3 tabular-nums text-sm text-[var(--text-body)]">
        {formatMarketCap(c.market_cap)}
      </td>
      <td className="px-3 py-3">
        {revenueYoY !== null && revenueYoY !== undefined ? (
          <Badge value={revenueYoY > 999 ? 999 : revenueYoY < -999 ? -999 : revenueYoY} suffix="%" />
        ) : (
          <span className="text-xs text-[var(--text-muted)]">—</span>
        )}
      </td>
      <td className="px-3 py-3 text-sm">
        {jobTotal > 0 ? (
          <span className="font-semibold tabular-nums text-[var(--accent)]">{jobTotal.toLocaleString()}</span>
        ) : (
          <span className="text-xs text-[var(--text-muted)]">—</span>
        )}
      </td>
      <td className="px-3 py-3 tabular-nums text-sm text-[var(--text-body)]">
        {c.employee_count ? c.employee_count.toLocaleString() : '—'}
      </td>
    </tr>
  )
}
