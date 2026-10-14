// @vitest-environment jsdom
import '@/test/dom'
import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ParameterForm } from './ParameterForm'
import { SettingsForm } from './SettingsForm'
import { defaults, validateInputs, type Description, type Drafts, type Value } from './inputs'
import fixture from '../../../tests/fixtures/inputs.json'
const schema = fixture as Description
function Parameters({ onChange = vi.fn(), onPick = vi.fn(), errors = {}, description = schema, initial = defaults(description) }: { onChange?: (title: string, value: Value) => void; onPick?: () => void; errors?: Record<string, string>; description?: Description; initial?: Drafts }) {
  const [values, setValues] = useState(initial)
  return <TooltipProvider delayDuration={0}><ParameterForm schema={description} values={values} errors={errors} onPick={onPick} onChange={(title, value) => { setValues(previous => ({ ...previous, [title]: value })); onChange(title, value) }} /></TooltipProvider>
}
it.each([
  ['Moving-average period', '31'], ['Highlight multiplier', '1.37'], ['Reference price', '123.45'], ['Session description', '0930-1600:23456'], ['Moving-average color', '#11223344'],
])('UI-P01: typing %s updates the appropriate input without losing its exact draft', (title, value) => {
  const changed = vi.fn(); render(<Parameters onChange={changed} />)
  fireEvent.change(screen.getByLabelText(title), { target: { value } })
  expect(changed).toHaveBeenLastCalledWith(title, value)
  expect((screen.getByLabelText(title) as HTMLInputElement).value).toBe(value)
})
it.each([['Price source', 'hl2'], ['Moving-average type', 'SMA']])('UI-P02: %s option selection submits the declared value', async (title, value) => {
  const changed = vi.fn(); render(<Parameters onChange={changed} />); const user = userEvent.setup()
  await user.click(screen.getByLabelText(title)); await user.click(screen.getByRole('option', { name: value })); expect(changed).toHaveBeenLastCalledWith(title, value)
})
it('UI-P03: boolean dependency disables its input and step controls while retaining the draft', async () => {
  const changed = vi.fn(); render(<Parameters onChange={changed} />); const user = userEvent.setup()
  fireEvent.change(screen.getByLabelText('Highlight multiplier'), { target: { value: '1.41' } })
  await user.click(screen.getByRole('switch', { name: 'Show highlights' }))
  expect((screen.getByLabelText('Highlight multiplier') as HTMLInputElement).disabled).toBe(true)
  for (const action of ['Increase', 'Decrease']) expect((screen.getByRole('button', { name: `${action} Highlight multiplier` }) as HTMLButtonElement).disabled).toBe(true)
  await user.click(screen.getByRole('switch', { name: 'Show highlights' }))
  expect((screen.getByLabelText('Highlight multiplier') as HTMLInputElement).value).toBe('1.41')
})
it.each([['Moving-average period', 20, 1], ['Highlight multiplier', 1.02, 0.01]] as const)('UI-P04: %s increase/decrease use the declared increment', async (title, value, step) => {
  const changed = vi.fn(); render(<Parameters onChange={changed} />); const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: `Increase ${title}` })); expect(changed.mock.lastCall?.[1]).toBeCloseTo(value + step)
  await user.click(screen.getByRole('button', { name: `Decrease ${title}` })); expect(changed.mock.lastCall?.[1]).toBeCloseTo(value)
})
it('UI-P05: UTC datetime changes preserve milliseconds and an empty draft remains invalid', () => {
  const changed = vi.fn(); render(<Parameters onChange={changed} />)
  fireEvent.change(screen.getByLabelText('Highlight start'), { target: { value: '2026-10-14T01:02:03.456' } })
  expect(changed).toHaveBeenLastCalledWith('Highlight start', Date.parse('2026-10-14T01:02:03.456Z'))
  fireEvent.change(screen.getByLabelText('Highlight start'), { target: { value: '' } })
  expect(changed).toHaveBeenLastCalledWith('Highlight start', '')
  expect(validateInputs(schema, { ...defaults(schema), 'Highlight start': '' }).errors['Highlight start']).toBeTruthy()
})
it.each(['Reference price', 'Highlight start'])('UI-P06: chart picker for %s forwards the declared field', async title => {
  const pick = vi.fn(); render(<Parameters onPick={pick} />); await userEvent.setup().click(screen.getByRole('button', { name: `Pick ${title} on chart` })); expect(pick).toHaveBeenCalledWith(expect.objectContaining({ title }))
})
it('UI-P07: help control opens its declared tooltip', async () => {
  render(<Parameters />); await userEvent.setup().hover(screen.getByRole('button', { name: 'Help for Highlight multiplier' }))
  expect((await screen.findByRole('tooltip')).textContent).toContain('step is an adjustment increment')
})
it.each(schema.inputs.map(input => input.title))('UI-P08: validation error for %s is associated with its actual control', title => {
  render(<Parameters errors={{ [title]: 'Invalid field value' }} />)
  expect(screen.getByRole('alert').textContent).toBe('Invalid field value')
  const control = screen.getByLabelText(title)
  expect(control.getAttribute('aria-invalid')).toBe('true')
  expect(control.getAttribute('aria-describedby')).toBe(screen.getByRole('alert').id)
})
it('UI-P09: an out-of-range saved timestamp cannot crash the settings dialog', () => {
  const values = { ...defaults(schema), 'Highlight start': Number.MAX_SAFE_INTEGER }
  expect(() => render(<Parameters initial={values} />)).not.toThrow()
  expect(validateInputs(schema, values).errors['Highlight start']).toBeTruthy()
})
it('UI-P10: numeric dropdown options preserve numeric types', async () => {
  const description: Description = { ...schema, inputs: [{ ...schema.inputs[1], default: 2, options: [2, 5] }] }
  const changed = vi.fn(); render(<Parameters description={description} onChange={changed} />); const user = userEvent.setup()
  await user.click(screen.getByLabelText('Moving-average period')); await user.click(screen.getByRole('option', { name: '5' }))
  expect(changed).toHaveBeenLastCalledWith('Moving-average period', 5)
})

const choices: Record<string, string> = { commission_type: 'cash per order', default_qty_type: 'percent of equity', slippage_type: 'fixed', execution_timing: 'same close', end_policy: 'close at last close' }
it.each(Object.entries(schema.backtest.settings))('UI-S01: execution property %s can be changed with the correct request type', async (key, value) => {
  const changed = vi.fn(); render(<SettingsForm schema={schema} values={{}} onChange={changed} />)
  const control = document.getElementById('setting-' + key)!
  if (typeof value === 'boolean') { await userEvent.setup().click(control); expect(changed).toHaveBeenCalledWith({ [key]: !value }) }
  else if (choices[key]) {
    const user = userEvent.setup(); await user.click(control); await user.click(screen.getByRole('option', { name: new RegExp('^' + choices[key] + '$', 'i') }))
    expect(changed.mock.lastCall?.[0][key]).toBe(choices[key].replaceAll(' ', '_'))
    if (key.endsWith('_type')) expect(changed.mock.lastCall?.[0]).toHaveProperty(key.replace('_type', '_value'), key === 'default_qty_type' ? null : 0)
  } else { fireEvent.change(control, { target: { value: '2.5' } }); expect(changed).toHaveBeenCalledWith({ [key]: 2.5 }) }
})
it('UI-S02: blank nullable settings remain null, invalid numeric drafts are not coerced to zero', () => {
  const changed = vi.fn(); render(<SettingsForm schema={schema} values={{ max_gross_exposure: 2 }} onChange={changed} />)
  fireEvent.change(document.getElementById('setting-max_gross_exposure')!, { target: { value: '' } }); expect(changed).toHaveBeenLastCalledWith({ max_gross_exposure: null })
  fireEvent.change(document.getElementById('setting-cash')!, { target: { value: 'not-a-number' } }); expect(changed).toHaveBeenLastCalledWith({ max_gross_exposure: 2, cash: 'not-a-number' })
})
it('UI-S05: numeric execution properties preserve decimal drafts and surface invalid values', async () => {
  function Form() { const [values, setValues] = useState<Record<string, Value | null>>({}); return <SettingsForm schema={schema} values={values} onChange={setValues} /> }
  render(<Form />); const user = userEvent.setup(), field = screen.getByLabelText('Commission value') as HTMLInputElement
  await user.clear(field); await user.type(field, '0.'); expect(field.value).toBe('0.')
  await user.type(field, '25'); expect(field.value).toBe('0.25')
  await user.clear(field); await user.type(field, ' '); expect(field.getAttribute('aria-invalid')).toBe('true')
  expect(document.getElementById(field.getAttribute('aria-describedby')!)?.textContent).toBe('Enter a finite number')
})
