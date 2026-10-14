export interface Numeric { values: (number | null)[]; valid: boolean[]; ready: boolean[]; missing: (string | null)[] }
export interface Axis { id: string; origin?: number; indices?: number[]; kind: 'utc-ns' | 'naive-datetime' | 'ordinal'; timezone: string | null; labels: string[] }
export interface Plot { leading?: { time: number; value: number | null; valid: boolean }[]; id: string; title: string; kind: 'line' | 'step' | 'histogram' | 'level'; pane: string; scale: string; source: string | null; color: string | null; gapPolicy: 'break' | 'connect'; offsetBars: number; value?: number; baseline?: number }
export interface Marker { id: string; pane: string; anchorBar: number; knownAtBar: number; shape: 'circle' | 'square' | 'triangle_up' | 'triangle_down'; position: 'above_bar' | 'below_bar' | 'price'; price: number | null; color: string | null; text: string }
export interface TradeFill { phase: string; sequence: number; fill_id: string; bar_index: number; price: number; qty: number; fee: number; side: 'buy' | 'sell' }
export interface Fill { id: string; lower: string; upper: string; pane: string; color: string; gapPolicy: 'break' | 'connect' }
export interface ColorEvent { kind: 'bar' | 'background'; pane: string; anchorBar: number; color: string | null; sequence: number }
export interface Plotting {
  display?: { aggregated: boolean; clusters: { bar: number; start: number; end: number; fillCount: number; signalCount: number; kind: string }[] };
  schemaVersion: string; requiredFeatures: string[]; axes: Axis[];
  panes: { id: string; title: string; axis: string; scale: string }[];
  scales: { id: string; pane: string; mode: string }[];
  sources: (Numeric & { id: string; axis: string })[]; plots: Plot[]; fills: Fill[];
  markers: Marker[]; colorEvents: ColorEvent[];
  market: { axis: string; open: Numeric; high: Numeric; low: Numeric; close: Numeric; volume: Numeric };
  tradingFacts: { fills: TradeFill[] }; execution: { processed: boolean[]; strategyNext: boolean[] };
}
export interface Point { time: number; value: number; breakBefore?: boolean; sampled?: boolean }
export const barAt = (axis: Axis, local: number) => axis.indices?.[local] ?? local + (axis.origin ?? 0)
export const localAt = (axis: Axis, bar: number) => axis.indices ? axis.indices.indexOf(bar) : bar - (axis.origin ?? 0)
/** Portfolio encodes naive wall-clock timestamps as nanoseconds, without a timezone. */
export function naiveNanosecondsLabel(value: string): string {
  const ns = BigInt(value), milliseconds = ns >= 0n ? ns / 1_000_000n : (ns - 999_999n) / 1_000_000n
  const fraction = ((ns % 1_000_000_000n + 1_000_000_000n) % 1_000_000_000n).toString().padStart(9, '0')
  return new Date(Number(milliseconds)).toISOString().slice(0, 19) + '.' + fraction
}
export function decode(value: unknown): Plotting {
  const data = value as Plotting
  if (!data || !['1.0.0', '1.1.0'].includes(data.schemaVersion)) throw new Error('Unsupported plotting version')
  if (!Array.isArray(data.requiredFeatures) || data.requiredFeatures.some(feature => !['core-v1', 'bar-coloring-v1'].includes(feature))) throw new Error('Unsupported required chart feature')
  for (const key of ['axes', 'panes', 'scales', 'sources', 'plots', 'fills', 'markers'] as const) if (!Array.isArray(data[key])) throw new Error(`Invalid plotting ${key}`)
  if (!data.colorEvents && data.schemaVersion === '1.0.0') data.colorEvents = []
  if (!Array.isArray(data.colorEvents) || !data.market || !data.tradingFacts || !Array.isArray(data.tradingFacts.fills)) throw new Error('Invalid plotting facts')
  const axis = data.axes.find(axis => axis.id === data.market.axis)
  if (!axis || !['utc-ns', 'naive-datetime', 'ordinal'].includes(axis.kind)) throw new Error('Invalid market axis')
  for (const source of [...data.sources, data.market.open, data.market.high, data.market.low, data.market.close, data.market.volume]) {
    if (!source || [source.values, source.valid, source.ready, source.missing].some(values => !Array.isArray(values) || values.length !== axis.labels.length)) throw new Error('Chart source length differs from its axis')
  }
  for (const axis of data.axes) {
    if (!Array.isArray(axis.labels) || axis.labels.some(label => typeof label !== 'string')) throw new Error('Invalid axis labels')
    if (axis.kind === 'utc-ns' && axis.labels.some(label => !/^-?\d+$/.test(label))) throw new Error('Invalid nanosecond label')
    if (axis.indices && (axis.indices.length !== axis.labels.length || axis.indices.some((bar, index) => !Number.isSafeInteger(bar) || index > 0 && bar <= axis.indices![index - 1]))) throw new Error('Invalid projected bar identities')
  }
  for (const source of [...data.sources, data.market.open, data.market.high, data.market.low, data.market.close, data.market.volume]) {
    if (source.values.some(value => value !== null && (typeof value !== 'number' || !Number.isFinite(value))) || source.valid.some(value => typeof value !== 'boolean') || source.ready.some(value => typeof value !== 'boolean')) throw new Error('Invalid numeric source or masks')
  }
  for (const plot of data.plots) {
    if (!['line', 'step', 'histogram', 'level'].includes(plot.kind) || !['break', 'connect'].includes(plot.gapPolicy) || !Number.isSafeInteger(plot.offsetBars) || plot.offsetBars < 0 || plot.offsetBars > 20000 || !data.panes.some(pane => pane.id === plot.pane) || !data.scales.some(scale => scale.id === plot.scale)) throw new Error('Invalid plot declaration')
    if (plot.kind !== 'level' && !data.sources.some(source => source.id === plot.source)) throw new Error('Missing plot source')
    if (plot.kind === 'level' && !Number.isFinite(plot.value)) throw new Error('Invalid level value')
  }
  for (const fill of data.fills) if (![fill.lower, fill.upper].every(id => data.plots.some(plot => plot.id === id))) throw new Error('Missing fill boundary')
  for (const marker of data.markers) if (!['circle', 'square', 'triangle_up', 'triangle_down'].includes(marker.shape) || !['above_bar', 'below_bar', 'price'].includes(marker.position) || marker.position === 'price' && !Number.isFinite(marker.price) || !Number.isSafeInteger(marker.anchorBar) || !Number.isSafeInteger(marker.knownAtBar)) throw new Error('Invalid marker')
  return data
}
export function exactLabel(axis: Axis, index: number, timezone = axis.timezone ?? 'UTC'): string {
  const local = localAt(axis, index)
  const label = axis.labels[local]
  if (label === undefined) { const last = barAt(axis, axis.labels.length - 1); return index > last ? `+${index - last} bars` : `Bar ${index}` }
  if (axis.kind !== 'utc-ns') return label
  const ns = BigInt(label), date = new Date(Number(ns >= 0n ? ns / 1_000_000n : (ns - 999_999n) / 1_000_000n))
  if (!Number.isFinite(date.getTime())) return label + ' ns UTC'
  const fraction = ((ns % 1_000_000_000n + 1_000_000_000n) % 1_000_000_000n).toString().padStart(9, '0')
  return new Intl.DateTimeFormat('en-GB', { timeZone: timezone, year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(date) + '.' + fraction
}
export function valid(source: Numeric, index: number) {
  return source.valid[index] && source.ready[index] && source.values[index] !== null && Number.isFinite(source.values[index])
}
export function segments(plot: Plot, data: Plotting): Point[][] {
  const axis = data.axes.find(axis => axis.id === data.market.axis)!
  const count = axis.labels.length
  if (plot.kind === 'level') return [[...Array(count)].map((_, time) => ({ time: barAt(axis, time), value: plot.value!, sampled: true }))]
  const source = data.sources.find(source => source.id === plot.source)
  if (!source) throw new Error(`Missing source for ${plot.title}`)
  const result: Point[][] = []; let current: Point[] = []
  for (const point of plot.leading ?? []) {
    if (point.valid && point.value !== null) current.push({ time: point.time, value: point.value, sampled: true, ...(current.length === 0 && result.length ? { breakBefore: true } : {}) })
    else if (plot.gapPolicy === 'break' && current.length) { result.push(current); current = [] }
  }
  for (let index = 0; index < count; index++) {
    if (valid(source, index)) current.push({ time: barAt(axis, index) + plot.offsetBars, value: source.values[index]!, sampled: true, ...(current.length === 0 && result.length ? { breakBefore: true } : {}) })
    else if (plot.gapPolicy === 'break' && current.length) { result.push(current); current = [] }
  }
  if (current.length) result.push(current)
  return result
}
export function finalColors(events: ColorEvent[], pane: string, kind: ColorEvent['kind']) {
  const colors = new Map<number, string | null>()
  for (const event of [...events].sort((a, b) => a.sequence - b.sequence)) if (event.pane === pane && event.kind === kind) colors.set(event.anchorBar, event.color)
  return colors
}
export function fillPolygons(lower: Point[], upper: Point[], connect: boolean): Point[][] {
  const top = new Map(upper.map(point => [point.time, point.value]))
  const pairs = lower.filter(point => top.has(point.time)).map(point => ({ ...point, top: top.get(point.time)! }))
  const polygons: Point[][] = []
  for (let index = 1; index < pairs.length; index++) {
    const a = pairs[index - 1], b = pairs[index]
    if (!connect && ((b.time !== a.time + 1 && !b.sampled) || b.breakBefore || upper.find(point => point.time === b.time)?.breakBefore)) continue
    const deltaA = a.value - a.top, deltaB = b.value - b.top
    if (deltaA * deltaB < 0) {
      const fraction = deltaA / (deltaA - deltaB)
      const cross = { time: a.time + fraction * (b.time - a.time), value: a.value + fraction * (b.value - a.value) }
      polygons.push([a, { time: a.time, value: a.top }, cross], [cross, b, { time: b.time, value: b.top }])
    } else polygons.push([a, b, { time: b.time, value: b.top }, { time: a.time, value: a.top }])
  }
  return polygons
}
/** Sweep overlapping boundary edges; different offsets, steps and gaps retain their own geometry. */
export function fillBetween(lower: Point[][], upper: Point[][], connect: boolean, lowerStep = false, upperStep = false): Point[][] {
  const edges = (segments: Point[][]) => (connect ? [segments.flat()] : segments).flatMap(segment => segment.slice(1).map((point, index) => [segment[index], point] as const))
  const a = edges(lower), b = edges(upper), result: Point[][] = []
  let i = 0, j = 0
  while (i < a.length && j < b.length) {
    const [a0, a1] = a[i], [b0, b1] = b[j], left = Math.max(a0.time, b0.time), right = Math.min(a1.time, b1.time)
    const at = (p: Point, q: Point, time: number, step: boolean) => step ? p.value : p.value + (q.value - p.value) * (time - p.time) / (q.time - p.time)
    if (right > left) {
      const av = [{ time: left, value: at(a0, a1, left, lowerStep), sampled: true }, { time: right, value: at(a0, a1, right, lowerStep), sampled: true }]
      const bv = [{ time: left, value: at(b0, b1, left, upperStep), sampled: true }, { time: right, value: at(b0, b1, right, upperStep), sampled: true }]
      result.push(...fillPolygons(av, bv, true))
    }
    if (a1.time <= b1.time) i++
    if (b1.time <= a1.time) j++
  }
  return result
}
export function interpolatedCoordinate(time: number, times: number[], coordinate: (time: number) => number | null) {
  const exact = coordinate(time)
  if (exact !== null) return exact
  let low = 0, high = times.length
  while (low < high) { const middle = (low + high) >> 1; if (times[middle] < time) low = middle + 1; else high = middle }
  if (!low || low >= times.length) return null
  const left = times[low - 1], right = times[low], a = coordinate(left), b = coordinate(right)
  return a === null || b === null ? null : a + (b - a) * (time - left) / (right - left)
}
