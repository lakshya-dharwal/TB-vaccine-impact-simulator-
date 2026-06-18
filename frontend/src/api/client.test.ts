import { describe, expect, it } from 'vitest'

import { normalizeConfig, normalizeCountrySummary, normalizeSimulationResult } from '../lib/api'

describe('api client normalization', () => {
  it('fills config collections safely', () => {
    const result = normalizeConfig({
      covariates: [],
      scenarios: ['combined'],
      income_levels: [],
      regions: [],
      use_income: true,
      target_source: 'x',
      target_display: 'y',
    })
    expect(result.scenarios).toEqual(['combined'])
    expect(result.covariates).toEqual([])
  })

  it('normalizes nullable country context', () => {
    const result = normalizeCountrySummary({
      country: 'India',
      year: 2023,
      tb_incidence: 100,
      tb_target_display: 'WHO',
      population: 1000,
      income_level: 'LM',
      region: 'SEA',
      country_story: 'Story',
      rapid_dx_sites: null,
    })
    expect(result.rapid_dx_sites).toBeNull()
    expect(result.bcg_coverage).toBeNull()
  })

  it('normalizes simulation shape', () => {
    const result = normalizeSimulationResult({
      country: 'India',
      scenario: 'combined',
      current_bcg_coverage: null,
      simulated_bcg_coverage: 90,
      current_gdp_per_capita: null,
      simulated_gdp_per_capita: null,
      current_income_level: 'LM',
      simulated_income_level: 'UM',
      current_tb_incidence: 150,
      predicted_tb_incidence: 120,
      absolute_reduction: 30,
      relative_reduction_pct: 20,
      ci_lower: 100,
      ci_upper: 140,
      population: 1000,
      cases_prevented_per_year: 300,
      country_story: 'Story',
      scenario_explanation: 'Summary',
      disclaimer: 'Disclaimer',
    })
    expect(result.simulated_bcg_coverage).toBe(90)
    expect(result.current_gdp_per_capita).toBeNull()
  })
})
