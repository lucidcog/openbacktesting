import { expect, it } from 'vitest'
import fixture from '../../../tests/fixtures/plotting.json'
import { decode, naiveNanosecondsLabel, exactLabel, fillPolygons, finalColors, segments } from './model'
it('decodes a real export and rejects future required features', () => {
  expect(decode(fixture).panes).toHaveLength(2)
  expect(() => decode({ ...fixture, requiredFeatures: ['future'] })).toThrow('required')
})
it('preserves ns identity, naive labels and ordinal labels', () => {
  const axis = { id: 'bars', kind: 'utc-ns' as const, timezone: 'UTC', labels: ['1000000001', '1000000002'] }
  expect(exactLabel(axis, 0)).not.toBe(exactLabel(axis, 1))
  expect(exactLabel({ ...axis, kind: 'ordinal', labels: ['abc'] }, 0)).toBe('abc')
  expect(exactLabel({ ...axis, kind: 'naive-datetime', labels: ['2026-01-01'] }, 0)).toBe('2026-01-01')
})
it('splits breaks, retains connected gaps and applies display offsets', () => {
  const data = decode(structuredClone(fixture)), plot = data.plots[0], source = data.sources[0]
  source.valid[20] = false; plot.offsetBars = 5
  expect(segments(plot, data)).toHaveLength(2)
  expect(segments(plot, data)[0][0].time).toBe(16)
  plot.gapPolicy = 'connect'
  expect(segments(plot, data)).toHaveLength(1)
})
it('resolves color clears without losing transparency or inheriting across bars', () => {
  const result = finalColors([{ kind: 'bar', pane: 'main', anchorBar: 1, color: '#ffffff00', sequence: 1 }, { kind: 'bar', pane: 'main', anchorBar: 2, color: 'red', sequence: 2 }, { kind: 'bar', pane: 'main', anchorBar: 2, color: null, sequence: 3 }], 'main', 'bar')
  expect(result.get(1)).toBe('#ffffff00'); expect(result.get(2)).toBeNull(); expect(result.has(3)).toBe(false)
})
it('splits crossing fills at the intersection and respects gaps', () => {
  const lower = [{ time: 0, value: 0 }, { time: 1, value: 2 }], upper = [{ time: 0, value: 2 }, { time: 1, value: 0 }]
  const shapes = fillPolygons(lower, upper, false)
  expect(shapes).toHaveLength(2); expect(shapes[0][2]).toEqual({ time: .5, value: 1 })
  expect(fillPolygons([{ time: 0, value: 0 }, { time: 2, value: 0 }], [{ time: 0, value: 2 }, { time: 2, value: 2 }], false)).toEqual([])
})
it('does not merge DST repeated local instants, and rejects malformed numeric data', () => {
  const axis = { id: 'bars', kind: 'utc-ns' as const, timezone: 'America/New_York', labels: ['1730611800000000001', '1730615400000000002'] }
  expect(exactLabel(axis, 0)).toContain('01:30:00.000000001')
  expect(exactLabel(axis, 1)).toContain('01:30:00.000000002')
  const data = structuredClone(fixture); data.sources[0].values[0] = Infinity
  expect(() => decode(data)).toThrow('numeric')
})
it('keeps original bar identities in projected arrays and masks missing values', () => {
  const data = decode(structuredClone(fixture)), axis = data.axes[0]
  axis.indices = axis.labels.map((_, index) => index * 10)
  const points = segments(data.plots[0], data)[0]
  expect(points[0].time).toBe(110)
  data.sources[0].ready[11] = false
  expect(segments(data.plots[0], data)[0][0].time).toBe(120)
})
it('fills stepped and independently offset boundaries and projects fractional crossings on sparse axes', async () => {
  const { fillBetween, interpolatedCoordinate } = await import('./model')
  const lower = [[{ time: 0, value: 0 }, { time: 10, value: 4 }]], upper = [[{ time: 2, value: 3 }, { time: 8, value: 3 }]]
  const stepped = fillBetween(lower, upper, false, true)
  expect(stepped[0].map(({ time, value }) => ({ time, value }))).toEqual([{ time: 2, value: 0 }, { time: 8, value: 0 }, { time: 8, value: 3 }, { time: 2, value: 3 }])
  expect(fillBetween(lower, upper, false)).toHaveLength(2)
  expect(interpolatedCoordinate(5, [0, 10], time => time === 0 ? 0 : time === 10 ? 100 : null)).toBe(50)
})

it.each([
  ['1704067200000000000', '2024-01-01T00:00:00.000000000'],
  ['1704067200000000001', '2024-01-01T00:00:00.000000001'],
  ['-1', '1969-12-31T23:59:59.999999999'],
])('formats naive Portfolio time %s without a timezone shift or loss of precision', (ns, label) => {
  expect(naiveNanosecondsLabel(ns)).toBe(label)
})
