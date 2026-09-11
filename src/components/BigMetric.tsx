export function BigMetric({
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
        {note && (
          <span className="text-xs text-[var(--text-muted)]">{note}</span>
        )}
      </div>
    </div>
  )
}
