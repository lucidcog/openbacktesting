export type Value = string | number | boolean
export type InputKind = 'int' | 'float' | 'bool' | 'string' | 'enum' | 'price' | 'time' | 'session' | 'color'
export interface InputSpec {
  title: string; attribute: string; kind: InputKind; default: Value; minval?: number; maxval?: number;
  step?: number; options?: Value[]; members?: { name: string; title: string }[];
  group: string; inline: string; tooltip: string; active: boolean | { title: string }; display: string; confirm: boolean;
}
export interface Description { schemaVersion: string; schemaHash: string; inputs: InputSpec[]; backtest: { settings: Record<string, Value | null> } }
export type Drafts = Record<string, Value>

export function defaults(schema: Description): Drafts { return Object.fromEntries(schema.inputs.map(input => [input.title, input.default])) }
export function active(input: InputSpec, schema: Description, values: Drafts, visited = new Set<string>()): boolean {
  if (typeof input.active === 'boolean') return input.active
  if (visited.has(input.title)) throw new Error('Cyclic input dependency')
  visited.add(input.title)
  const reference = schema.inputs.find(item => item.title === (input.active as { title: string }).title)
  return !!reference && values[reference.title] === true && active(reference, schema, values, visited)
}
export function parse(input: InputSpec, draft: Value): Value {
  let value: Value = draft
  if (['int', 'float', 'price', 'time'].includes(input.kind)) {
    if (typeof draft === 'boolean' || (typeof draft === 'string' && !draft.trim())) throw new Error('Enter a number')
    value = Number(draft)
    if (!Number.isFinite(value)) throw new Error('Enter a finite number')
    if (['int', 'time'].includes(input.kind) && !Number.isSafeInteger(value)) throw new Error('Enter a safe integer')
    if (input.kind === 'time' && !Number.isFinite(new Date(value).getTime())) throw new Error('Enter a valid UTC date')
    if (input.minval !== undefined && value < input.minval) throw new Error(`Minimum ${input.minval}`)
    if (input.maxval !== undefined && value > input.maxval) throw new Error(`Maximum ${input.maxval}`)
  } else if (input.kind === 'bool') {
    if (typeof value !== 'boolean') throw new Error('Choose true or false')
  } else if (typeof value !== 'string') throw new Error('Enter text')
  if (input.options && !input.options.includes(value)) throw new Error('Choose one of the available options')
  if (input.kind === 'enum' && !input.members?.some(member => member.name === value)) throw new Error('Choose an enum member')
  if (input.kind === 'color' && !/^#[0-9a-f]{6}([0-9a-f]{2})?$/i.test(String(value))) throw new Error('Use #RRGGBB or #RRGGBBAA')
  if (input.kind === 'session') {
    if (value === '24x7') return '0000-0000:1234567'
    const match = /^(\d{4}-\d{4}(?:,\d{4}-\d{4})*)(?::([1-7]+))?$/.exec(String(value))
    if (!match) throw new Error('Use HHMM-HHMM:days; for example 0930-1600:23456')
    const days = match[2] ?? '1234567'
    if (new Set(days).size !== days.length) throw new Error('Weekdays must not repeat')
    if (match[1].split(/[-,]/).some(clock => Number(clock.slice(0, 2)) > 23 || Number(clock.slice(2)) > 59)) throw new Error('Time range must be 0000–2359')
    value = match[1] + ':' + [...days].sort().join('')
  }
  return value
}
export function validateInputs(schema: Description, values: Drafts) {
  const errors: Record<string, string> = {}, parsed: Drafts = {}
  for (const input of schema.inputs) {
    try { parsed[input.title] = parse(input, values[input.title] ?? input.default) }
    catch (error) { errors[input.title] = String((error as Error).message) }
  }
  return { values: parsed, errors }
}
export function migrate(previous: Description, next: Description, values: Drafts) {
  const proposed = defaults(next), changes: string[] = []
  for (const input of next.inputs) {
    const old = previous.inputs.find(item => item.title === input.title)
    if (!old || old.kind !== input.kind) { changes.push(`${input.title}: new or changed type`); continue }
    if (JSON.stringify([old.options, old.minval, old.maxval, old.members]) !== JSON.stringify([input.options, input.minval, input.maxval, input.members])) changes.push(`${input.title}: choices or numeric limits changed`)
    try { proposed[input.title] = parse(input, values[input.title]) }
    catch { changes.push(`${input.title}: previous value is no longer valid`) }
  }
  for (const input of previous.inputs) if (!next.inputs.some(item => item.title === input.title)) changes.push(`${input.title}: removed`)
  return { proposed, changes }
}

export function pickedValues(schema: Description, input: InputSpec, point: { price: number | null; milliseconds: number | null }): Drafts {
  const fields = input.inline ? schema.inputs.filter(item => item.group === input.group && item.inline === input.inline && ['price', 'time'].includes(item.kind)) : [input]
  return Object.fromEntries(fields.map(field => {
    const value = field.kind === 'price' ? point.price : point.milliseconds
    if (value === null) throw new Error('The chart position has no compatible price or UTC time')
    return [field.title, parse(field, value)]
  }))
}
