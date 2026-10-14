import { expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { ParameterForm } from './ParameterForm'
import { TooltipProvider } from '@/components/ui/tooltip'
import fixture from '../../../tests/fixtures/inputs.json'
import { defaults, type Description } from './inputs'
import { SettingsForm } from './SettingsForm'
import { DataForm, defaultProfile } from './DataForm'
const schema = fixture as Description
it('renders all nine input kinds through styled accessible components, including display none', () => {
  const values = { ...defaults(schema), 'Show highlights': false }
  const html = renderToStaticMarkup(<TooltipProvider><ParameterForm schema={schema} values={values} errors={{ 'Moving-average period': 'Invalid number' }} onChange={() => {}} onPick={() => {}} /></TooltipProvider>)
  for (const kind of new Set(schema.inputs.map(input => input.kind))) expect(html).toContain(`data-input-kind="${kind}"`)
  for (const input of schema.inputs) expect(html).toContain(`id="input-${input.attribute}"`)
  expect(html).toContain('disabled=""'); expect(html).toContain('aria-invalid="true"'); expect(html).toContain('role="alert"')
  expect(html).toContain('data-slot="input"'); expect(html).toContain('data-slot="switch"'); expect(html).toContain('data-slot="select-trigger"')
})
it('renders explicit properties, timeframe and original source settings', () => {
  const html = renderToStaticMarkup(<SettingsForm schema={schema} values={{ commission_type: 'cash_per_order', commission_value: 2 }} onChange={() => {}} />)
  expect(html).toContain('cash per fill / unit'); expect(html).toContain('data-slot="input"')
  const data = renderToStaticMarkup(<DataForm value={defaultProfile} onChange={() => {}} />)
  expect(data).toContain('changing it does not resample prices'); expect(data).toContain('aria-label="Timeframe unit"')
})
it('keeps reports readable without chart/log assets and renders text inertly', async () => {
  const { ReportView } = await import('./ReportView')
  const { LogPanel } = await import('./LogPanel')
  const portfolio = await import('../../../tests/fixtures/portfolio.json')
  const report = structuredClone(portfolio.default)
  report.summary.all.closedFragmentCount.value = 0
  report.run.complete = false; report.run.terminationReason = 'stopped'
  const html = renderToStaticMarkup(<ReportView runId="test" report={report} tab="overview" dark onFill={() => {}} />)
  expect(html).toContain('stopped'); expect(html).toContain('Closed Fragment Count')
  const logs = renderToStaticMarkup(<LogPanel value={{ message: '<script>alert(1)</script>\nline two' }} runId="test" dark />)
  expect(logs).toContain('&lt;script&gt;'); expect(logs).not.toContain('<script>')
})
