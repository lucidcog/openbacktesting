import { expect, it } from 'vitest'
import { parseLayout, pairedSetting, BoundedCache } from './layout'
it('restores bounded layout preferences without touching drafts, selected runs or viewport', () => {
  expect(parseLayout('{bad')).toEqual({ chart: 58, bottom: 42 })
  expect(parseLayout('{"chart":70,"bottom":30}')).toEqual({ chart: 70, bottom: 30 })
  expect(parseLayout('{"chart":1,"bottom":99}')).toEqual({ chart: 58, bottom: 42 })
})
it('pairs quantity and cost units with deliberate values while retaining sparse overrides', () => {
  expect(pairedSetting({}, 'commission_type', 'cash_per_order')).toEqual({ commission_type: 'cash_per_order', commission_value: 0 })
  expect(pairedSetting({ cash: 2000 }, 'slippage_type', 'fixed')).toEqual({ cash: 2000, slippage_type: 'fixed', slippage_value: 0 })
  expect(pairedSetting({}, 'default_qty_type', 'percent_of_equity')).toEqual({ default_qty_type: 'percent_of_equity', default_qty_value: null })
})
it('keeps bounded cached ranges isolated by run ID', () => {
  const cache = new BoundedCache<number>(2)
  cache.set('a', '0', 10); cache.set('b', '0', 20)
  expect(cache.get('a', '0')).toBe(10); expect(cache.get('b', '0')).toBe(20)
  cache.set('c', '0', 30); expect(cache.get('a', '0')).toBeUndefined()
})
it('does not serialize an invalid optional numeric field into a valid null', async () => {
  const { validDataNumbers } = await import('./layout')
  const { defaultProfile } = await import('./DataForm')
  expect(validDataNumbers(defaultProfile)).toBe(true)
  expect(validDataNumbers({ ...defaultProfile, instrument: { ...defaultProfile.instrument, price_tick: NaN } })).toBe(false)
})
