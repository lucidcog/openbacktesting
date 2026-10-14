import { lazy, Suspense, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useSavedResource } from './saved-resource'
const CodeEditor = lazy(() => import('./CodeEditor'))
import { Search, Info, TriangleAlert, CircleAlert, Crosshair, FileCode2, RotateCcw } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { logFrames, logRows, logTimestamp, logMatcher, type LogFrame } from './logs'
export function LogPanel({ value, runId, dark, timezone = 'UTC', onBar }: { value: unknown; runId: string; dark: boolean; timezone?: string; onBar?: (bar: number) => void }) {
  const [requested, setRequested] = useState<{ runId: string; frame: LogFrame } | null>(null)
  const sourceRun = value && typeof value === 'object' && 'runId' in value ? String(value.runId) : runId
  const current = requested?.runId === sourceRun ? requested : null
  const resource = useSavedResource<{ path: string; content: string; revision: string; currentMatches: boolean }>(current ? `/runs/${sourceRun}/source?path=${encodeURIComponent(current.frame.workspacePath!)}` : null)
  const source = resource.value
  const [query, setQuery] = useState(''), [levels, setLevels] = useState(['info', 'warning', 'error'])
  const [channel, setChannel] = useState('all'), [after, setAfter] = useState(''), [page, setPage] = useState(0)
  const [searchOptions, setSearchOptions] = useState({ matchCase: false, wholeWord: false, regex: false })
  const matcher = logMatcher(query, searchOptions)
  const { rows, truncated } = logRows(value)
  const filtered = rows.filter(row => levels.includes(row.level) && (channel === 'all' || row.channel === channel) && matcher.matches(row.message) && (!after || row.time !== null && logTimestamp(row, timezone) >= after))
  const offset = Math.min(page * 100, Math.floor(Math.max(0, filtered.length - 1) / 100) * 100)
  const diagnosticFrames = logFrames(value && typeof value === 'object' ? { frames: 'frames' in value ? value.frames : [], error: 'error' in value ? value.error : null } : null).filter((frame, index, frames) => frames.findIndex(other => other.workspacePath === frame.workspacePath && other.line === frame.line) === index)
  return <div className="flex min-h-full flex-col text-xs" aria-label="Strategy logs">
    <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 border-b bg-background p-2">
      <div className="relative min-w-36 flex-1"><Search className="absolute left-2 top-2 size-3.5 text-muted-foreground" /><Input aria-label="Search logs" className="h-8 pl-7 text-xs" placeholder="Search logs…" value={query} onChange={event => { setQuery(event.target.value); setPage(0) }} /></div>
      {([['matchCase', 'Match case', 'Aa'], ['wholeWord', 'Match whole word', 'Ab'], ['regex', 'Use regular expression', '.*']] as const).map(([key, label, text]) => <Button key={key} variant={searchOptions[key] ? 'secondary' : 'ghost'} size="icon-sm" aria-label={label} title={label} aria-pressed={searchOptions[key]} onClick={() => { setSearchOptions(previous => ({ ...previous, [key]: !previous[key] })); setPage(0) }}>{text}</Button>)}
      <Select value={channel} onValueChange={value => { setChannel(value); setPage(0) }}><SelectTrigger aria-label="Log source" className="h-8 w-32"><SelectValue /></SelectTrigger><SelectContent>{['all', 'strategy', 'stdout', 'stderr', 'diagnostic'].map(value => <SelectItem key={value} value={value}>{value === 'all' ? 'All sources' : value}</SelectItem>)}</SelectContent></Select>
      {(['info', 'warning', 'error'] as const).map(level => { const Icon = level === 'error' ? CircleAlert : level === 'warning' ? TriangleAlert : Info; return <Button key={level} size="sm" variant={levels.includes(level) ? 'secondary' : 'ghost'} aria-label={`Show ${level} logs`} aria-pressed={levels.includes(level)} onClick={() => { setLevels(previous => previous.includes(level) ? previous.filter(item => item !== level) : [...previous, level]); setPage(0) }}><Icon className={`size-3.5 ${level === 'error' ? 'text-destructive' : level === 'warning' ? 'text-amber-500' : 'text-muted-foreground'}`} /><span className="capitalize">{level}</span></Button> })}
      <Label className="text-xs">From<Input aria-label="Logs from date and time" type="datetime-local" className="h-8 w-44 text-xs" value={after} onChange={event => { setAfter(event.target.value); setPage(0) }} /></Label>
      <Button variant="ghost" size="icon-sm" aria-label="Reset log filters" onClick={() => { setQuery(''); setLevels(['info', 'warning', 'error']); setChannel('all'); setAfter(''); setPage(0); setSearchOptions({ matchCase: false, wholeWord: false, regex: false }) }}><RotateCcw className="size-3.5" /></Button>
    </div>
    <div className="flex flex-wrap items-center gap-2 border-b px-3 py-1 text-muted-foreground"><span>{filtered.length} of {rows.length} messages · {timezone}</span><span className="ml-auto">{offset + (filtered.length ? 1 : 0)}–{Math.min(offset + 100, filtered.length)}</span><Button variant="ghost" size="sm" disabled={!offset} onClick={() => setPage(Math.max(0, offset / 100 - 1))}>Previous logs</Button><Button variant="ghost" size="sm" disabled={offset + 100 >= filtered.length} onClick={() => setPage(offset / 100 + 1)}>Next logs</Button></div>
    {matcher.error && <p role="alert" className="border-b px-3 py-2 text-destructive">{matcher.error}</p>}
    {truncated && <p role="status" className="border-b bg-amber-500/10 px-3 py-2">Some logs were truncated or not collected. Only available messages are shown.</p>}
    {!rows.length && <p className="p-4 text-muted-foreground">No logs were included with this report.</p>}
    {!!rows.length && !filtered.length && <p className="p-4 text-muted-foreground">No messages match these filters.</p>}
    <ol className="divide-y" aria-label="Log messages">{filtered.slice(offset, offset + 100).map(row => <li key={row.id} className={`group flex items-start gap-2 px-3 py-2 ${row.level === 'error' ? 'bg-destructive/5' : row.level === 'warning' ? 'bg-amber-500/5' : ''}`}>
      <span className={`mt-0.5 text-[10px] uppercase ${row.level === 'error' ? 'text-destructive' : row.level === 'warning' ? 'text-amber-500' : 'text-muted-foreground'}`}>{row.level}</span>
      <div className="min-w-0 flex-1"><div className="mb-0.5 flex flex-wrap gap-x-2 text-[10px] text-muted-foreground"><time title={row.time ?? undefined}>{logTimestamp(row, timezone)}</time><span>{row.channel}{row.phase ? ` · ${row.phase}` : ''}</span>{row.timeKind === 'naive' && <span>local time</span>}</div><p className="whitespace-pre-wrap break-words font-mono text-[11px]">{row.message || '(empty message)'}</p></div>
      <div className="flex shrink-0 opacity-60 group-hover:opacity-100 focus-within:opacity-100">{row.frame && <Button variant="ghost" size="icon-xs" aria-label={`Source code: ${row.frame.workspacePath}:${row.frame.line}`} title={`Source code: ${row.frame.workspacePath}:${row.frame.line}`} onClick={() => setRequested({ runId: sourceRun, frame: row.frame! })}><FileCode2 className="size-3.5" /></Button>}{row.bar !== null && <Button variant="ghost" size="icon-xs" aria-label={`Scroll to bar ${row.bar}`} title={`Scroll to bar ${row.bar}`} disabled={!onBar} onClick={() => onBar?.(row.bar!)}><Crosshair className="size-3.5" /></Button>}</div>
    </li>)}</ol>
    {!!diagnosticFrames.length && <div className="flex flex-wrap gap-2 border-t p-2">{diagnosticFrames.map(frame => <Button key={`${frame.workspacePath}:${frame.line}`} variant="ghost" size="sm" onClick={() => setRequested({ runId: sourceRun, frame })}>Snapshot: {frame.workspacePath}:{frame.line}</Button>)}</div>}
    <Dialog open={!!current} onOpenChange={open => { if (!open) setRequested(null) }}><DialogContent className="sm:max-w-4xl"><DialogHeader><DialogTitle>Source snapshot · {sourceRun.slice(0, 8)}</DialogTitle><DialogDescription>{current?.frame.workspacePath}:{current?.frame.line} · {source?.currentMatches ? 'Matches current disk version' : 'Historical version; current file differs or is unavailable'}</DialogDescription></DialogHeader><div className="h-96">{resource.loading && <p role="status">Loading source snapshot…</p>}{resource.error && <div role="alert"><p>{resource.error}</p><Button variant="outline" onClick={resource.retry}>Retry source</Button></div>}{source && current && <Suspense fallback={<p>Loading editor…</p>}><CodeEditor path={`snapshot/${sourceRun}/${source.path}`} value={source.content} line={current.frame.line} readonly dark={dark} onChange={() => {}} onSave={() => {}} /></Suspense>}</div></DialogContent></Dialog></div>
}
