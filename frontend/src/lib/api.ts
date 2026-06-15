export interface AppConfig {
  covariates: string[]
  scenarios: string[]
  income_levels: string[]
  regions: string[]
  use_income: boolean
  target_source: string
  target_display: string
  target_transform?: string
}

export interface CountrySummary {
  country: string
  year: number
  tb_incidence: number
  tb_target_display: string
  population: number
  income_level: string | null
  region: string
  country_story: string
  rapid_dx_sites: number | null
  bcg_coverage?: number | null
  gdp_per_capita?: number | null
}

export interface SimulationResult {
  country: string
  scenario: string
  current_bcg_coverage: number | null
  simulated_bcg_coverage: number | null
  current_gdp_per_capita: number | null
  simulated_gdp_per_capita: number | null
  current_income_level: string | null
  simulated_income_level: string | null
  current_tb_incidence: number
  predicted_tb_incidence: number
  absolute_reduction: number
  relative_reduction_pct: number
  ci_lower: number
  ci_upper: number
  population: number
  cases_prevented_per_year: number
  country_story: string
  scenario_explanation: string
  disclaimer: string
}

export interface MapRow {
  country: string
  iso3: string
  tb_incidence?: number | null
  bcg_coverage?: number | null
  current_bcg_coverage?: number | null
  predicted_tb_incidence?: number | null
  gdp_per_capita?: number | null
  rapid_dx_sites?: number | null
  population?: number | null
  region?: string
}

export interface PrioritizationRow {
  country: string
  iso3: string
  region: string
  income_level: string | null
  population: number
  current_tb_incidence: number
  predicted_tb_incidence: number
  cases_prevented_per_year: number
  relative_reduction_pct: number
  current_bcg_coverage: number
  rapid_dx_sites: number | null
}

export interface PrioritizationResponse {
  bcg_target: number
  top: number
  target_display: string
  rows: PrioritizationRow[]
}

export interface ModelMetric {
  r2: number
  mae: number
  rmse: number
}

export interface ModelInfo {
  metrics: {
    rf: ModelMetric
    lr: ModelMetric
    gbm: ModelMetric
    rf_best_params: Record<string, string | number | null>
    rf_cv_best_score: number
    rf_cv_scoring: string
    target_transform: string
    train_rows: number
    test_rows: number
  }
  feature_importance: Record<string, number>
  diagnostics: {
    by_region: Array<{ region: string; count: number; mae: number; bias: number; rmse: number }>
    by_income: Array<{ income_level: string; count: number; mae: number; bias: number; rmse: number }>
    scatter_sample: Array<{
      country: string
      year: number
      actual: number
      predicted: number
      region: string
      income_level: string
    }>
  }
  model_card: string
  schema: AppConfig & { feature_columns: string[] }
  target_source: string
  target_display: string
  training_period: string
  test_period: string
  n_countries: number
}

export interface SimulationPayload {
  country: string
  scenario: string
  bcg_override?: number
  gdp_override?: number
  income_override?: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function joinUrl(path: string) {
  return `${API_BASE}${path}`
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(joinUrl(path), {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export function normalizeConfig(input: AppConfig): AppConfig {
  return {
    ...input,
    scenarios: input.scenarios ?? [],
    covariates: input.covariates ?? [],
    income_levels: input.income_levels ?? [],
    regions: input.regions ?? [],
  }
}

export function normalizeCountrySummary(input: CountrySummary): CountrySummary {
  return {
    ...input,
    rapid_dx_sites: input.rapid_dx_sites ?? null,
    bcg_coverage: input.bcg_coverage ?? null,
    gdp_per_capita: input.gdp_per_capita ?? null,
  }
}

export function normalizeSimulationResult(input: SimulationResult): SimulationResult {
  return {
    ...input,
    current_bcg_coverage: input.current_bcg_coverage ?? null,
    simulated_bcg_coverage: input.simulated_bcg_coverage ?? null,
    current_gdp_per_capita: input.current_gdp_per_capita ?? null,
    simulated_gdp_per_capita: input.simulated_gdp_per_capita ?? null,
    current_income_level: input.current_income_level ?? null,
    simulated_income_level: input.simulated_income_level ?? null,
  }
}

export const api = {
  fetchConfig: async () => normalizeConfig(await fetchJson<AppConfig>('/config')),
  fetchCountries: () => fetchJson<string[]>('/countries'),
  fetchCountry: async (name: string) =>
    normalizeCountrySummary(
      await fetchJson<CountrySummary>(`/country/${encodeURIComponent(name)}`),
    ),
  simulate: async (payload: SimulationPayload) =>
    normalizeSimulationResult(
      await fetchJson<SimulationResult>('/simulate', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    ),
  fetchMapData: () => fetchJson<MapRow[]>('/map-data'),
  fetchWhatIfMap: (bcgTarget: number) =>
    fetchJson<MapRow[]>(`/whatif-map?bcg=${encodeURIComponent(bcgTarget)}`),
  fetchPrioritization: (bcgTarget: number, top: number) =>
    fetchJson<PrioritizationResponse>(
      `/prioritize?bcg_target=${encodeURIComponent(bcgTarget)}&top=${encodeURIComponent(top)}`,
    ),
  fetchModelInfo: () => fetchJson<ModelInfo>('/model-info'),
}
