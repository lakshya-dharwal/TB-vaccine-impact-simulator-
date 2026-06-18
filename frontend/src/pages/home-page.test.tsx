import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { HomePage } from './home-page'
import { renderWithProviders } from '../test/test-utils'

describe('HomePage', () => {
  it('renders live scenario output', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.endsWith('/config')) {
          return Promise.resolve(new Response(JSON.stringify({
            covariates: ['bcg_coverage', 'gdp_per_capita', 'income_level'],
            scenarios: ['baseline', 'vaccine_push', 'income_up', 'combined'],
            income_levels: ['L', 'LM', 'UM', 'H'],
            regions: ['AFR'],
            use_income: true,
            target_source: 'owid',
            target_display: 'WHO estimated TB incidence',
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
            tb_incidence: 180,
            tb_target_display: 'WHO estimated TB incidence',
            population: 1000000,
            income_level: 'LM',
            region: 'SEA',
            country_story: 'Context story',
            rapid_dx_sites: 2.5,
            bcg_coverage: 80,
            gdp_per_capita: 2500,
          })))
        }
        if (url.endsWith('/simulate')) {
          return Promise.resolve(new Response(JSON.stringify({
            country: 'India',
            scenario: 'combined',
            current_bcg_coverage: 80,
            simulated_bcg_coverage: 99,
            current_gdp_per_capita: 2500,
            simulated_gdp_per_capita: 2500,
            current_income_level: 'LM',
            simulated_income_level: 'UM',
            current_tb_incidence: 180,
            predicted_tb_incidence: 132,
            absolute_reduction: 48,
            relative_reduction_pct: 26.7,
            ci_lower: 120,
            ci_upper: 148,
            population: 1000000,
            cases_prevented_per_year: 480,
            country_story: 'Context story',
            scenario_explanation: 'Scenario summary',
            disclaimer: 'Disclaimer',
          })))
        }
        return Promise.reject(new Error(`Unhandled URL ${url}`))
      }),
    )

    renderWithProviders(<HomePage />, '/?country=India&scenario=combined')

    expect(await screen.findByText(/Explore TB futures/i)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/Scenario summary/i)).toBeInTheDocument())
    expect(screen.getByText(/Cases prevented/i)).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})
