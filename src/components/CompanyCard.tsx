import { Link } from '@tanstack/react-router'
import { Badge } from './Badge'
import { MetricBox } from './MetricBox'
import type { Company } from '#/lib/types'

export function CompanyCard({ company: c }: { company: Company }) {
  const salaryWan = c.salary_median_k ? (c.salary_median_k / 10).toFixed(1) : null
  const changePct = c.salary_median_change_pct
  const initial = (c.short_name || c.name).charAt(0)
  const marketLabel = c.market === 'listed' ? '上市' : '上櫃'

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
        <div className="min-w-0">
          <div className="truncate font-display text-sm font-bold text-[var(--text-heading)]">
            {c.short_name || c.name}
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
          sub={changePct !== null ? <Badge value={changePct} suffix="%" /> : undefined}
        />
        <MetricBox label="EPS" value={c.eps !== null ? `${c.eps}` : '—'} sub="元/股" />
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

      {c.ai_insight && (
        <div className="mt-2 rounded-lg bg-[var(--accent-soft)] px-3 py-2">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--accent)]">AI 洞察</div>
          <div className="text-xs text-[var(--text-heading)]">{c.ai_insight}</div>
        </div>
      )}

      {(c.job_count_104 ?? 0) > 0 && (
        <div className="mt-2 text-xs font-medium text-[var(--accent)]">
          104 上有 {c.job_count_104!.toLocaleString()} 個職缺 →
        </div>
      )}
    </Link>
  )
}
