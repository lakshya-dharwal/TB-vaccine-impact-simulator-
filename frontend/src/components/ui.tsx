import type { ReactNode } from 'react'

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="text-xs font-semibold uppercase tracking-[0.26em] text-charcoal/45">{children}</div>
}

export function SectionTitle({ children, accent }: { children: ReactNode; accent?: ReactNode }) {
  return (
    <h2 className="max-w-3xl font-display text-4xl leading-[0.98] text-charcoal sm:text-5xl lg:text-6xl">
      {children}
      {accent ? <span className="ml-2 text-accent italic">{accent}</span> : null}
    </h2>
  )
}

export function SectionCopy({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <p className={`max-w-2xl text-base leading-7 text-charcoal/70 sm:text-lg ${className}`}>{children}</p>
}

export function Card({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return <div className={`rounded-[2rem] border border-border bg-surface shadow-soft ${className}`}>{children}</div>
}

export function MetricCard({
  label,
  value,
  supporting,
}: {
  label: string
  value: string
  supporting: string
}) {
  return (
    <Card className="p-6">
      <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-charcoal/40">{label}</div>
      <div className="mt-3 font-display text-4xl text-charcoal">{value}</div>
      <div className="mt-3 text-sm leading-6 text-charcoal/62">{supporting}</div>
    </Card>
  )
}

export function Pill({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-medium text-charcoal/70">
      {children}
    </span>
  )
}

export function Button({
  children,
  kind = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { kind?: 'primary' | 'ghost' }) {
  const classes =
    kind === 'primary'
      ? 'bg-charcoal text-ivory shadow-soft hover:-translate-y-0.5'
      : 'border border-border bg-surface text-charcoal hover:bg-surface-2'
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition ${classes} ${props.className ?? ''}`}
    >
      {children}
    </button>
  )
}

export function HeroMedia() {
  return (
    <Card className="relative overflow-hidden bg-[#ead6c8] p-6 sm:p-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.9),_transparent_40%),linear-gradient(135deg,rgba(255,255,255,0.68),rgba(236,181,138,0.42))]" />
      <div className="relative grid min-h-[28rem] place-items-center overflow-hidden rounded-[1.75rem] bg-[linear-gradient(180deg,#e9c7ae,#bb7e5d)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,220,190,0.75),_transparent_35%)]" />
        <div className="absolute left-6 top-6 rounded-full bg-surface/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-charcoal/55 shadow-soft">
          Editorial Portrait Slot
        </div>
        <div className="relative h-[24rem] w-[16rem] rounded-[8rem] bg-[linear-gradient(180deg,#f3d6c3,#e29c6c_42%,#8c4f35)] shadow-[0_40px_80px_rgba(76,34,16,0.28)]">
          <div className="absolute inset-x-4 top-10 h-28 rounded-full bg-[radial-gradient(circle,#ffd48d,_#ff9e4a_60%,transparent_68%)] opacity-80 blur-[2px]" />
          <div className="absolute inset-x-5 bottom-0 h-56 rounded-t-[7rem] bg-[linear-gradient(180deg,rgba(255,243,233,0.08),rgba(59,18,10,0.18))]" />
        </div>
        <div className="absolute bottom-6 left-6 flex flex-wrap gap-3">
          <Pill>WHO incidence target</Pill>
          <Pill>BCG + GDP narrative</Pill>
          <Pill>FastAPI-backed</Pill>
        </div>
      </div>
    </Card>
  )
}

export function RangeMeter({
  low,
  high,
  current,
}: {
  low: number
  high: number
  current: number
}) {
  const min = Math.min(low, current)
  const max = Math.max(high, current)
  const span = Math.max(max - min, 1)
  const marker = ((current - min) / span) * 100
  return (
    <div className="space-y-3">
      <div className="h-3 rounded-full bg-accent/10">
        <div className="relative h-3 rounded-full bg-[linear-gradient(90deg,rgba(242,107,58,0.16),rgba(242,107,58,0.42))]">
          <span
            className="absolute top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border-2 border-surface bg-charcoal shadow-soft"
            style={{ left: `calc(${marker}% - 0.625rem)` }}
          />
        </div>
      </div>
      <div className="flex items-center justify-between text-sm text-charcoal/60">
        <span>{low.toFixed(0)} / 100k</span>
        <span>{high.toFixed(0)} / 100k</span>
      </div>
    </div>
  )
}
