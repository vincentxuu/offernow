export function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-[var(--border)] pb-2 last:border-0 last:pb-0">
      <span className="flex-shrink-0 text-xs text-[var(--text-muted)]">{label}</span>
      <span className="text-right text-xs font-medium text-[var(--text-heading)]">{value}</span>
    </div>
  )
}
