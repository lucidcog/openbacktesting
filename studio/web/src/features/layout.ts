export interface LayoutPreference { [key: string]: number; chart: number; bottom: number }
export function parseLayout(value: string | null): LayoutPreference {
  try { const layout = JSON.parse(value ?? 'null'); if (layout && Number.isFinite(layout.chart) && Number.isFinite(layout.bottom) && layout.chart >= 15 && layout.bottom >= 15 && Math.abs(layout.chart + layout.bottom - 100) < 1) return layout } catch { /* Restore a usable default after malformed local storage. */ }
  return { chart: 58, bottom: 42 }
}
export function pairedSetting(values: Record<string, string | number | boolean | null>, key: string, value: string | number | boolean | null) {
  return { ...values, [key]: value, ...(key.endsWith('_type') ? { [key.replace('_type', '_value')]: key === 'default_qty_type' ? null : 0 } : {}) }
}
export class BoundedCache<T> {
  private values = new Map<string, T>()
  constructor(private limit = 8) {}
  get(runId: string, range: string) { return this.values.get(runId + ':' + range) }
  set(runId: string, range: string, value: T) { const key = runId + ':' + range; this.values.delete(key); this.values.set(key, value); if (this.values.size > this.limit) this.values.delete(this.values.keys().next().value!) }
}
export function validDataNumbers(profile: { timeframe: { multiplier: number }; instrument: { quantity_step: number; price_tick: number | null; min_quantity: number | null; min_notional: number } }) {
  const instrument = profile.instrument
  return Number.isSafeInteger(profile.timeframe.multiplier) && profile.timeframe.multiplier > 0 &&
    Number.isFinite(instrument.quantity_step) && instrument.quantity_step > 0 &&
    Number.isFinite(instrument.min_notional) && instrument.min_notional >= 0 &&
    [instrument.price_tick, instrument.min_quantity].every(value => value === null || Number.isFinite(value) && value > 0)
}
