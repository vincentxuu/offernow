export function MetricBox({
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
      <div className="font-display text-base font-bold tabular-nums text-[var(--text-heading)]">
        {value}
      </div>
      {sub && <div className="text-[10px] text-[var(--text-muted)]">{sub}</div>}
    </div>
  )
}
