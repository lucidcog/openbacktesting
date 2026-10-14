import { formatMetric, formatFact, label } from './report'
import { parse, type InputSpec, type Value } from './inputs'
export interface DomainDraft { enabled: boolean; kind: 'values' | 'range'; values: Value[]; start: string; stop: string; step: string }
export type SearchDomain = { kind: 'values'; values: Value[] } | { kind: 'range'; start: number | string; stop: number | string; step: number | string }
export function initialDomain(input: InputSpec, current?: Value): DomainDraft { return { enabled: false, kind: 'values', values: [current ?? input.default], start: String(current ?? input.default), stop: String(current ?? input.default), step: String(input.step ?? 1) } }
export function searchDomains(inputs: InputSpec[], drafts: Record<string, DomainDraft>) {
  const result: Record<string, SearchDomain> = {}
  for (const input of inputs) {
    const draft = drafts[input.title]
    if (!draft?.enabled) continue
    if (draft.kind === 'values') {
      if (!draft.values.length) throw Error(`${input.title}: add at least one value`)
      const values = draft.values.map(value => parse(input, value))
      if (new Set(values.map(value => JSON.stringify(value))).size !== values.length) throw Error(`${input.title}: duplicate candidates`)
      result[input.title] = { kind: 'values', values }
    } else {
      if (!['int', 'float', 'price'].includes(input.kind)) throw Error(`${input.title}: ranges require a numeric input`)
      const raw = [draft.start, draft.stop, draft.step]
      if (raw.some(value => !value.trim() || !Number.isFinite(Number(value))) || Number(draft.step) <= 0 || Number(draft.start) > Number(draft.stop)) throw Error(`${input.title}: use an ascending range with a positive step`)
      if (input.kind === 'int' && raw.some(value => !Number.isSafeInteger(Number(value)))) throw Error(`${input.title}: use integer bounds and step`)
      const [start, stop, step] = input.kind === 'int' ? raw.map(Number) : raw
      result[input.title] = { kind: 'range', start, stop, step }
    }
  }
  if (!Object.keys(result).length) throw Error('Select at least one input to optimize')
  return result
}
export interface Experiment { id: string; status: string; source: string; imported?: boolean; error?: string; info?: { total: number; checked: number; committed: number; skipped: number; failed: number; remaining: number }; plan?: { total: number; inputs: { schemaHash: string; values: Record<string, Value> }; dimensions: { title: string; values: Value[] }[]; execution: { backtest: { settings: Record<string, Value | null> } } } }
export interface ResultField { path: string; kind: string; unit: string | null; status: string | null; method: string | null; suggestedDirection: 'asc' | 'desc' }
export interface ResultRow { trial_id: string; ordinal: number; inputs: Record<string, Value>; values: Record<string, { value: unknown; status: string; unit: string | null; methodId: string | null }> }
export interface ResultPage { rows: ResultRow[]; cursor: string | null; watermark: number }
export const optimizing = (status: string) => ['planning', 'running', 'cancelling'].includes(status)
export function filterValue(value: string) { try { return JSON.parse(value) } catch { return value } }

export function resultLabel(path: string) {
  const summary = path.match(/^summary\.(all|long|short)\.([^.]+)\.value$/)
  return summary ? `${summary[1] === 'all' ? '' : summary[1] + ' · '}${label(summary[2])}` : label(path.replace(/\.value$/, ''))
}
export function resultValue(path: string, cell?: ResultRow['values'][string]) {
  if (!cell || cell.value === null || cell.status && cell.status !== 'ok') return '—'
  if (cell.unit && cell.unit !== 'ns' && (typeof cell.value === 'number' || typeof cell.value === 'string')) return formatMetric(path.split('.').at(-2) ?? path, { value: cell.value, unit: cell.unit, status: 'ok', methodId: cell.methodId ?? '', reason: null })
  return formatFact(path, cell.value) + (cell.unit === 'ns' ? ' ns' : '')
}
