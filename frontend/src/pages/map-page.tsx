import { useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import Plot from 'react-plotly.js'
import { useSearchParams } from 'react-router-dom'

import { api, type MapRow } from '../lib/api'
import { fmtPct, fmtUsd } from '../lib/format'
import { ErrorState, LoadingState } from '../components/loading-state'
import { Card, Eyebrow, SectionCopy, SectionTitle } from '../components/ui'

const layerOptions = [
  { value: 'tb', label: 'TB burden' },
  { value: 'bcg', label: 'BCG coverage' },
  { value: 'gdp', label: 'GDP per capita' },
  { value: 'detection', label: 'Detection capacity' },
  { value: 'whatif', label: '90%-BCG what-if' },
] as const

function buildLayer(rows: MapRow[], layer: string, bcgTarget: number) {
  const base = {
    locations: rows.map((row) => row.iso3),
    hovertemplate: '%{text}<extra></extra>',
    marker: { line: { color: '#fffaf5', width: 0.5 } },
  }

  if (layer === 'bcg') {
    return {
      ...base,
      z: rows.map((row) => row.bcg_coverage ?? 0),
      colorscale: [
        [0, '#fff8f2'],
        [1, '#f26b3a'],
      ],
      colorbar: { title: 'BCG %' },
      text: rows.map((row) => `${row.country}<br>BCG: ${fmtPct(row.bcg_coverage, 0)}<br>TB: ${row.tb_incidence?.toFixed(0)} / 100k`),
      title: 'BCG coverage',
    }
  }
  if (layer === 'gdp') {
    return {
      ...base,
      z: rows.map((row) => row.gdp_per_capita ?? 0),
      colorscale: [
        [0, '#fff8f2'],
        [1, '#776d66'],
      ],
      colorbar: { title: 'USD' },
      text: rows.map((row) => `${row.country}<br>GDP: ${fmtUsd(row.gdp_per_capita)}<br>TB: ${row.tb_incidence?.toFixed(0)} / 100k`),
      title: 'GDP per capita',
    }
  }
  if (layer === 'detection') {
    return {
      ...base,
      z: rows.map((row) => row.rapid_dx_sites ?? 0),
      colorscale: [
        [0, '#fff8f2'],
        [1, '#4f7e8d'],
      ],
      colorbar: { title: 'Sites / million' },
      text: rows.map((row) => `${row.country}<br>Rapid Dx: ${(row.rapid_dx_sites ?? 0).toFixed(2)} / million`),
      title: 'Detection capacity',
    }
  }
  if (layer === 'whatif') {
    return {
      ...base,
      z: rows.map((row) => row.predicted_tb_incidence ?? 0),
      colorscale: [
        [0, '#fff8f2'],
        [1, '#f26b3a'],
      ],
      colorbar: { title: 'TB / 100k' },
      text: rows.map(
        (row) =>
          `${row.country}<br>Predicted TB: ${row.predicted_tb_incidence?.toFixed(0)} / 100k<br>Target BCG: ${bcgTarget}%`,
      ),
      title: `Predicted TB burden at ${bcgTarget}% BCG`,
    }
  }

  return {
    ...base,
    z: rows.map((row) => row.tb_incidence ?? 0),
    colorscale: [
      [0, '#fff8f2'],
      [1, '#f26b3a'],
    ],
    colorbar: { title: 'TB / 100k' },
    text: rows.map((row) => `${row.country}<br>TB: ${row.tb_incidence?.toFixed(0)} / 100k`),
    title: 'TB burden',
  }
}

export function MapPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const layer = searchParams.get('layer') ?? 'tb'
  const bcgTarget = Number(searchParams.get('bcg_target') ?? '90')

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    let changed = false
    if (!searchParams.get('layer')) {
      next.set('layer', 'tb')
      changed = true
    }
    if (!searchParams.get('bcg_target')) {
      next.set('bcg_target', '90')
      changed = true
    }
    if (changed) setSearchParams(next, { replace: true })
  }, [searchParams, setSearchParams])

  const mapDataQuery = useQuery({ queryKey: ['map-data'], queryFn: api.fetchMapData })
  const whatIfQuery = useQuery({
    queryKey: ['whatif-map', bcgTarget],
    queryFn: () => api.fetchWhatIfMap(bcgTarget),
    enabled: layer === 'whatif',
  })

  const rows = layer === 'whatif' ? whatIfQuery.data : mapDataQuery.data
  const loading = mapDataQuery.isLoading || whatIfQuery.isLoading
  const error = mapDataQuery.error || whatIfQuery.error

  const figure = useMemo(() => {
    if (!rows?.length) return null
    const layerConfig = buildLayer(rows, layer, bcgTarget)
    return {
      data: [
        {
          type: 'choropleth',
          ...layerConfig,
        },
      ],
      layout: {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 0, r: 0, t: 40, b: 0 },
        geo: {
          projection: { type: 'natural earth' },
          showframe: false,
          showcoastlines: false,
          bgcolor: 'rgba(0,0,0,0)',
        },
        title: { text: layerConfig.title, x: 0.02, font: { family: 'Fraunces, serif', size: 24 } },
      },
    }
  }, [rows, layer, bcgTarget])

  if (loading) return <LoadingState label="Rendering the world context layers…" />
  if (error) return <ErrorState error={error as Error} />
  if (!figure) return null

  return (
    <div className="space-y-8">
      <div className="space-y-5">
        <Eyebrow>Global context layers</Eyebrow>
        <SectionTitle accent="with restraint.">Map burden, prevention, and system context</SectionTitle>
        <SectionCopy>
          Use the large-format world view to compare observed burden, BCG protection, economic context, detection
          capacity, and the 90%-BCG counterfactual.
        </SectionCopy>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap gap-3">
          {layerOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                const next = new URLSearchParams(searchParams)
                next.set('layer', option.value)
                setSearchParams(next, { replace: true })
              }}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                layer === option.value
                  ? 'bg-charcoal text-ivory shadow-soft'
                  : 'border border-border bg-surface text-charcoal/72 hover:bg-surface-2'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="mt-6 max-w-md">
          <label className="space-y-3">
            <span className="text-xs font-semibold uppercase tracking-[0.24em] text-charcoal/45">What-if BCG target</span>
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
          </label>
        </div>
      </Card>

      <Card className="overflow-hidden p-3">
        <div className="rounded-[1.5rem] bg-[#fbf7f3] p-4">
          <Plot
            data={figure.data as never}
            layout={figure.layout as never}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%', height: '48rem' }}
          />
        </div>
      </Card>
    </div>
  )
}
