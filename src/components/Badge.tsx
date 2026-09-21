import { TrendingDown, TrendingUp } from '@sketchyicons/react'

export function Badge({
  value,
  suffix = '',
}: {
  value: number
  suffix?: string
}) {
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
      {isPositive ? (
        <TrendingUp size={10} />
      ) : isNegative ? (
        <TrendingDown size={10} />
      ) : null}{' '}
      {Math.abs(value).toFixed(1)}
      {suffix}
    </span>
  )
}
