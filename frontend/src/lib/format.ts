export const REGION_COLORS: Record<string, string> = {
  AFR: '#f26b3a',
  AMR: '#cc7f4f',
  EMR: '#99735d',
  EUR: '#766f67',
  SEA: '#5f6f68',
  WPR: '#43687b',
}

export const SCENARIO_LABELS: Record<string, string> = {
  baseline: 'Baseline',
  vaccine_push: 'Vaccine Push',
  income_up: 'Income Level Up',
  combined: 'Combined',
  custom: 'Custom Mix',
}

export const INCOME_LABELS: Record<string, string> = {
  L: 'Low income',
  LM: 'Lower-middle income',
  UM: 'Upper-middle income',
  H: 'High income',
}

export function fmtInt(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '—'
  return Math.round(value).toLocaleString()
}

export function fmtCompact(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

export function fmtPct(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) return '—'
  return `${value.toFixed(digits)}%`
}

export function fmtUsd(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function toTitleCase(input: string) {
  return input.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}
