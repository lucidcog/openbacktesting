import { useState } from 'react'
import { settingChoices as choices, settingErrors } from './settings'
import { pairedSetting } from './layout'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { label } from './report'
import type { Description, Value } from './inputs'
function NumericSetting({ id, value, nullable, error, onChange }: { id: string; value: Value | null; nullable: boolean; error?: string; onChange: (value: Value | null) => void }) {
  const [draft, setDraft] = useState({ source: value, text: String(value ?? '') })
  const text = Object.is(draft.source, value) ? draft.text : String(value ?? '')
  return <Input id={id} inputMode="decimal" value={text} aria-invalid={!!error} aria-describedby={error ? id + '-error' : undefined} onChange={event => {
    const text = event.target.value, next = !text.trim() ? nullable ? null : '' : Number.isFinite(Number(text)) ? Number(text) : text
    setDraft({ source: next, text }); onChange(next)
  }} />
}
export function SettingsForm({ schema, values, onChange }: { schema: Description; values: Record<string, Value | null>; onChange: (value: Record<string, Value | null>) => void }) {
  const effective = { ...schema.backtest.settings, ...values }, errors = settingErrors(schema, values)
  const update = (key: string, value: Value | null) => onChange(pairedSetting(values, key, value))
  return <div className="grid grid-cols-2 gap-x-5 gap-y-4">{Object.entries(schema.backtest.settings).map(([key, defaultValue]) => {
    const value = effective[key], id = 'setting-' + key
    const unit = key === 'commission_value' ? effective.commission_type === 'percent' ? 'percentage points' : 'cash per fill / unit' : key === 'slippage_value' ? effective.slippage_type === 'bps' ? 'basis points' : 'price distance' : ['spread', 'margin', 'risk_free_rate'].includes(key) ? 'fraction' : key === 'default_qty_value' ? effective.default_qty_type === 'fixed' ? 'asset units' : 'percent of equity' : ''
    return <div key={key} className="space-y-2"><Label htmlFor={id} className="text-xs">{label(key.replaceAll('_', ' '))}</Label>{typeof defaultValue === 'boolean' ? <div><Switch id={id} checked={value === true} onCheckedChange={checked => update(key, checked)} /></div> : choices[key] ? <Select value={String(value)} onValueChange={next => update(key, next)}><SelectTrigger id={id} className="w-full"><SelectValue /></SelectTrigger><SelectContent>{choices[key].map(option => <SelectItem key={option} value={option}>{label(option.replaceAll('_', ' '))}</SelectItem>)}</SelectContent></Select> : <NumericSetting id={id} value={value} nullable={['default_qty_value', 'max_gross_exposure'].includes(key)} error={errors[key]} onChange={next => update(key, next)} />}{errors[key] && <p id={id + '-error'} role="alert" className="text-xs text-destructive">{errors[key]}</p>}{unit && <p className="text-[10px] text-muted-foreground">{unit}</p>}</div>
  })}</div>
}
