import { screen, waitFor } from '@testing-library/react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { HomePage } from './home-page'
import { PrioritizationPage } from './prioritization-page'
import { renderWithProviders } from '../test/test-utils'

function Probe() {
  const location = useLocation()
  return <div data-testid="probe">{location.search}</div>
}

describe('query parameter defaults', () => {
  it('hydrates country and scenario defaults on the home page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.endsWith('/config')) {
          return Promise.resolve(new Response(JSON.stringify({
            covariates: ['bcg_coverage', 'gdp_per_capita', 'income_level'],
            scenarios: ['baseline', 'combined'],
            income_levels: ['L', 'LM', 'UM', 'H'],
            regions: ['AFR'],
            use_income: true,
            target_source: 'owid',
            target_display: 'WHO',
            target_transform: 'log1p',
          })))
        }
        if (url.endsWith('/countries')) {
          return Promise.resolve(new Response(JSON.stringify(['India'])))
        }
        if (url.includes('/country/India')) {
          return Promise.resolve(new Response(JSON.stringify({
            country: 'India',
            year: 2023,
            tb_incidence: 100,
            tb_target_display: 'WHO',
            population: 100,
            income_level: 'LM',
            region: 'SEA',
            country_story: 'Story',
            rapid_dx_sites: null,
            bcg_coverage: 80,
            gdp_per_capita: 2000,
          })))
        }
        if (url.endsWith('/simulate')) {
          return Promise.resolve(new Response(JSON.stringify({
            country: 'India',
            scenario: 'combined',
            current_bcg_coverage: 80,
            simulated_bcg_coverage: 99,
            current_gdp_per_capita: 2000,
            simulated_gdp_per_capita: 2000,
            current_income_level: 'LM',
            simulated_income_level: 'UM',
            current_tb_incidence: 100,
            predicted_tb_incidence: 90,
            absolute_reduction: 10,
            relative_reduction_pct: 10,
            ci_lower: 85,
            ci_upper: 95,
            population: 100,
            cases_prevented_per_year: 10,
            country_story: 'Story',
            scenario_explanation: 'Summary',
            disclaimer: 'Disclaimer',
          })))
        }
        return Promise.reject(new Error(`Unhandled URL ${url}`))
      }),
    )

    renderWithProviders(
      <Routes>
        <Route path="/" element={<><HomePage /><Probe /></>} />
      </Routes>,
      '/',
    )

    await waitFor(() => expect(screen.getByTestId('probe')).toHaveTextContent('country=India'))
    expect(screen.getByTestId('probe')).toHaveTextContent('scenario=combined')
    vi.unstubAllGlobals()
  })

  it('hydrates prioritization defaults', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ bcg_target: 90, top: 20, target_display: 'WHO', rows: [] })),
        ),
      ),
    )

    renderWithProviders(
      <Routes>
        <Route path="/prioritization" element={<><PrioritizationPage /><Probe /></>} />
      </Routes>,
      '/prioritization',
    )

    await waitFor(() => expect(screen.getByTestId('probe')).toHaveTextContent('bcg_target=90'))
    expect(screen.getByTestId('probe')).toHaveTextContent('top=20')
    vi.unstubAllGlobals()
  })
})
