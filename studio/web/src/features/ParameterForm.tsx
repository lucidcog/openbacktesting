import { Crosshair, HelpCircle } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { active, type Description, type Drafts, type InputSpec, type Value } from './inputs'

export function ParameterForm({ schema, values, errors, onChange, onPick }: { schema: Description; values: Drafts; errors: Record<string, string>; onChange: (title: string, value: Value) => void; onPick: (input: InputSpec) => void }) {
  const groups = [...new Set(schema.inputs.map(input => input.group))]
  if (!schema.inputs.length) return <p className="py-8 text-center text-muted-foreground">This strategy has no input parameters.</p>
  const render = (input: InputSpec) => {
    const value = values[input.title] ?? input.default, disabled = !active(input, schema, values)
    const id = `input-${input.attribute}`, error = errors[input.title]
    const date = input.kind === 'time' && typeof value === 'number' ? new Date(value) : null
    const dateValue = date && Number.isFinite(date.getTime()) ? date.toISOString().slice(0, -1) : ''
    const options = input.options ?? (input.kind === 'enum' ? input.members?.map(member => member.name) : undefined)
    return <div key={input.title} className="min-w-0 flex-1 space-y-2" data-input-kind={input.kind}>
      <div className="flex items-center gap-1.5"><Label htmlFor={id} className="text-xs">{input.title}</Label>{input.tooltip && <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon-xs" aria-label={`Help for ${input.title}`}><HelpCircle className="size-3" /></Button></TooltipTrigger><TooltipContent className="max-w-72">{input.tooltip}</TooltipContent></Tooltip>}{input.confirm && <span className="ml-auto text-[10px] text-primary">Confirm</span>}</div>
      {input.kind === 'bool' ? <Switch id={id} aria-invalid={!!error} aria-describedby={error ? id + '-error' : undefined} checked={value === true} disabled={disabled} onCheckedChange={checked => onChange(input.title, checked)} /> : options ? <Select value={JSON.stringify(value)} disabled={disabled} onValueChange={value => onChange(input.title, JSON.parse(value))}><SelectTrigger id={id} className="w-full" aria-invalid={!!error} aria-describedby={error ? id + '-error' : undefined}><SelectValue /></SelectTrigger><SelectContent>{options.map(option => <SelectItem key={String(option)} value={JSON.stringify(option)}>{input.members?.find(member => member.name === option)?.title ?? String(option)}</SelectItem>)}</SelectContent></Select> : input.kind === 'time' ? <div className="flex gap-1"><Input id={id} type="datetime-local" step="0.001" disabled={disabled} value={dateValue} onChange={event => onChange(input.title, event.target.value ? Date.parse(event.target.value + 'Z') : '')} aria-invalid={!!error} aria-describedby={error ? id + '-error' : id + '-unit'} /><Button variant="outline" size="icon" disabled={disabled} onClick={() => onPick(input)} aria-label={`Pick ${input.title} on chart`}><Crosshair /></Button></div> : <div className="flex gap-1">
        {input.kind === 'color' && <span className="size-8 shrink-0 rounded-sm border" style={{ backgroundColor: String(value) }} aria-hidden="true" />}
        <Input id={id} type="text" inputMode={['int', 'float', 'price'].includes(input.kind) ? 'decimal' : undefined} value={String(value)} disabled={disabled} onChange={event => onChange(input.title, event.target.value)} aria-invalid={!!error} aria-describedby={error ? id + '-error' : undefined} />
        {input.step !== undefined && <div className="flex"><Button variant="outline" size="icon" disabled={disabled} aria-label={`Decrease ${input.title}`} onClick={() => onChange(input.title, Number(value) - input.step!)}>−</Button><Button variant="outline" size="icon" disabled={disabled} aria-label={`Increase ${input.title}`} onClick={() => onChange(input.title, Number(value) + input.step!)}>+</Button></div>}
        {input.kind === 'price' && <Button variant="outline" size="icon" disabled={disabled} onClick={() => onPick(input)} aria-label={`Pick ${input.title} on chart`}><Crosshair /></Button>}
      </div>}
      {input.kind === 'time' && <p id={id + '-unit'} className="text-[10px] text-muted-foreground">UTC · Unix milliseconds</p>}
      {input.kind === 'color' && <p className="text-[10px] text-muted-foreground">#RRGGBBAA · final two digits control opacity</p>}
      {error && <p id={id + '-error'} role="alert" className="text-xs text-destructive">{error}</p>}
    </div>
  }
  return <div className="space-y-7">{groups.map(group => {
    const items = schema.inputs.filter(input => input.group === group), consumed = new Set<string>()
    return <section key={group} className="space-y-4"><h3 className="border-b pb-2 text-xs font-medium text-muted-foreground">{group || 'General'}</h3>{items.map(input => {
      if (consumed.has(input.title)) return null
      const row = input.inline ? items.filter(item => item.inline === input.inline) : [input]
      row.forEach(item => consumed.add(item.title))
      return <div key={input.title} className="flex flex-wrap gap-4">{row.map(render)}</div>
    })}</section>
  })}</div>
}
