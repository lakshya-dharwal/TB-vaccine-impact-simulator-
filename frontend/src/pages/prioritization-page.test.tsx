import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PrioritizationPage } from './prioritization-page'
import { renderWithProviders } from '../test/test-utils'

describe('PrioritizationPage', () => {
  it('loads prioritization rows and exposes controls', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({
            bcg_target: 90,
            top: 20,
            target_display: 'WHO',
            rows: [
              {
                country: 'Nigeria',
                iso3: 'NGA',
                region: 'AFR',
                income_level: 'LM',
                population: 1000000,
                current_tb_incidence: 210,
                predicted_tb_incidence: 165,
                cases_prevented_per_year: 450,
                relative_reduction_pct: 21.4,
                current_bcg_coverage: 64,
                rapid_dx_sites: 1.2,
              },
            ],
          })),
        ),
      ),
    )

    renderWithProviders(<PrioritizationPage />, '/prioritization?bcg_target=90&top=20')

    expect(await screen.findByText(/Find where BCG scale-up matters most/i)).toBeInTheDocument()
    expect(screen.getByText('Nigeria')).toBeInTheDocument()
    expect(screen.getByRole('slider', { name: /BCG target/i })).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})
