import { createFileRoute, Link } from '@tanstack/react-router'
import { getCompanyByStockId } from '#/lib/data'
import { Badge } from '#/components/Badge'

export const Route = createFileRoute('/company/$stockId')({
  loader: ({ params }) => getCompanyByStockId({ data: params.stockId }),
  component: CompanyDetailPage,
  head: ({ loaderData }) => {
    const c = loaderData
    if (!c) return { meta: [{ title: '找不到公司 | OfferNow' }] }
    const salaryStr = c.salary_median_k ? `薪資中位數 ${(c.salary_median_k / 10).toFixed(1)} 萬` : ''
    return {
      meta: [
        { title: `${c.short_name || c.name}（${c.stock_id}）${salaryStr ? ` · ${salaryStr}` : ''} | OfferNow` },
        { name: 'description', content: `${c.name}（${c.stock_id}）的薪資、EPS、員工數等公司全貌資訊。${salaryStr}。` },
      ],
    }
  },
})

function CompanyDetailPage() {
  const company = Route.useLoaderData()

  if (!company) {
    return (
      <main className="page-wrap px-4 py-16 text-center">
        <h1 className="mb-4 font-display text-2xl font-bold text-[var(--text-heading)]">找不到公司</h1>
        <p className="mb-6 text-[var(--text-muted)]">沒有找到此股票代號的公司資料。</p>
        <Link to="/" className="text-sm font-semibold text-[var(--accent)]">← 返回公司列表</Link>
      </main>
    )
  }

  const c = company
  const marketLabel = c.market === 'listed' ? '上市' : '上櫃'
  const salaryMedianWan = c.salary_median_k ? (c.salary_median_k / 10).toFixed(1) : null
  const salaryMeanWan = c.salary_mean_k ? (c.salary_mean_k / 10).toFixed(1) : null
  const initial = (c.short_name || c.name).charAt(0)

  const capitalFormatted = c.capital
    ? `${(Number(c.capital) / 100000000).toFixed(0)} 億`
    : '—'

  const formatDate = (d: string) => {
    if (!d || d.length < 8) return d || '—'
    return `${d.slice(0, 4)}/${d.slice(4, 6)}/${d.slice(6, 8)}`
  }

  return (
    <main className="page-wrap px-4 pb-12 pt-6">
      <div className="mb-6 flex items-center gap-4">
        <Link to="/" className="inline-flex items-center gap-1 text-sm font-medium text-[var(--accent)] no-underline hover:underline">
          ← 返回公司列表
        </Link>
        <Link to="/salary" className="inline-flex items-center gap-1 text-sm font-medium text-[var(--text-muted)] no-underline hover:text-[var(--accent)]">
          薪資排行 →
        </Link>
      </div>

      {/* Company Header */}
      <div className="mb-8 flex items-start gap-4">
        <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-[var(--bg-elevated)] font-display text-2xl font-bold text-[var(--text-heading)]">
          {initial}
        </div>
        <div>
          <h1 className="font-display text-2xl font-extrabold text-[var(--text-heading)] sm:text-3xl">
            {c.short_name || c.name}
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {c.name}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-0.5 text-xs font-semibold text-[var(--text-heading)]">
              {c.stock_id}
            </span>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">
              {c.industry || '未分類'}
            </span>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs text-[var(--text-muted)]">
              {marketLabel}
            </span>
          </div>
        </div>
      </div>

      {/* AI Insight */}
      {c.ai_insight && (
        <div className="mb-6 rounded-xl bg-[var(--accent-soft)] px-5 py-4">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-[var(--accent)]">AI 洞察</div>
          <div className="text-sm text-[var(--text-heading)]">{c.ai_insight}</div>
        </div>
      )}

      {/* 104 Link */}
      {c.job_count_104 != null && c.job_count_104 > 0 && (
        <div className="mb-6">
          <a
            href={c.encoded_cust_no_104 ? `https://www.104.com.tw/company/${c.encoded_cust_no_104}` : `https://www.104.com.tw/company/search?keyword=${encodeURIComponent(c.short_name || c.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold !text-[#1a2e1a] no-underline transition hover:bg-[var(--accent-hover)]"
          >
            在 104 上查看 {c.job_count_104.toLocaleString()} 個職缺 →
          </a>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Salary Section */}
        <div className="lg:col-span-2">
          <Section title="薪資資訊">
            <div className="grid gap-4 sm:grid-cols-2">
              <BigMetric
                label="非主管薪資中位數"
                value={salaryMedianWan ? `${salaryMedianWan} 萬` : '未揭露'}
                badge={c.salary_median_change_pct !== null ? <Badge value={c.salary_median_change_pct} suffix="%" /> : undefined}
                note={c.salary_year ? `${c.salary_year} 年度` : undefined}
              />
              <BigMetric
                label="非主管薪資平均數"
                value={salaryMeanWan ? `${salaryMeanWan} 萬` : '未揭露'}
              />
              <BigMetric
                label="EPS"
                value={c.eps !== null ? `${c.eps} 元/股` : '未揭露'}
              />
              <BigMetric
                label="員工人數"
                value={c.employee_count ? `${c.employee_count.toLocaleString()} 人` : '未揭露'}
              />
            </div>
          </Section>
        </div>

        {/* Company Info */}
        <div>
          <Section title="公司資訊">
            <div className="space-y-3">
              <InfoRow label="資本額" value={capitalFormatted} />
              <InfoRow label="董事長" value={c.chairman || '—'} />
              <InfoRow label="總經理" value={c.gm || '—'} />
              <InfoRow label="成立日期" value={formatDate(c.established)} />
              <InfoRow label={c.market === 'listed' ? '上市日期' : '上櫃日期'} value={formatDate(c.listed_date)} />
              <InfoRow label="地址" value={c.address || '—'} />
              {c.phone && <InfoRow label="電話" value={c.phone} />}
              {c.tax_id && <InfoRow label="統一編號" value={c.tax_id} />}
            </div>
          </Section>
        </div>
      </div>
    </main>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-5 shadow-[var(--shadow)]">
      <h2 className="mb-4 font-display text-lg font-bold text-[var(--text-heading)]">{title}</h2>
      {children}
    </section>
  )
}

function BigMetric({
  label,
  value,
  badge,
  note,
}: {
  label: string
  value: string
  badge?: React.ReactNode
  note?: string
}) {
  return (
    <div className="rounded-lg bg-[var(--bg-elevated)] p-4">
      <div className="mb-1 text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">
        {label}
      </div>
      <div className="font-display text-2xl font-bold tabular-nums text-[var(--text-heading)]">
        {value}
      </div>
      <div className="mt-1 flex items-center gap-2">
        {badge}
        {note && <span className="text-xs text-[var(--text-muted)]">{note}</span>}
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-[var(--border)] pb-2 last:border-0 last:pb-0">
      <span className="flex-shrink-0 text-xs text-[var(--text-muted)]">{label}</span>
      <span className="text-right text-xs font-medium text-[var(--text-heading)]">{value}</span>
    </div>
  )
}
