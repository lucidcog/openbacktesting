import { useEffect, useRef } from 'react'
import { createChartEx, CandlestickSeries, HistogramSeries, LineSeries, LineType, ColorType, createSeriesMarkers, type IChartApiBase, type ISeriesApi, type SeriesMarker, type SeriesMarkerShape } from 'lightweight-charts'
import { chartSync, rangeInteraction } from './sync'
import { BarScale } from './scale'
import { Bands } from './primitive'
import { decode, barAt, localAt, exactLabel, fillBetween, finalColors, segments, valid, type Plotting, type TradeFill } from './model'

export interface ChartSelection { bar: number; label: string; price: number | null; milliseconds: number | null; fills: TradeFill[]; markers: Plotting['markers']; cluster?: NonNullable<Plotting['display']>['clusters'][number] }
interface Props { data: Plotting; dark: boolean; selectedFill?: string; showSignals: boolean; showTrades: boolean; onSelect: (selection: ChartSelection) => void; onViewport?: (range: { from: number; to: number }) => void }

export function MarketChart({ data: raw, dark, selectedFill, showSignals, showTrades, onSelect, onViewport }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApiBase<number> | null>(null)
  const previousData = useRef(raw)
  const viewport = useRef<{ from: number; to: number } | null>(null)
  const paneFactors = useRef<number[]>([])
  const rangeCallback = useRef(onViewport)
  useEffect(() => { rangeCallback.current = onViewport }, [onViewport])
  const selection = useRef(onSelect)
  useEffect(() => { selection.current = onSelect }, [onSelect])
  useEffect(() => {
    if (!container.current) return
    if (previousData.current !== raw) { viewport.current = null; paneFactors.current = []; previousData.current = raw }
    const data = decode(raw), axis = data.axes.find(axis => axis.id === data.market.axis)!
    const chart = createChartEx<number, BarScale>(container.current, new BarScale(axis), {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: dark ? '#131722' : '#ffffff' }, textColor: dark ? '#b2b5be' : '#434651', fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 11, panes: { enableResize: true } },
      grid: { vertLines: { color: dark ? '#202530' : '#eef0f3' }, horzLines: { color: dark ? '#202530' : '#eef0f3' } },
      rightPriceScale: { borderColor: dark ? '#2a2e39' : '#e0e3eb' },
      timeScale: { borderColor: dark ? '#2a2e39' : '#e0e3eb', rightOffset: 5, minBarSpacing: .001 },
      crosshair: { mode: 0 },
    })
    chartRef.current = chart
    const market = chart.addSeries(CandlestickSeries, { upColor: '#089981', downColor: '#f23645', wickUpColor: '#089981', wickDownColor: '#f23645', borderVisible: false }, 0)
    const colors = finalColors(data.colorEvents, 'main', 'bar')
    const candles = axis.labels.map((_, index) => {
      const time = barAt(axis, index)
      if (![data.market.open, data.market.high, data.market.low, data.market.close].every(source => valid(source, index))) return { time }
      const color = colors.get(time)
      return { time, open: data.market.open.values[index]!, high: data.market.high.values[index]!, low: data.market.low.values[index]!, close: data.market.close.values[index]!, ...(color !== null && color !== undefined ? { color, wickColor: color, borderColor: color } : {}) }
    })
    const last = barAt(axis, axis.labels.length - 1)
    const futureEnd = data.plots.reduce((end, plot) => segments(plot, data).reduce((value, segment) => Math.max(value, segment.at(-1)?.time ?? last), end), last)
    market.setData([...candles, ...Array.from({ length: Math.max(0, futureEnd - last) }, (_, index) => ({ time: last + index + 1 }))])
    const panes = new Map<string, number>([['main', 0]])
    let nextPane = 1
    for (const pane of data.panes) if (pane.id !== 'main') panes.set(pane.id, nextPane++)
    // addSeries only appends one missing pane; reserve every index before volume.
    for (let index = 1; index <= nextPane; index++) chart.addPane(true)
    const volume = chart.addSeries(HistogramSeries, { title: 'Volume', priceFormat: { type: 'volume' }, priceLineVisible: false, lastValueVisible: false }, nextPane)
    volume.setData(axis.labels.map((_, index) => valid(data.market.volume, index) ? { time: barAt(axis, index), value: data.market.volume.values[index]!, color: data.market.close.values[index]! >= data.market.open.values[index]! ? '#08998180' : '#f2364580' } : { time: barAt(axis, index) }))
    const owners = new Map<string, ISeriesApi<'Line' | 'Candlestick' | 'Histogram', number>>([['main', market]])
    const palette = ['#2962ff', '#ff9800', '#9c68df', '#26a69a']
    for (const [index, plot] of data.plots.entries()) {
      const pane = panes.get(plot.pane)!
      for (const segment of segments(plot, data)) {
        if (plot.kind === 'histogram') {
          const series = chart.addSeries(HistogramSeries, { priceScaleId: data.panes.find(pane => pane.id === plot.pane)?.scale === plot.scale ? 'right' : plot.scale, title: plot.title, base: plot.baseline ?? 0, color: plot.color ?? palette[index % palette.length], priceLineVisible: false, lastValueVisible: false }, pane)
          series.setData(segment); if (!owners.has(plot.pane)) owners.set(plot.pane, series)
        } else {
          const series = chart.addSeries(LineSeries, { priceScaleId: data.panes.find(pane => pane.id === plot.pane)?.scale === plot.scale ? 'right' : plot.scale, title: plot.title, color: plot.color ?? palette[index % palette.length], lineWidth: 1, lineType: plot.kind === 'step' ? LineType.WithSteps : LineType.Simple, priceLineVisible: false, lastValueVisible: false }, pane)
          series.setData(segment); if (!owners.has(plot.pane)) owners.set(plot.pane, series)
        }
      }
    }
    for (const scale of data.scales) chart.priceScale(data.panes.find(pane => pane.id === scale.pane)?.scale === scale.id ? 'right' : scale.id, panes.get(scale.pane)).applyOptions({ mode: scale.mode === 'logarithmic' ? 1 : 0 })
    for (const [pane, index] of panes) {
      if (!owners.has(pane)) {
        const empty = chart.addSeries(LineSeries, { color: 'transparent', priceLineVisible: false, lastValueVisible: false }, index)
        empty.setData(axis.labels.map((_, i) => { const time = barAt(axis, i), marker = data.markers.find(marker => marker.pane === pane && marker.anchorBar === time); return marker ? { time, value: marker.price ?? 0 } : { time } }))
        owners.set(pane, empty)
      }
      owners.get(pane)!.attachPrimitive(new Bands([], 'transparent', finalColors(data.colorEvents, pane, 'background')))
    }
    const times = [...new Set([...axis.labels.map((_, index) => barAt(axis, index)), ...data.plots.flatMap(plot => segments(plot, data).flat().map(point => point.time))])].sort((a, b) => a - b)
    for (const fill of data.fills) {
      const lower = data.plots.find(plot => plot.id === fill.lower)!, upper = data.plots.find(plot => plot.id === fill.upper)!
      owners.get(fill.pane)!.attachPrimitive(new Bands(fillBetween(segments(lower, data), segments(upper, data), fill.gapPolicy === 'connect', lower.kind === 'step', upper.kind === 'step'), fill.color, undefined, times))
    }
    for (const [pane, owner] of owners) {
      const markers: SeriesMarker<number>[] = []
      if (showSignals) for (const marker of data.markers.filter(marker => marker.pane === pane)) {
        const shape: SeriesMarkerShape = marker.shape === 'triangle_up' ? 'triangleUp' : marker.shape === 'triangle_down' ? 'triangleDown' : marker.shape
        const common = { time: marker.anchorBar, id: marker.id, text: marker.text, color: marker.color ?? '#2962ff', shape }
        if (marker.position === 'price') markers.push({ ...common, position: 'atPriceMiddle', price: marker.price! })
        else markers.push({ ...common, position: marker.position === 'above_bar' ? 'aboveBar' : 'belowBar' })
      }
      if (pane === 'main' && showTrades) for (const fill of data.tradingFacts.fills) markers.push({ time: fill.bar_index, id: fill.fill_id, position: 'atPriceMiddle', price: fill.price, shape: 'square', color: fill.fill_id === selectedFill ? '#ffb300' : fill.side === 'buy' ? '#089981' : '#f23645', text: `${fill.side} ${fill.qty}` })
      if (pane === 'main') for (const cluster of data.display?.clusters ?? []) {
        const count = (showTrades ? cluster.fillCount : 0) + (showSignals ? cluster.signalCount : 0)
        if (count) markers.push({ time: cluster.bar, position: 'aboveBar', shape: 'circle', color: '#787b86', text: `${count} events · cluster` })
      }
      createSeriesMarkers(owner, markers.sort((a, b) => a.time - b.time), { autoScale: true })
    }
    chart.panes()[0]?.setStretchFactor(4)
    chart.panes()[nextPane]?.setStretchFactor(.65)
    if (paneFactors.current.length === chart.panes().length) chart.panes().forEach((pane, index) => pane.setStretchFactor(paneFactors.current[index]))
    if (viewport.current) chart.timeScale().setVisibleRange(viewport.current)
    else chart.timeScale().fitContent()
    const interaction = rangeInteraction(container.current)
    chart.subscribeCrosshairMove(event => chartSync.publish('market', { kind: 'cursor', bar: event.time ?? null }))
    chart.timeScale().subscribeVisibleTimeRangeChange(range => { if (range) { viewport.current = range; if (interaction.active()) { rangeCallback.current?.(range); chartSync.publish('market', { kind: 'range', ...range }) } } })
    const unsync = chartSync.subscribe('market', event => {
      if (event.kind === 'range') { interaction.suppress(); chart.timeScale().setVisibleRange(event); rangeCallback.current?.(event) }
      else if (event.bar === null) chart.clearCrosshairPosition()
      else { const value = data.market.close.values[localAt(axis, event.bar)]; if (typeof value === 'number') chart.setCrosshairPosition(value, event.bar, market) }
    })
    chartSync.publish('market', { kind: 'range', ...(viewport.current ?? { from: barAt(axis, 0), to: futureEnd }) })
    chart.subscribeClick(event => {
      if (event.time === undefined) return
      const bar = event.time, local = localAt(axis, bar), price = event.point && event.paneIndex === 0 ? market.coordinateToPrice(event.point.y) : null
      selection.current({ cluster: data.display?.clusters.find(cluster => cluster.start <= bar && bar < cluster.end), bar, label: exactLabel(axis, bar), price, milliseconds: axis.kind === 'utc-ns' && axis.labels[local] !== undefined ? Number(BigInt(axis.labels[local]) / 1_000_000n) : null, fills: data.tradingFacts.fills.filter(fill => fill.bar_index === bar), markers: data.markers.filter(marker => marker.anchorBar === bar) })
    })
    return () => { paneFactors.current = chart.panes().map(pane => pane.getStretchFactor()); interaction.dispose(); unsync(); chartRef.current = null; chart.remove() }
  }, [raw, dark, selectedFill, showSignals, showTrades])
  useEffect(() => {
    if (!selectedFill || !chartRef.current) return
    const fill = raw.tradingFacts.fills.find(fill => fill.fill_id === selectedFill)
    if (fill) {
      const range = { from: Math.max(0, fill.bar_index - 30), to: fill.bar_index + 30 }
      chartRef.current.timeScale().setVisibleRange(range)
      chartSync.publish('market', { kind: 'range', ...range })
    }
  }, [selectedFill, raw])
  return <div ref={container} className="h-full min-h-52 w-full" aria-label="Market chart with linked strategy panes" />
}
