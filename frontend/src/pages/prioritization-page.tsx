import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent'
import { CartesianGrid, Cell, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis, BarChart, Bar } from 'recharts'
import { useSearchParams } from 'react-router-dom'

import { api } from '../lib/api'
import { fmtCompact, fmtInt, fmtPct, INCOME_LABELS, REGION_COLORS } from '../lib/format'
import { ErrorState, LoadingState } from '../components/loading-state'
import { Card, Eyebrow, MetricCard, SectionCopy, SectionTitle } from '../components/ui'

export function PrioritizationPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const bcgTarget = Number(searchParams.get('bcg_target') ?? '90')
  const top = Number(searchParams.get('top') ?? '20')

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    let changed = false
    if (!searchParams.get('bcg_target')) {
      next.set('bcg_target', '90')
      changed = true
    }
    if (!searchParams.get('top')) {
      next.set('top', '20')
      changed = true
    }
    if (changed) setSearchParams(next, { replace: true })
  }, [searchParams, setSearchParams])

  const priorityQuery = useQuery({
    queryKey: ['prioritize', bcgTarget, top],
    queryFn: () => api.fetchPrioritization(bcgTarget, top),
  })

  if (priorityQuery.isLoading) return <LoadingState label="Ranking country opportunity…" />
  if (priorityQuery.error) return <ErrorState error={priorityQuery.error as Error} />
  if (!priorityQuery.data) return null

  const rows = priorityQuery.data.rows
  const totalPrevented = rows.reduce((sum, row) => sum + row.cases_prevented_per_year, 0)
  const barData = rows.slice(0, 10).map((row) => ({
    country: row.country,
    value: row.cases_prevented_per_year,
    current_bcg_coverage: row.current_bcg_coverage,
  }))

  return (
    <div className="space-y-8">
      <div className="space-y-5">
        <Eyebrow>Vaccine prioritization</Eyebrow>
        <SectionTitle accent="for action.">Find where BCG scale-up matters most</SectionTitle>
        <SectionCopy>
          This page ranks countries by modeled cases prevented per year if BCG coverage reached a chosen target.
          It is an opportunity lens for strategic discussion, not a deployment prescription.
        </SectionCopy>
      </div>

      <Card className="p-6">
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <label className="space-y-3">
            <span className="text-xs font-semibold uppercase tracking-[0.24em] text-charcoal/45">BCG target</span>
            <input
              type="range"
              min={70}
              max={99}
              value={bcgTarget}
              onChange={(event) => {
                const next = new URLSearchParams(searchParams)
                next.set('bcg_target', event.target.value)
                setSearchParams(next, { replace: true })
              }}
              className="w-full accent-accent"
            />
            <div className="text-sm text-charcoal/62">{bcgTarget}% target coverage</div>
          </label>
          <label className="space-y-3">
            <span className="text-xs font-semibold uppercase tracking-[0.24em] text-charcoal/45">Top countries</span>
            <input
              type="range"
              min={10}
              max={40}
              step={5}
              value={top}
              onChange={(event) => {
                const next = new URLSearchParams(searchParams)
                next.set('top', event.target.value)
                setSearchParams(next, { replace: true })
              }}
              className="w-full accent-accent"
            />
            <div className="text-sm text-charcoal/62">{top} rows returned</div>
          </label>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Target coverage" value={`${bcgTarget}%`} supporting="Applied as a counterfactual cap." />
        <MetricCard label="Countries returned" value={fmtInt(rows.length)} supporting="Highest modeled impact rows." />
        <MetricCard
          label="Cases prevented / year"
          value={fmtCompact(totalPrevented)}
          supporting="Aggregate of the displayed ranking."
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="p-6">
          <Eyebrow>Ranking bars</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Estimated annual impact</div>
          <div className="mt-5 h-[28rem]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ left: 20, right: 12 }}>
                <CartesianGrid horizontal stroke="#efe4dc" />
                <XAxis type="number" axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="country" axisLine={false} tickLine={false} width={120} />
                <Tooltip formatter={(value: ValueType | undefined) => fmtInt(Number(value ?? 0))} />
                <Bar dataKey="value" radius={[0, 16, 16, 0]}>
                  {barData.map((entry) => (
                    <Cell
                      key={entry.country}
                      fill={`rgba(242,107,58,${Math.max(entry.current_bcg_coverage / 110, 0.22)})`}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <Eyebrow>Opportunity landscape</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Burden, coverage, and scale</div>
          <div className="mt-5 h-[28rem]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 12, right: 12, bottom: 24, left: 12 }}>
                <CartesianGrid stroke="#efe4dc" />
                <XAxis
                  dataKey="current_bcg_coverage"
                  type="number"
                  name="BCG coverage"
                  unit="%"
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  dataKey="current_tb_incidence"
                  type="number"
                  name="TB incidence"
                  unit="/100k"
                  axisLine={false}
                  tickLine={false}
                />
                <ZAxis dataKey="population" range={[80, 780]} />
                <Tooltip
                  formatter={(value: ValueType | undefined, key: NameType | undefined) => {
                    const safe = Number(value ?? 0)
                    if (key === 'population') return fmtCompact(safe)
                    if (key === 'current_bcg_coverage') return `${safe.toFixed(0)}%`
                    return `${safe.toFixed(0)} / 100k`
                  }}
                />
                <Scatter
                  data={rows}
                  shape={(props) => {
                    const { cx, cy, payload } = props
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={Math.max(7, Math.min(18, Math.sqrt(payload.population) / 65))}
                        fill={REGION_COLORS[payload.region] ?? '#f26b3a'}
                        fillOpacity={0.85}
                        stroke="#fffaf5"
                        strokeWidth={1.5}
                      />
                    )
                  }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="border-b border-border px-6 py-5">
          <Eyebrow>Refined ranking table</Eyebrow>
          <div className="mt-2 font-display text-3xl text-charcoal">Top modeled opportunities</div>
        </div>
        <div className="max-h-[34rem] overflow-auto">
          <table className="min-w-full table-fixed text-left text-sm">
            <thead className="sticky top-0 bg-surface/95 backdrop-blur">
              <tr className="text-charcoal/50">
                {['Country', 'Region', 'Income', 'BCG', 'TB / 100k', 'Prevented / year', 'Reduction'].map((heading) => (
                  <th key={heading} className="px-6 py-4 font-semibold">
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.iso3} className="border-t border-border/70">
                  <td className="px-6 py-4 font-medium text-charcoal">{row.country}</td>
                  <td className="px-6 py-4 text-charcoal/64">{row.region}</td>
                  <td className="px-6 py-4 text-charcoal/64">{INCOME_LABELS[row.income_level ?? ''] ?? '—'}</td>
                  <td className="px-6 py-4 text-charcoal/64">{fmtPct(row.current_bcg_coverage, 0)}</td>
                  <td className="px-6 py-4 text-charcoal/64">{fmtInt(row.current_tb_incidence)}</td>
                  <td className="px-6 py-4 text-charcoal/64">{fmtInt(row.cases_prevented_per_year)}</td>
                  <td className="px-6 py-4 text-charcoal/64">{fmtPct(row.relative_reduction_pct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
