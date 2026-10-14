import { useEffect, useRef } from 'react'
import { createChartEx, LineSeries, ColorType } from 'lightweight-charts'
import { chartSync, rangeInteraction, sampleAt } from '@/chart/sync'
import { BarScale } from '@/chart/scale'
import { naiveNanosecondsLabel } from '@/chart/model'
export interface Curve { points: { bar: number; time: { kind: string; value: string }; equity: number; drawdown: number | null; observations: Record<string, unknown>[] }[]; total: number; aggregated: boolean; method: string; unorderedCount: number; unorderedBounds: Record<string, unknown>[] }
export function EquityChart({ curve, dark }: { curve: Curve; dark: boolean }) {
  const container = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!container.current || !curve.points.length) return
    const points = curve.points
    const labels: string[] = []
    for (const point of points) labels[point.bar] = point.time.kind === 'naive' ? naiveNanosecondsLabel(point.time.value) : point.time.value
    const axis = { id: 'equity', labels, timezone: 'UTC', kind: (points[0].time.kind === 'aware' ? 'utc-ns' : points[0].time.kind === 'naive' ? 'naive-datetime' : 'ordinal') as 'utc-ns' | 'naive-datetime' | 'ordinal' }
    const chart = createChartEx<number, BarScale>(container.current, new BarScale(axis), { autoSize: true, timeScale: { minBarSpacing: .001 }, layout: { background: { type: ColorType.Solid, color: dark ? '#131722' : '#ffffff' }, textColor: dark ? '#b2b5be' : '#434651', fontSize: 10 }, grid: { vertLines: { visible: false }, horzLines: { color: dark ? '#202530' : '#eef0f3' } } })
    const equity = chart.addSeries(LineSeries, { title: 'Equity · close', color: '#2962ff', lineWidth: 2, priceLineVisible: false })
    equity.setData(points.map(point => ({ time: point.bar, value: point.equity })))
    const drawdown = chart.addSeries(LineSeries, { title: 'Drawdown · close', color: '#f23645', lineWidth: 1, priceFormat: { type: 'percent' }, priceLineVisible: false }, 1)
    drawdown.setData(points.map(point => point.drawdown === null ? { time: point.bar } : { time: point.bar, value: point.drawdown * 100 }))
    chart.timeScale().fitContent()
    const interaction = rangeInteraction(container.current)
    chart.subscribeCrosshairMove(event => chartSync.publish('equity', { kind: 'cursor', bar: event.time ?? null }))
    chart.timeScale().subscribeVisibleTimeRangeChange(range => { if (range && interaction.active()) chartSync.publish('equity', { kind: 'range', ...range }) })
    const unsync = chartSync.subscribe('equity', event => {
      if (event.kind === 'range') { interaction.suppress(); chart.timeScale().setVisibleRange(event) }
      else if (event.bar === null) chart.clearCrosshairPosition()
      else { const point = sampleAt(points, event.bar); if (point) chart.setCrosshairPosition(point.equity, event.bar, equity) }
    }, true)
    return () => { interaction.dispose(); unsync(); chart.remove() }
  }, [curve, dark])
  return <div><div ref={container} className="h-56" aria-label="Close-sampled equity and drawdown" /><p className="px-3 pt-1 text-[10px] text-muted-foreground">{curve.method} {curve.aggregated ? 'Extrema-preserving display aggregation.' : ''} {curve.unorderedCount > 0 ? `${curve.unorderedCount} unordered intrabar observations are available in the account table; they are not connected as a path.` : ''}</p></div>
}
