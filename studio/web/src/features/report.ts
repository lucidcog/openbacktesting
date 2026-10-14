export interface Metric { value: number | string | null; unit: string; methodId: string; status: string; reason: string | null }
const percentages = new Set(['winRate', 'meanTradeReturn', 'averageProfitReturn', 'largestProfitReturn', 'largestProfitShare', 'averageLossReturn', 'largestLossReturn', 'largestLossShare', 'totalReturn', 'closedReturn', 'commissionLoad', 'returnOnInitialCapital', 'returnOnObservedCapital', 'buyHoldReturn', 'cagr'])
export function formatMetric(id: string, metric: Metric, currency?: string | null): string {
  if (metric.value === null || metric.status !== 'ok') return '—'
  if (metric.unit === 'nanoseconds') {
    const value = BigInt(metric.value), day = 86_400_000_000_000n
    return `${value / day}d ${(value % day) / 3_600_000_000_000n}h`
  }
  const value = Number(metric.value)
  if (!Number.isFinite(value)) return '—'
  if (metric.unit === 'ratio' && (percentages.has(id) || id.toLowerCase().includes('fraction'))) return new Intl.NumberFormat('en', { style: 'percent', maximumFractionDigits: 2 }).format(value)
  if (metric.unit === 'percent' || metric.unit === 'percentage_points') return value.toFixed(2) + '%'
  const formatted = new Intl.NumberFormat('en', { maximumFractionDigits: metric.unit === 'count' || metric.unit === 'bars' ? 0 : 2 }).format(value)
  return metric.unit === 'money' && currency ? formatted + ' ' + currency : formatted
}
export const label = (id: string) => id.replaceAll('.', ' · ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/^./, letter => letter.toUpperCase())
const moneyFields = new Set(['pnlNet', 'pnlGross', 'unrealizedPnlNet', 'unrealizedPnlGross', 'openPnlNet', 'openPnlGross', 'remainingEntryFee', 'feeTotal', 'fee', 'equity', 'balance', 'entryFeeAllocated', 'exitFee'])
export function formatFact(key: string, value: unknown, currency?: string | null) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number' && moneyFields.has(key)) return formatMetric(key, { value, unit: 'money', status: 'ok', methodId: '', reason: null }, currency)
  if (typeof value === 'number') return new Intl.NumberFormat('en', { maximumFractionDigits: 8 }).format(value)
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}
