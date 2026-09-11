import { Link } from '@tanstack/react-router'
import { Badge } from './Badge'
import { MetricBox } from './MetricBox'
import type { Company } from '#/utils/types'
import { calculateAttractivenessScore } from '#/utils/companies.functions'

const GRADE_COLORS: Record<string, { bg: string; text: string }> = {
  A: { bg: 'bg-[var(--green-soft)]', text: 'text-[var(--green-positive)]' },
  B: { bg: 'bg-[var(--accent-soft)]', text: 'text-[var(--accent)]' },
  C: { bg: 'bg-[var(--bg-elevated)]', text: 'text-[var(--text-muted)]' },
  D: { bg: 'bg-[var(--red-soft)]', text: 'text-[var(--red-negative)]' },
  F: { bg: 'bg-[var(--red-soft)]', text: 'text-[var(--red-negative)]' },
}

function formatMarketCap(cap: number | null): string {
  if (!cap) return '—'
  if (cap >= 10000) return `${(cap / 10000).toFixed(1)} 兆`
  if (cap >= 1000) return `${cap.toLocaleString(undefined, { maximumFractionDigits: 0 })} 億`
  return `${cap.toFixed(0)} 億`
}

function formatRevenueYoY(pct: number | null): string {
  if (pct === null || pct === undefined) return '—'
  if (pct > 999) return '>999%'
  if (pct < -999) return '<-999%'
  return `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
}

export function CompanyCard({ company: c }: { company: Company }) {
  const salaryWan = c.salary_median_k ? (c.salary_median_k / 10).toFixed(1) : null
  const changePct = c.salary_median_change_pct
  const initial = (c.short_name || c.name).charAt(0)
  const marketLabel = c.market === 'listed' ? '上市' : '上櫃'
  const vsIndustry = c.salary_vs_industry_pct
  const score = calculateAttractivenessScore(c)
  const gradeColor = GRADE_COLORS[score.grade] ?? GRADE_COLORS.C

  return (
    <Link
      to="/company/$stockId"
      params={{ stockId: c.stock_id }}
      className="block rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-4 shadow-[var(--shadow)] transition no-underline hover:border-[var(--accent)] hover:shadow-[var(--shadow-lg)]"
    >
      <div className="mb-3 flex items-center gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--bg-elevated)] font-display text-sm font-bold text-[var(--text-heading)]">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate font-display text-sm font-bold text-[var(--text-heading)]">
              {c.short_name || c.name}
            </span>
            <span className={`flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold ${gradeColor.bg} ${gradeColor.text}`}>
              {score.grade}
            </span>
          </div>
          <div className="text-xs text-[var(--text-muted)]">
            {c.industry} · {marketLabel} · {c.stock_id}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <MetricBox
          label="薪資中位數"
          value={salaryWan ? `${salaryWan} 萬` : '—'}
          sub={
            <div className="flex flex-wrap items-center gap-1">
              {changePct !== null && <Badge value={changePct} suffix="%" />}
              {vsIndustry !== null && vsIndustry !== undefined && Math.abs(vsIndustry) > 5 && (
                <span className={`text-[10px] font-medium ${vsIndustry > 0 ? 'text-[var(--green-positive)]' : 'text-[var(--red-negative)]'}`}>
                  同業{vsIndustry > 0 ? '+' : ''}{vsIndustry.toFixed(0)}%
                </span>
              )}
            </div>
          }
        />
        <MetricBox
          label="營收年增"
          value={formatRevenueYoY(c.revenue_yoy_pct)}
          sub={c.revenue_yoy_pct !== null && c.revenue_yoy_pct !== undefined ? (
            <Badge value={c.revenue_yoy_pct > 999 ? 999 : c.revenue_yoy_pct} suffix="" />
          ) : undefined}
        />
        <MetricBox label="EPS" value={c.eps !== null ? `${c.eps}` : '—'} sub="元/股" />
        <MetricBox
          label="市值"
          value={formatMarketCap(c.market_cap)}
        />
      </div>

      {c.ai_insight && (
        <div className="mt-2 rounded-lg bg-[var(--accent-soft)] px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--accent)]">AI 洞察</div>
          <div className="text-xs text-[var(--text-heading)]">{c.ai_insight}</div>
        </div>
      )}

      {((c.job_count_104 ?? 0) > 0 || (c.job_count_linkedin ?? 0) > 0) && (
        <div className="mt-2 flex flex-wrap items-center gap-x-3 text-xs font-medium text-[var(--accent)]">
          {(c.job_count_104 ?? 0) > 0 && <span>104: {c.job_count_104!.toLocaleString()} 缺</span>}
          {(c.job_count_linkedin ?? 0) > 0 && <span>LinkedIn: {c.job_count_linkedin!.toLocaleString()}+ 缺</span>}
          {c.job_count_trend === 'expanding' && (
            <span className="rounded bg-[var(--green-soft)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--green-positive)]">擴編中</span>
          )}
          {c.job_count_trend === 'shrinking' && (
            <span className="rounded bg-[var(--red-soft)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--red-negative)]">縮編中</span>
          )}
        </div>
      )}

      {/* Salary flags */}
      {(c.flag_low_salary === 1 || c.flag_eps_high_salary_low === 1 || c.flag_eps_up_salary_down === 1) && (
        <div className="mt-2 flex flex-wrap gap-1">
          {c.flag_low_salary === 1 && (
            <span className="rounded bg-[var(--red-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--red-negative)]">平均未達50萬</span>
          )}
          {c.flag_eps_high_salary_low === 1 && (
            <span className="rounded bg-[var(--red-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--red-negative)]">EPS高但薪低</span>
          )}
          {c.flag_eps_up_salary_down === 1 && (
            <span className="rounded bg-[var(--red-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--red-negative)]">EPS漲薪減</span>
          )}
        </div>
      )}
    </Link>
  )
}
