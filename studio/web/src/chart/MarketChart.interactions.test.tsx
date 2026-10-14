// @vitest-environment jsdom
import '@/test/dom'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi, type Mock } from 'vitest'
import { createSeriesMarkers, type IPrimitivePaneRenderer } from 'lightweight-charts'
import fixture from '../../../tests/fixtures/plotting.json'
import matrix from '../../../tests/fixtures/plotting-matrix.json'
import type { Bands } from './primitive'
import type { BarScale } from './scale'
import { decode } from './model'
import { MarketChart } from './MarketChart'
import { EquityChart } from '@/features/EquityChart'
import { chartSync } from './sync'
interface SeriesDouble { kind: string; settings: { title?: string; lineType?: number; base?: number; color?: string; priceScaleId?: string }; pane: number; setData: Mock; attachPrimitive: Mock }
interface ChartDouble { axis: BarScale; options: { timeScale: { minBarSpacing: number } }; series: SeriesDouble[]; timeScale: () => { fitContent: Mock; setVisibleRange: Mock; subscribeVisibleTimeRangeChange: Mock }; subscribeClick: Mock; panes: () => { setStretchFactor: Mock; getStretchFactor: Mock }[]; remove: Mock }
const state = vi.hoisted(() => ({ charts: [] as ChartDouble[] }))
vi.mock('lightweight-charts', () => ({
  CandlestickSeries: 'candle', HistogramSeries: 'histogram', LineSeries: 'line', LineType: { Simple: 0, WithSteps: 1 }, ColorType: { Solid: 'solid' }, createSeriesMarkers: vi.fn(),
  createChartEx: vi.fn((_element, _axis, options) => {
    const panes = [{ setStretchFactor: vi.fn(), getStretchFactor: vi.fn(() => 1) }], series: SeriesDouble[] = []
    const scale = { fitContent: vi.fn(), setVisibleRange: vi.fn(), subscribeVisibleTimeRangeChange: vi.fn() }
    const chart = { axis: _axis, options, series, timeScale: () => scale, panes: () => panes,
      addPane: vi.fn(() => { const pane = { setStretchFactor: vi.fn(), getStretchFactor: vi.fn(() => 1) }; panes.push(pane); return pane }),
      addSeries: vi.fn((kind, settings, requested = 0) => {
        // The library appends one pane even when the requested index is further away.
        if (requested >= panes.length) panes.push({ setStretchFactor: vi.fn(), getStretchFactor: vi.fn(() => 1) })
        const item = { kind, settings, pane: Math.min(requested, panes.length - 1), setData: vi.fn(), attachPrimitive: vi.fn(), coordinateToPrice: vi.fn(() => 101) }
        series.push(item); return item
      }), priceScale: () => ({ applyOptions: vi.fn() }), subscribeCrosshairMove: vi.fn(), subscribeClick: vi.fn(), clearCrosshairPosition: vi.fn(), setCrosshairPosition: vi.fn(), remove: vi.fn() }
    state.charts.push(chart); return chart
  }),
}))
beforeEach(() => { state.charts.length = 0; chartSync.reset() })
const props = () => ({ data: decode(structuredClone(fixture)), dark: false, showSignals: true, showTrades: true, onSelect: vi.fn() })
it('UI-G13: strategy panes and volume retain distinct indices even when volume is added first', () => {
  const input = props(); render(<MarketChart {...input} />)
  const chart = state.charts[0], volume = chart.series.find((item) => item.settings.title === 'Volume')
  expect(volume?.pane).toBe(input.data.panes.length)
  for (const plot of input.data.plots) {
    const series = chart.series.find((item) => item.settings.title === plot.title)
    expect(series?.pane).toBe(input.data.panes.findIndex(pane => pane.id === plot.pane))
    expect(series?.pane).not.toBe(volume?.pane)
  }
})
it('UI-G14: both charts permit fitting more bars than the default pixel spacing allows', () => {
  render(<MarketChart {...props()} />)
  render(<EquityChart dark={false} curve={{ points: [{ bar: 0, time: { kind: 'ordinal', value: 'first' }, equity: 100, drawdown: 0, observations: [] }], total: 1, aggregated: false, method: '', unorderedCount: 0, unorderedBounds: [] }} />)
  for (const chart of state.charts) { expect(chart.options.timeScale.minBarSpacing).toBeLessThanOrEqual(.001); expect(chart.timeScale().fitContent).toHaveBeenCalledOnce() }
})
it('UI-G15: chart replacement removes its subscription and disposes its canvas', () => {
  const input = props(), { rerender, unmount } = render(<MarketChart {...input} />)
  const old = state.charts[0]; rerender(<MarketChart {...input} dark />)
  expect(old.remove).toHaveBeenCalledOnce()
  chartSync.publish('equity', { kind: 'range', from: 10, to: 20 })
  expect(old.timeScale().setVisibleRange).not.toHaveBeenCalled()
  expect(state.charts[1].timeScale().setVisibleRange).toHaveBeenCalledWith({ kind: 'range', from: 10, to: 20 })
  unmount(); expect(state.charts[1].remove).toHaveBeenCalledOnce()
})
it('UI-G16: deferred initialization and linked range notifications cannot trigger a refinement loop', () => {
  const onViewport = vi.fn(); render(<MarketChart {...props()} onViewport={onViewport} />)
  const changed = state.charts[0].timeScale().subscribeVisibleTimeRangeChange.mock.calls[0][0]
  changed({ from: 10, to: 30 }); expect(onViewport).not.toHaveBeenCalled()
  fireEvent.wheel(screen.getByLabelText('Market chart with linked strategy panes'))
  changed({ from: 12, to: 28 }); expect(onViewport).toHaveBeenCalledExactlyOnceWith({ from: 12, to: 28 })
  chartSync.publish('equity', { kind: 'range', from: 15, to: 25 })
  expect(onViewport).toHaveBeenCalledTimes(2)
  changed({ from: 16, to: 24 }); expect(onViewport).toHaveBeenCalledTimes(2)
})
it('UI-G17: a late equity chart restores the market range and cannot echo its deferred fit', () => {
  chartSync.publish('market', { kind: 'range', from: 100, to: 200 })
  render(<EquityChart dark={false} curve={{ points: [{ bar: 0, time: { kind: 'ordinal', value: 'first' }, equity: 100, drawdown: 0, observations: [] }], total: 1, aggregated: false, method: '', unorderedCount: 0, unorderedBounds: [] }} />)
  const chart = state.charts[0], received = vi.fn(), remove = chartSync.subscribe('market', received)
  expect(chart.timeScale().setVisibleRange).toHaveBeenCalledWith({ kind: 'range', from: 100, to: 200 })
  const changed = chart.timeScale().subscribeVisibleTimeRangeChange.mock.calls[0][0]
  changed({ from: 0, to: 10 }); expect(received).not.toHaveBeenCalled()
  fireEvent.pointerDown(screen.getByLabelText('Close-sampled equity and drawdown'))
  changed({ from: 2, to: 8 }); expect(received).toHaveBeenCalledExactlyOnceWith({ kind: 'range', from: 2, to: 8 })
  remove()
})

it('UI-G18: clicking an interior extrema sample opens its containing event cluster', () => {
  const input = props(), cluster = { bar: 29, start: 15, end: 30, fillCount: 1, signalCount: 15, kind: 'display-cluster' }
  input.data.display = { aggregated: true, clusters: [cluster] }
  render(<MarketChart {...input} />)
  const click = state.charts[0].subscribeClick.mock.calls[0][0]
  click({ time: 22, point: { y: 10 }, paneIndex: 0 })
  expect(input.onSelect).toHaveBeenLastCalledWith(expect.objectContaining({ bar: 22, cluster }))
  click({ time: 30, point: { y: 10 }, paneIndex: 0 })
  expect(input.onSelect).toHaveBeenLastCalledWith(expect.objectContaining({ bar: 30, cluster: undefined }))
})
it.each([[true, true, 16], [true, false, 15], [false, true, 1], [false, false, 0]])('UI-G19: aggregate marker visibility follows signals=%s and fills=%s', (showSignals, showTrades, count) => {
  vi.mocked(createSeriesMarkers).mockClear()
  const input = props()
  input.data.display = { aggregated: true, clusters: [{ bar: 29, start: 15, end: 30, fillCount: 1, signalCount: 15, kind: 'display-cluster' }] }
  render(<MarketChart {...input} showSignals={showSignals} showTrades={showTrades} />)
  const clusters = vi.mocked(createSeriesMarkers).mock.calls.flatMap(call => call[1] ?? []).filter(marker => marker.text?.includes('events · cluster'))
  expect(clusters.map(marker => marker.text)).toEqual(count ? [`${count} events · cluster`] : [])
})
it('UI-G23: theme and layer changes retain the user viewport', () => {
  const input = props(), { rerender } = render(<MarketChart {...input} />)
  const changed = state.charts[0].timeScale().subscribeVisibleTimeRangeChange.mock.calls[0][0]
  changed({ from: 10, to: 20 })
  rerender(<MarketChart {...input} dark showSignals={false} showTrades={false} />)
  expect(state.charts[1].timeScale().setVisibleRange).toHaveBeenCalledWith({ from: 10, to: 20 })
  expect(state.charts[1].timeScale().fitContent).not.toHaveBeenCalled()
})

it('UI-G24: theme and layer reconstruction preserve resized strategy pane proportions', () => {
  const input = props(), { rerender } = render(<MarketChart {...input} />)
  state.charts[0].panes().forEach((pane, index) => pane.getStretchFactor.mockReturnValue(index + 2))
  rerender(<MarketChart {...input} dark showSignals={false} />)
  state.charts[1].panes().forEach((pane, index) => expect(pane.setStretchFactor).toHaveBeenLastCalledWith(index + 2))
})

const matrixProps = () => ({ ...props(), data: decode(structuredClone(matrix)) })
const paneCases = [{ pane: 'main', index: 0 }, { pane: 'secondary', index: 1 }]
const plotCases = paneCases.flatMap(pane => ['line', 'step', 'histogram', 'level'].map(kind => ({ ...pane, kind })))
it.each(plotCases)('UI-V01: $kind renders correct values, style and scale in $pane', ({ pane, index, kind }) => {
  const input = matrixProps(); render(<MarketChart {...input} />)
  const rendered = state.charts[0].series.filter(series => series.settings.title === `${pane} ${kind}`)
  expect(rendered).toHaveLength(1)
  const series = rendered[0]
  expect(series.pane).toBe(index)
  expect(series.settings.priceScaleId).toBe('right')
  expect(series.kind).toBe(kind === 'histogram' ? 'histogram' : 'line')
  if (kind === 'histogram') expect(series.settings.base).toBe(95)
  else expect(series.settings.lineType).toBe(kind === 'step' ? 1 : 0)
  const column = kind === 'step' ? input.data.market.open : kind === 'histogram' ? input.data.market.low : input.data.market.close
  expect(series.setData).toHaveBeenCalledExactlyOnceWith(column.values.map((value, time) => ({ time, value: kind === 'level' ? 108 : value, sampled: true })))
  expect(series.settings.color).toBe(input.data.plots.find(plot => plot.id === `${pane}-${kind}`)!.color)
})

const markerCases = paneCases.flatMap(pane => ['circle', 'square', 'triangle_up', 'triangle_down'].flatMap(shape => ['above_bar', 'below_bar', 'price'].map(position => ({ ...pane, shape, position }))))
it.each(markerCases)('UI-V02: $shape at $position attaches to $pane only', ({ pane, index, shape, position }) => {
  vi.mocked(createSeriesMarkers).mockClear()
  const input = matrixProps(); render(<MarketChart {...input} />)
  const id = `${pane}-${shape}-${position}`, original = input.data.markers.find(marker => marker.id === id)!
  expect(original).toBeTruthy()
  const matches = vi.mocked(createSeriesMarkers).mock.calls.filter(([, markers]) => markers?.some(marker => marker.id === id))
  expect(matches).toHaveLength(1)
  expect((matches[0][0] as unknown as SeriesDouble).pane).toBe(index)
  expect(matches[0][1]?.find(marker => marker.id === id)).toEqual({
    time: original.anchorBar, id, text: original.text, color: original.color,
    shape: shape === 'triangle_up' ? 'triangleUp' : shape === 'triangle_down' ? 'triangleDown' : shape,
    position: position === 'price' ? 'atPriceMiddle' : position === 'above_bar' ? 'aboveBar' : 'belowBar',
    ...(position === 'price' ? { price: 103 } : {}),
  })
})

// Exercise the actual primitive renderer, not just the fact that a primitive was attached.
function paint(primitive: Bands, pane: number) {
  const paths: { color: string; points: number[][] }[] = [], rectangles: { color: string; bounds: number[] }[] = []
  let points: number[][] = []
  const context = { fillStyle: '', beginPath: () => { points = [] }, moveTo: (x: number, y: number) => points.push([x, y]), lineTo: (x: number, y: number) => points.push([x, y]), closePath: vi.fn(), fill: () => paths.push({ color: context.fillStyle, points }), fillRect: (...bounds: number[]) => rectangles.push({ color: context.fillStyle, bounds }) }
  primitive.attached({ chart: { timeScale: () => ({ timeToCoordinate: (time: number) => time * 10, options: () => ({ barSpacing: 10 }) }) }, series: { priceToCoordinate: (value: number) => (120 - value) * (pane + 1) } } as unknown as Parameters<Bands['attached']>[0])
  primitive.paneViews()[0].renderer().draw({ useMediaCoordinateSpace: (draw: (scope: unknown) => void) => draw({ context, mediaSize: { height: 200, width: 320 } }) } as Parameters<IPrimitivePaneRenderer['draw']>[0])
  return { paths, rectangles }
}
it.each(paneCases)('UI-V03: fill draws its polygon on $pane with that pane’s price coordinates', ({ pane, index }) => {
  const input = matrixProps(); render(<MarketChart {...input} />)
  const painted = state.charts[0].series.filter(series => series.pane === index).flatMap(series => series.attachPrimitive.mock.calls.map(([primitive]) => paint(primitive, index)))
  const paths = painted.flatMap(result => result.paths)
  expect(paths).toHaveLength(31)
  const color = input.data.fills.find(fill => fill.pane === pane)!.color
  expect(paths[0]).toEqual({ color, points: [[0, 20 * (index + 1)], [10, (120 - input.data.market.close.values[1]!) * (index + 1)], [10, 12 * (index + 1)], [0, 12 * (index + 1)]] })
  expect(paths.every(path => path.color === color)).toBe(true)
})
it.each(paneCases)('UI-V04: background paints full $pane height and a cleared bar stays unpainted', ({ pane, index }) => {
  const input = matrixProps(); render(<MarketChart {...input} />)
  const rectangles = state.charts[0].series.filter(series => series.pane === index).flatMap(series => series.attachPrimitive.mock.calls.flatMap(([primitive]) => paint(primitive, index).rectangles))
  const color = input.data.colorEvents.find(event => event.pane === pane && event.kind === 'background')!.color
  expect(rectangles).toContainEqual({ color, bounds: [15, 0, 10, 200] })
  expect(rectangles.some(rectangle => rectangle.bounds[0] === 25)).toBe(false)
  expect(rectangles.every(rectangle => rectangle.bounds[1] === 0 && rectangle.bounds[3] === 200)).toBe(true)
})
it('UI-V05: main candles use OHLC and candle overrides while volume stays in its own secondary pane', () => {
  const input = matrixProps(); render(<MarketChart {...input} />)
  const candles = state.charts[0].series.find(series => series.kind === 'candle')!
  expect(candles.pane).toBe(0)
  const points = candles.setData.mock.calls[0][0]
  expect(points[2]).toEqual({ time: 2, open: input.data.market.open.values[2], high: input.data.market.high.values[2], low: input.data.market.low.values[2], close: input.data.market.close.values[2], color: '#FFAA00FF', wickColor: '#FFAA00FF', borderColor: '#FFAA00FF' })
  expect(points[3]).not.toHaveProperty('color')
  const volume = state.charts[0].series.find(series => series.settings.title === 'Volume')!
  expect(volume.pane).toBe(2)
  expect(volume.setData.mock.calls[0][0][2]).toEqual({ time: 2, value: 102, color: '#08998180' })
})
it.each(plotCases.filter(item => item.kind !== 'level'))('UI-V06: $kind in $pane honors offsets and masks without bridging gaps', ({ pane, index, kind }) => {
  const input = matrixProps(), plot = input.data.plots.find(plot => plot.id === `${pane}-${kind}`)!
  const source = input.data.sources.find(source => source.id === plot.source)!
  source.ready[0] = false; source.valid[3] = false; plot.offsetBars = 2
  render(<MarketChart {...input} />)
  const series = state.charts[0].series.filter(series => series.settings.title === plot.title)
  expect(series).toHaveLength(2)
  expect(series.every(series => series.pane === index)).toBe(true)
  expect(series[0].setData.mock.calls[0][0].map((point: { time: number }) => point.time)).toEqual([3, 4])
  expect(series[1].setData.mock.calls[0][0][0]).toEqual({ time: 6, value: source.values[4], sampled: true, breakBefore: true })
})

it('UI-V07: real naive exports use date ticks and exact crosshair labels in market and equity panes', () => {
  render(<MarketChart {...matrixProps()} />)
  render(<EquityChart dark={false} curve={{ points: [{ bar: 0, time: { kind: 'naive', value: '1704067200000000000' }, equity: 100, drawdown: 0, observations: [] }], total: 1, aggregated: false, method: '', unorderedCount: 0, unorderedBounds: [] }} />)
  for (const chart of state.charts) {
    expect(chart.axis.formatTickmark({ time: 0 } as unknown as Parameters<BarScale['formatTickmark']>[0])).toBe('2024-01-01')
    expect(chart.axis.formatHorzItem(0 as unknown as Parameters<BarScale['formatHorzItem']>[0])).toMatch(/^2024-01-01T00:00:00/)
  }
})
