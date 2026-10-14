import { expect, it } from 'vitest'
import fixture from '../../../tests/fixtures/inputs.json'
import type { Description, Value } from './inputs'
import { settingErrors } from './settings'
const schema = fixture as Description
it.each<[string, Value | null, object?]>([
  ['cash', ''], ['cash', ' '], ['cash', 0], ['cash', -1], ['margin', 0], ['margin', 1.1], ['spread', -0.1], ['spread', 1], ['risk_free_rate', -1], ['risk_free_rate', 1], ['commission_value', -10.1], ['commission_value', 10], ['commission_value', -1, { commission_type: 'cash_per_order' }], ['slippage_value', -1], ['default_qty_value', 0], ['default_qty_value', 101, { default_qty_type: 'percent_of_equity' }], ['max_gross_exposure', 0], ['margin', Infinity], ['cash', false], ['allow_short', 'true'], ['end_policy', 'unknown'],
])('UI-S03: rejects invalid %s=%s using core constraints', (key, value, extra = {}) => { expect(settingErrors(schema, { ...extra, [key]: value })[key]).toBeTruthy() })
it.each<Record<string, Value | null>>([{}, { commission_value: -10 }, { cash: 1, margin: .01, spread: .99, risk_free_rate: -.99 }, { default_qty_value: 100, default_qty_type: 'percent_of_equity' }, { max_gross_exposure: null, default_qty_value: null }, { slippage_value: 0, commission_type: 'cash_per_contract', commission_value: 0 }])('UI-S04: valid boundary configuration %j remains usable', values => { expect(settingErrors(schema, values)).toEqual({}) })
