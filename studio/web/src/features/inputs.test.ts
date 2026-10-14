import { expect, it } from 'vitest'
import fixture from '../../../tests/fixtures/inputs.json'
import { active, defaults, migrate, parse, validateInputs, type Description } from './inputs'

const schema = fixture as Description
it('preserves all nine kinds, title identities and disabled values', () => {
  expect(new Set(schema.inputs.map(input => input.kind)).size).toBe(9)
  const values = defaults(schema)
  values['Show highlights'] = false
  const multiplier = schema.inputs.find(input => input.title === 'Highlight multiplier')!
  expect(active(multiplier, schema, values)).toBe(false)
  expect(validateInputs(schema, values).values[multiplier.title]).toBe(1.02)
  expect(schema.inputs.find(input => input.kind === 'color')?.display).toBe('none')
})
it('rejects invalid numeric drafts but does not invent step divisibility', () => {
  const input = schema.inputs.find(input => input.kind === 'float')!
  expect(parse(input, 1.015)).toBe(1.015)
  for (const value of ['', true, Infinity, 'Infinity']) expect(() => parse(input, value)).toThrow()
})
it('preserves alpha, enum names and millisecond time values', () => {
  const values = validateInputs(schema, defaults(schema))
  expect(values.errors).toEqual({})
  expect(values.values['Moving-average color']).toBe('#22AA44FF')
  expect(values.values['Moving-average type']).toBe('EMA')
  expect(values.values['Highlight start']).toBe(1092873600000)
})
it('does not silently migrate renamed or constrained inputs', () => {
  const next = structuredClone(schema)
  next.inputs[1].maxval = 3
  const result = migrate(schema, next, defaults(schema))
  expect(result.changes).toContain('Moving-average period: previous value is no longer valid')
})
it('fills an inline price/time pair atomically without executing anything', async () => {
  const { pickedValues } = await import('./inputs')
  const paired = structuredClone(schema), price = paired.inputs.find(input => input.kind === 'price')!, time = paired.inputs.find(input => input.kind === 'time')!
  price.group = time.group = 'Pick'; price.inline = time.inline = 'anchor'
  expect(pickedValues(paired, price, { price: 123.45, milliseconds: 1700000000123 })).toEqual({ [price.title]: 123.45, [time.title]: 1700000000123 })
  expect(() => pickedValues(paired, price, { price: 123, milliseconds: null })).toThrow()
})
it.each(['2400-1600', '0930-2360', '9961-9999:123', '0930-1600:223', '0930-1600:0'])('UI-P11: invalid session %s is rejected before submission', value => {
  expect(() => parse(schema.inputs.find(input => input.kind === 'session')!, value)).toThrow()
})
it.each([['24x7', '0000-0000:1234567'], ['2200-0600:765', '2200-0600:567'], ['0930-1200,1300-1600', '0930-1200,1300-1600:1234567']])('UI-P12: session %s is normalized like the core', (value, expected) => {
  expect(parse(schema.inputs.find(input => input.kind === 'session')!, value)).toBe(expected)
})
