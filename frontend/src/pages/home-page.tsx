import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import { useSearchParams } from 'react-router-dom'

import { api } from '../lib/api'
import { fmtCompact, fmtInt, fmtPct, fmtUsd, INCOME_LABELS, SCENARIO_LABELS } from '../lib/format'
import { ErrorState, LoadingState } from '../components/loading-state'
import { Button, Card, Eyebrow, HeroMedia, MetricCard, Pill, RangeMeter, SectionCopy, SectionTitle } from '../components/ui'

const scenarioDescriptions: Record<string, string> = {
  baseline: 'Hold the country profile constant and inspect the current model estimate.',
  vaccine_push: 'Lift BCG coverage and see how modeled incidence responds.',
  income_up: 'Move the income band up one step while preserving other context.',
  combined: 'Apply the prevention and structural uplift together.',
  custom: 'Tune the levers manually.',
}

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [useCustom, setUseCustom] = useState(false)
  const [overrides, setOverrides] = useState<{ bcg?: number; gdp?: number; income?: string }>({})
  const requestKeyRef = useRef<string>('')

  const configQuery = useQuery({ queryKey: ['config'], queryFn: api.fetchConfig })
  const countriesQuery = useQuery({ queryKey: ['countries'], queryFn: api.fetchCountries })
  const country = searchParams.get('country') ?? ''
  const scenario = searchParams.get('scenario') ?? ''

  const resolvedScenario = useMemo(() => {
    if (!configQuery.data) return ''
    if (scenario && configQuery.data.scenarios.includes(scenario)) return scenario
    return configQuery.data.scenarios.includes('combined')
      ? 'combined'
      : configQuery.data.scenarios[0]
  }, [configQuery.data, scenario])

  useEffect(() => {
    if (!countriesQuery.data?.length || !configQuery.data) return
    const next = new URLSearchParams(searchParams)
    let changed = false
    if (!country || !countriesQuery.data.includes(country)) {
      next.set('country', countriesQuery.data[0])
      changed = true
    }
    if (!scenario || !configQuery.data.scenarios.includes(scenario)) {
      next.set('scenario', resolvedScenario)
      changed = true
    }
    if (changed) setSearchParams(next, { replace: true })
  }, [countriesQuery.data, configQuery.data, country, scenario, searchParams, setSearchParams, resolvedScenario])

  const countryQuery = useQuery({
    queryKey: ['country', country],
    queryFn: () => api.fetchCountry(country),
    enabled: Boolean(country),
  })

  useEffect(() => {
    if (!countryQuery.data) return
    setOverrides({
      bcg: countryQuery.data.bcg_coverage ?? undefined,
      gdp: countryQuery.data.gdp_per_capita ?? undefined,
      income: countryQuery.data.income_level ?? undefined,
    })
  }, [countryQuery.data])

  const simulateMutation = useMutation({
    mutationFn: api.simulate,
  })

  useEffect(() => {
    if (!country || !resolvedScenario || useCustom) return
    const key = `${country}:${resolvedScenario}`
    if (requestKeyRef.current === key) return
    requestKeyRef.current = key
    simulateMutation.mutate({ country, scenario: resolvedScenario })
  }, [country, resolvedScenario, simulateMutation, useCustom])

  const loading = configQuery.isLoading || countriesQuery.isLoading || countryQuery.isLoading
  const error = configQuery.error || countriesQuery.error || countryQuery.error

  if (loading) return <LoadingState label="Preparing the scenario explorer…" />
  if (error) return <ErrorState error={error as Error} />
  if (!configQuery.data || !countryQuery.data) return null

  const currentCountry = countryQuery.data
  const result = simulateMutation.data

  const beforeAfterData = result
    ? [
        { name: 'Current', value: result.current_tb_incidence, fill: '#d3c2b4' },
        { name: 'Simulated', value: result.predicted_tb_incidence, fill: '#f26b3a' },
      ]
    : []

  function updateSearch(key: string, value: string) {
    const next = new URLSearchParams(searchParams)
    next.set(key, value)
    setSearchParams(next, { replace: true })
  }

  function runScenario() {
    requestKeyRef.current = ''
    simulateMutation.mutate({
      country,
      scenario: useCustom ? 'custom' : resolvedScenario,
      bcg_override: useCustom ? overrides.bcg : undefined,
      gdp_override: useCustom ? overrides.gdp : undefined,
      income_override: useCustom ? overrides.income : undefined,
    })
  }

  return (
    <div className="space-y-10">
      <section className="grid gap-8 lg:grid-cols-[1.04fr_0.96fr] lg:items-center">
        <div className="space-y-6">
          <Eyebrow>Dashboard-first health-tech interface</Eyebrow>
          <SectionTitle accent="with warmth.">Explore TB futures</SectionTitle>
          <SectionCopy>
            A premium prevention lab built on the live FastAPI model. Adjust vaccination coverage, GDP, and
            income context, then see how the country profile shifts through an editorial-quality analytical
            experience.
          </SectionCopy>
          <div className="flex flex-wrap gap-3">
            <Pill>{configQuery.data.target_display}</Pill>
            <Pill>{configQuery.data.target_transform ?? 'original target'}</Pill>
            <Pill>FastAPI + React</Pill>
          </div>
          <div className="flex flex-wrap gap-4">
            <Button onClick={runScenario}>
              Run Live Scenario
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button kind="ghost" onClick={() => setUseCustom((value) => !value)}>
              {useCustom ? 'Back to Preset Scenarios' : 'Open Custom Mix'}
            </Button>
          </div>
        </div>
        <HeroMedia />
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.86fr_1.14fr]">
        <Card className="p-6 lg:p-8">
          <div className="space-y-6">
            <div>
              <Eyebrow>Control panel</Eyebrow>
              <div className="mt-2 font-display text-3xl text-charcoal">Country and scenario</div>
              <SectionCopy className="mt-3 max-w-none">
                Choose the current country profile, then move through preset scenarios or a custom override mix.
              </SectionCopy>
            </div>

            <label className="block space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.24em] text-charcoal/45">Country</span>
              <select
                className="w-full rounded-[1.35rem] border border-border bg-surface px-4 py-3 text-sm text-charcoal outline-none transition focus:border-charcoal/25"
                value={country}
                onChange={(event) => updateSearch('country', event.target.value)}
              >
                {countriesQuery.data?.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </label>

            <div className="space-y-3">
              <span className="text-xs font-semibold uppercase tracking-[0.24em] text-charcoal/45">Scenario</span>
              <div className="flex flex-wrap gap-3">
                {configQuery.data.scenarios.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => updateSearch('scenario', option)}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                      resolvedScenario === option && !useCustom
                        ? 'border border-accent/25 bg-accent/12 text-accent shadow-soft'
                        : 'border border-border bg-surface text-charcoal/70 hover:bg-surface-2'
                    }`}
                  >
                    {SCENARIO_LABELS[option] ?? option}
                  </button>
                ))}
              </div>
              <div className="text-sm leading-6 text-charcoal/62">
                {scenarioDescriptions[resolvedScenario] ?? 'Explore a counterfactual scenario.'}
              </div>
            </div>

            <div className="rounded-[1.5rem] border border-border bg-surface-2 p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold text-charcoal">Custom override mix</div>
                  <div className="mt-1 text-sm text-charcoal/60">Swap preset moves for direct control.</div>
                </div>
                <button
                  type="button"
                  onClick={() => setUseCustom((value) => !value)}
                  className={`relative h-7 w-12 rounded-full transition ${useCustom ? 'bg-accent' : 'bg-border'}`}
                >
                  <span
                    className={`absolute top-1 h-5 w-5 rounded-full bg-surface transition ${useCustom ? 'left-6' : 'left-1'}`}
                  />
                </button>
              </div>
              <div className="mt-5 grid gap-4">
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-charcoal/45">BCG coverage</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={overrides.bcg ?? 0}
                    onChange={(event) =>
                      setOverrides((current) => ({ ...current, bcg: Number(event.target.value) }))
                    }
                    disabled={!useCustom}
                    className="w-full accent-accent disabled:opacity-40"
                  />
                  <div className="text-sm text-charcoal/60">{fmtPct(overrides.bcg ?? 0, 0)}</div>
                </label>
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-charcoal/45">GDP per capita</span>
                  <input
                    type="range"
                    min={500}
                    max={30000}
                    step={100}
                    value={overrides.gdp ?? 500}
                    onChange={(event) =>
                      setOverrides((current) => ({ ...current, gdp: Number(event.target.value) }))
                    }
                    disabled={!useCustom}
                    className="w-full accent-accent disabled:opacity-40"
                  />
                  <div className="text-sm text-charcoal/60">{fmtUsd(overrides.gdp ?? 0)}</div>
                </label>
                <label className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-charcoal/45">Income band</span>
                  <select
                    className="w-full rounded-[1.15rem] border border-border bg-surface px-4 py-3 text-sm disabled:opacity-40"
                    value={overrides.income ?? ''}
                    disabled={!useCustom}
                    onChange={(event) => setOverrides((current) => ({ ...current, income: event.target.value }))}
                  >
                    {configQuery.data.income_levels.map((income) => (
                      <option key={income} value={income}>
                        {INCOME_LABELS[income] ?? income}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <Card className="bg-[#fbf6f1] p-5">
              <div className="flex items-start gap-4">
                <div className="grid h-12 w-12 place-items-center rounded-2xl bg-accent/10 text-accent">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div className="space-y-2">
                  <div className="font-semibold text-charcoal">{currentCountry.country}</div>
                  <div className="text-sm leading-6 text-charcoal/65">{currentCountry.country_story}</div>
                  <div className="flex flex-wrap gap-2 pt-2">
                    <Pill>{currentCountry.region}</Pill>
                    <Pill>{currentCountry.year}</Pill>
                    <Pill>{INCOME_LABELS[currentCountry.income_level ?? ''] ?? currentCountry.income_level}</Pill>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </Card>

        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <MetricCard
              label="Current TB incidence"
              value={result ? fmtInt(result.current_tb_incidence) : fmtInt(currentCountry.tb_incidence)}
              supporting="Per 100,000 population"
            />
            <MetricCard
              label="Simulated incidence"
              value={result ? fmtInt(result.predicted_tb_incidence) : '—'}
              supporting="Counterfactual estimate"
            />
            <MetricCard
              label="Cases prevented / year"
              value={result ? fmtCompact(Math.max(result.cases_prevented_per_year, 0)) : '—'}
              supporting="Population-scaled directional estimate"
            />
            <MetricCard
              label="Relative reduction"
              value={result ? fmtPct(result.relative_reduction_pct) : '—'}
              supporting="Compared with the current incidence"
            />
          </div>

          <Card className="grid gap-6 p-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-4">
              <div>
                <Eyebrow>Current vs simulated</Eyebrow>
                <div className="mt-2 font-display text-3xl text-charcoal">Scenario output</div>
              </div>
              {result ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={beforeAfterData} barGap={18}>
                      <CartesianGrid vertical={false} stroke="#efe4dc" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} />
                      <YAxis axisLine={false} tickLine={false} />
                      <Bar dataKey="value" radius={[14, 14, 6, 6]}>
                        {beforeAfterData.map((entry) => (
                          <Cell key={entry.name} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <LoadingState label="Running the first scenario…" />
              )}
            </div>
            <div className="space-y-5">
              <div>
                <Eyebrow>Confidence interval</Eyebrow>
                <div className="mt-2 font-display text-3xl text-charcoal">Model uncertainty</div>
              </div>
              {result ? (
                <>
                  <RangeMeter low={result.ci_lower} high={result.ci_upper} current={result.predicted_tb_incidence} />
                  <div className="text-sm leading-7 text-charcoal/65">
                    The interval reflects model variance rather than epidemiological certainty. It is meant to
                    anchor interpretation, not imply causal precision.
                  </div>
                  <Card className="bg-[#fbf7f3] p-5">
                    <div className="text-sm font-semibold uppercase tracking-[0.18em] text-charcoal/45">Narrative readout</div>
                    <div className="mt-3 text-sm leading-7 text-charcoal/72">{result.scenario_explanation}</div>
                  </Card>
                </>
              ) : (
                <LoadingState label="Waiting for scenario results…" />
              )}
            </div>
          </Card>

          <Card className="p-6">
            <Eyebrow>Reality check</Eyebrow>
            <div className="mt-2 font-display text-3xl text-charcoal">Interpret this as directional screening.</div>
            <div className="mt-4 grid gap-4 text-sm leading-7 text-charcoal/68 lg:grid-cols-2">
              <p>
                The model changes selected levers while holding the rest of the observed country context fixed. It
                is useful for comparing patterns and opportunity shape, not for policy-grade forecasting.
              </p>
              <p>
                BCG coverage, GDP, and income act as proxies for broader prevention and structural conditions. The
                result should be read alongside regional context, current burden, and the model card.
              </p>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
