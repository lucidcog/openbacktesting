export interface LogFrame { workspacePath: string; line: number; sourceRevision?: string }
export interface LogRow { id: string; level: 'info' | 'warning' | 'error'; message: string; channel: 'strategy' | 'stdout' | 'stderr' | 'diagnostic'; time: string | null; timeKind: string; bar: number | null; frame?: LogFrame; phase?: string }
const record = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
export function logFrames(value: unknown): LogFrame[] {
  if (!value || typeof value !== 'object') return []
  if (Array.isArray(value)) return value.flatMap(logFrames)
  const item = record(value)
  return typeof item.workspacePath === 'string' && typeof item.line === 'number' ? [item as unknown as LogFrame] : Object.values(item).flatMap(logFrames)
}
export function logRows(value: unknown): { rows: LogRow[]; truncated: boolean } {
  const root = record(value), error = record(root.error)
  const structured = record(root.logs ?? error.logs ?? (Array.isArray(root.records) ? root : null))
  const rows: LogRow[] = (Array.isArray(structured.records) ? structured.records : []).map((value, index) => {
    const item = record(value), frame = logFrames(item)[0]
    return { id: `strategy-${index}`, channel: 'strategy', level: item.level === 'error' || item.level === 'warning' ? item.level : 'info', message: typeof item.message === 'string' ? item.message : '', time: typeof item.bar_time === 'string' ? item.bar_time : typeof item.recorded_at === 'string' ? item.recorded_at : null, timeKind: typeof item.bar_time === 'string' ? String(item.time_kind) : 'aware', bar: Number.isSafeInteger(item.bar_index) && Number(item.bar_index) >= 0 ? Number(item.bar_index) : null, frame, phase: typeof item.phase === 'string' ? item.phase : undefined }
  })
  for (const channel of ['stdout', 'stderr'] as const) {
    const stream = root[channel], text = typeof stream === 'string' ? stream : record(stream).text
    if (typeof text === 'string' && text) rows.push(...text.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n').map((message, index): LogRow => ({ id: `${channel}-${index}`, channel, level: 'info', message, time: null, timeKind: 'none', bar: null })))
  }
  const diagnostic = Object.keys(error).length ? error : root
  if (typeof diagnostic.message === 'string' || typeof root.text === 'string') rows.push({ id: 'diagnostic', channel: 'diagnostic', level: Object.keys(error).length || diagnostic.errorType ? 'error' : 'info', message: String(diagnostic.message ?? root.text), time: null, timeKind: 'none', bar: null, frame: logFrames(diagnostic)[0] })
  return { rows, truncated: [structured, record(root.stdout), record(root.stderr)].some(item => item.truncated === true) || root.logsIncomplete === true }
}
export function logTimestamp(row: LogRow, timezone: string) {
  if (!row.time) return row.bar === null ? '—' : `Bar ${row.bar}`
  if (row.timeKind === 'naive') return row.time
  const date = new Date(row.time)
  if (!Number.isFinite(date.getTime())) return row.time
  const fraction = row.time.match(/\.([0-9]+)/)?.[1]
  try { return new Intl.DateTimeFormat('sv-SE', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(date).replace(' ', 'T') + (fraction ? '.' + fraction : '') } catch { return row.time }
}

export function logMatcher(query: string, options: { matchCase: boolean; wholeWord: boolean; regex: boolean }) {
  try {
    const pattern = options.regex ? query : query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    // Validate the user expression before adding boundary groups.
    new RegExp(pattern, options.matchCase ? 'u' : 'iu')
    const matcher = new RegExp(options.wholeWord ? `(?<![\\p{L}\\p{N}_])(?:${pattern})(?![\\p{L}\\p{N}_])` : pattern, options.matchCase ? 'u' : 'iu')
    return { matches: (message: string) => matcher.test(message), error: '' }
  } catch {
    return { matches: () => false, error: 'Invalid regular expression. Correct the search or disable regular expressions.' }
  }
}
