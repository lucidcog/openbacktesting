import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { Activity, PanelLeft, Play, Save, Settings2, Sun, Moon, Download, Upload, Square, X, ChevronDown, ChevronUp, FileCode2, RefreshCw, Search, FolderOpen, PanelBottom, PanelRight } from 'lucide-react'
import { Brand } from '@/components/Brand'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { api, ApiError } from '@/protocol/client'
import { parseLayout, BoundedCache, validDataNumbers } from '@/features/layout'
import { ParameterForm } from '@/features/ParameterForm'
import { useSavedResource } from '@/features/saved-resource'
import { WorkspacePicker } from '@/features/WorkspacePicker'
import { DataForm, defaultProfile, type DataProfile } from '@/features/DataForm'
import { settingErrors } from '@/features/settings'
import { SettingsForm } from '@/features/SettingsForm'
import { defaults, migrate, pickedValues, validateInputs, type Drafts, type InputSpec, type Value } from '@/features/inputs'
import { dirty, external, merge, saved, type Buffer, type DiskFile } from '@/features/editor-state'
import { prepareRun, ReviewRequired, LatestRequest, configurationIdentity, type Discovery } from '@/features/workflow'
import { ChartBoundary } from '@/chart/ChartBoundary'
import { MarketChart, type ChartSelection } from '@/chart/MarketChart'
import { decode, type Plotting } from '@/chart/model'
import { OptimizerPanel } from '@/features/OptimizerPanel'
import { LogPanel } from '@/features/LogPanel'
import { ReportView, type Report } from '@/features/ReportView'
const CodeEditor = lazy(() => import('@/features/CodeEditor'))
interface Capabilities { workspaceId: string; suggestedWorkspace: string; mode: string; workspace: string | null; interpreter: { compatible: boolean; executable?: string; message?: string }; capabilities: { edit: boolean; discover: boolean } }
interface Run { createdAt?: number; startedAt?: number; id: string; status: string; phase?: string; sourceHash?: string; sourceFiles?: Record<string, string>; request?: { source: { path: string; revision: string }; inputs: { values: Drafts }; settings: Record<string, Value | null>; data: DataProfile }; imported?: boolean; error?: unknown; stdout?: unknown; stderr?: unknown }
interface ChartResponse { plotting: Plotting; window: { start: number; end: number; total: number; granularity: number } }
interface Preset { schemaVersion: number; name: string; inputs: { schemaVersion: string; schemaHash: string; values: Drafts }; settings: Record<string, Value | null> }
const activeStatus = (run: Run) => ['queued', 'running', 'cancelling'].includes(run.status)
const message = (error: unknown) => error instanceof Error ? error.message : String(error)
const json = (value: unknown) => JSON.stringify(value, null, 2)
const loadPreference = (key: string, fallback: string) => { try { return localStorage.getItem('studio.' + key) ?? fallback } catch { return fallback } }
const savePreference = (key: string, value: string) => { try { localStorage.setItem('studio.' + key, value) } catch { /* Storage may be disabled. */ } }

export default function App() {
  const [optimizerMounted, setOptimizerMounted] = useState(false), [optimizerActive, setOptimizerActive] = useState(false)
  const [workspacePicker, setWorkspacePicker] = useState(false), [reportError, setReportError] = useState('')
  const selectedId = useRef(''), resultCache = useRef(new BoundedCache<unknown>(24))
  const [resultAttempt, setResultAttempt] = useState(0), [windowError, setWindowError] = useState(''), [chartLoading, setChartLoading] = useState(false)
  const lastWindow = useRef<{ runId: string; start: number; fill?: string; end?: number } | null>(null)
  const [now, setNow] = useState(0)
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer) }, [])
  const [cap, setCap] = useState<Capabilities | null>(null), [error, setError] = useState(''), [busy, setBusy] = useState('')
  const [files, setFiles] = useState<string[]>([]), [path, setPath] = useState(''), [buffers, setBuffers] = useState<Record<string, Buffer>>({})
  const fileSelection = useRef(0), fileReads = useRef(new Map<string, Promise<DiskFile>>())
  const actions = useRef(new Map<number, string>()), actionSequence = useRef(0)
  const [fileQuery, setFileQuery] = useState(''), fileSearch = useRef<HTMLInputElement>(null)
  const [discovery, setDiscovery] = useState<Discovery | null>(null), [values, setValues] = useState<Drafts>({}), [settings, setSettings] = useState<Record<string, Value | null>>({}), [data, setData] = useState(defaultProfile)
  const [sourceRoots, setSourceRoots] = useState('.'), [sourceResources, setSourceResources] = useState('')
  const [runs, setRuns] = useState<Run[]>([]), [selected, setSelected] = useState(''), [pending, setPending] = useState(''), [report, setReport] = useState<Report | null>(null), [chart, setChart] = useState<ChartResponse | null>(null), [chartError, setChartError] = useState('')
  const [logs, setLogs] = useState<unknown>(null), [provenance, setProvenance] = useState<unknown>(null)
  const [dark, setDark] = useState(() => loadPreference('theme', matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') === 'dark')
  const [dock, setDock] = useState(() => loadPreference('resultsDock', 'bottom') === 'right' ? 'right' : 'bottom')
  const [sidebar, setSidebar] = useState(() => loadPreference('sidebar', 'true') === 'true'), [bottom, setBottom] = useState(true), [tab, setTab] = useState('overview')
  const [configOpen, setConfigOpen] = useState(false), [configTab, setConfigTab] = useState('inputs'), [migration, setMigration] = useState<{ discovery: Discovery; values: Drafts; changes: string[]; settings?: Record<string, Value | null> } | null>(null)
  const [diskMatch, setDiskMatch] = useState<{ runId: string; matches: boolean | null } | null>(null)
  const [dataValid, setDataValid] = useState(true)
  const [confirmedSchema, setConfirmedSchema] = useState('')
  const [runAfterReview, setRunAfterReview] = useState(false)
  const [clusterOffset, setClusterOffset] = useState(0)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({}), [pick, setPick] = useState<InputSpec | null>(null), [selection, setSelection] = useState<ChartSelection | null>(null), [selectedFill, setSelectedFill] = useState<string>()
  const [signals, setSignals] = useState(true), [trades, setTrades] = useState(true), [conflictOpen, setConflictOpen] = useState(false)
  const [exportOpen, setExportOpen] = useState(false), [exportOptions, setExportOptions] = useState({ source: false, data: false, logs: false })
  const [presetName, setPresetName] = useState('default'), [presets, setPresets] = useState<{ id: string; value: Preset }[]>([]), [profiles, setProfiles] = useState<{ id: string; value: DataProfile }[]>([])
  const upload = useRef<HTMLInputElement>(null), buffersRef = useRef(buffers), latest = useRef(new LatestRequest()), resultLatest = useRef(new LatestRequest())
  const viewportTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  useEffect(() => { const requests = latest.current; return () => { clearTimeout(viewportTimer.current); requests.close() } }, [selected])
  const pendingRef = useRef(''), chartCache = useRef(new BoundedCache<ChartResponse>())
  useEffect(() => { buffersRef.current = buffers }, [buffers])
  useEffect(() => { if (!pick) return; const exit = (event: KeyboardEvent) => { if (event.key === 'Escape') { setPick(null); setConfigOpen(true) } }; window.addEventListener('keydown', exit); return () => window.removeEventListener('keydown', exit) }, [pick])
  const cluster = selection?.cluster
  const clusterResource = useSavedResource<{ rows: { kind: string; value: Record<string, unknown> }[]; total: number; offset: number }>(cluster ? `/runs/${selected}/events?start=${cluster.start}&end=${cluster.end}&offset=${clusterOffset}` : null)
  const clusterPage = clusterResource.value
  const normalizedFileQuery = fileQuery.trim().toLowerCase()
  const visibleFiles = files.filter(name => name.toLowerCase().includes(normalizedFileQuery))
  const buffer = buffers[path], schema = discovery?.description
  const propertiesValid = !schema || Object.keys(settingErrors(schema, settings)).length === 0
  const selectedRun = runs.find(run => run.id === selected), pendingRun = runs.find(run => run.id === pending)
  const selectedStatus = selectedRun?.status
  const displayedChartError = selectedStatus && selectedStatus !== 'succeeded' ? `Run ${selectedStatus}; no completed chart` : chartError
  const displayedReportError = selectedStatus && selectedStatus !== 'succeeded' ? `Run ${selectedStatus}; no completed report` : reportError
  const displayedLogs = selectedRun && selectedStatus !== 'succeeded' ? { runId: selectedRun.id, error: selectedRun.error, stdout: selectedRun.stdout, stderr: selectedRun.stderr, logsIncomplete: (selectedRun as Run & { logsIncomplete?: boolean }).logsIncomplete } : logs
  const currentIdentity = buffer ? configurationIdentity(path, buffer.disk.revision, values, settings, data) : ''
  const expectedIdentity = (selectedRun?.request ? configurationIdentity(selectedRun.request.source.path, selectedRun.request.source.revision, selectedRun.request.inputs.values, selectedRun.request.settings, selectedRun.request.data) : '')
  const outOfDate = !!selected && !selectedRun?.imported && (diskMatch?.runId === selected && diskMatch.matches === false || !!buffer && dirty(buffer) || !!buffer && !!expectedIdentity && currentIdentity !== expectedIdentity || !!discovery && !!selectedRun?.sourceHash && selectedRun.sourceHash !== discovery.sourceHash)
  const retrySavedResult = () => { setReportError(''); setChartError(''); setResultAttempt(value => value + 1) }
  const runAction = async (label: string, action: () => Promise<void>) => { const id = ++actionSequence.current; actions.current.set(id, label); setBusy(label); setError(''); try { await action() } catch (failure) { setError(message(failure) + (failure instanceof ApiError && Object.keys(failure.fields).length ? '\n' + json(failure.fields) : '') + (failure instanceof ApiError && failure.details.frames ? '\nSnapshot locations:\n' + json(failure.details.frames) : '')) } finally { actions.current.delete(id); setBusy([...actions.current.values()].at(-1) ?? '') } }
  const selectRun = useCallback((id: string) => {
    if (selectedId.current === id) { setLogs(resultCache.current.get(id, 'logs') ?? null); return }
    selectedId.current = id
    setReportError(''); setWindowError(''); setChartLoading(false); lastWindow.current = null
    latest.current.close(); resultLatest.current.close()
    setSelected(id); setReport(resultCache.current.get(id, 'summary') as Report ?? null); setChart(resultCache.current.get(id, 'chart') as ChartResponse ?? null); setLogs(resultCache.current.get(id, 'logs') ?? null); setProvenance(resultCache.current.get(id, 'provenance') ?? null); setSelection(null); setSelectedFill(undefined); setChartError('')
  }, [setSelection, setSelectedFill])
  const refresh = useCallback(async () => {
    const result = await api.request<{ runs: Run[] }>('/runs'); setRuns(result.runs)
    const completed = result.runs.find(run => run.id === pendingRef.current && !activeStatus(run))
    if (completed) {
      if (completed.status === 'succeeded') { selectRun(completed.id); setTab('overview') }
      else { setError(`Run ${completed.id.slice(0, 8)} ${completed.status}: ${json(completed.error ?? '')}`); const fields = (completed.error as { fieldErrors?: Record<string, string[]> } | undefined)?.fieldErrors; if (fields) setFormErrors(Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, value.join('; ')]))) }
      pendingRef.current = ''; setPending('')
    }
    return result.runs
  }, [selectRun, setTab, setFormErrors])
  useEffect(() => {
    let disposed = false
    const token = new URLSearchParams(location.hash.slice(1)).get('token') ?? undefined
    void api.connect(token).then(async () => {
      if (disposed) return
      history.replaceState(null, '', location.pathname + location.search)
      let capabilities = await api.request<Capabilities>('/capabilities')
      if (disposed) return
      api.workspaceId = capabilities.workspaceId ?? ''
      const remembered = loadPreference('workspace', '')
      if (capabilities.mode !== 'view' && !capabilities.workspace && remembered) {
        try { capabilities = await api.request<Capabilities>('/workspace', { method: 'PUT', body: JSON.stringify({ path: remembered }) }); api.workspaceId = capabilities.workspaceId }
        catch (failure) { if (!disposed) setError('The remembered workspace is unavailable. Choose a directory. ' + message(failure)) }
      }
      if (disposed) return
      setCap(capabilities)
      if (capabilities.mode !== 'view' && !capabilities.workspace) { setWorkspacePicker(true); return }
      if (capabilities.capabilities.edit) setFiles((await api.request<{ files: string[] }>('/files')).files)
      const result = await refresh()
      if (!disposed) selectRun(result.find(run => run.status === 'succeeded')?.id ?? '')
    }).catch(failure => { if (!disposed) setError(message(failure)) })
    return () => { disposed = true }
  }, [refresh, selectRun])
  useEffect(() => { document.documentElement.classList.toggle('dark', dark); savePreference('theme', dark ? 'dark' : 'light') }, [dark])
  useEffect(() => { savePreference('sidebar', String(sidebar)) }, [sidebar])
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => { if (Object.values(buffers).some(dirty)) event.preventDefault() }
    window.addEventListener('beforeunload', prevent); return () => window.removeEventListener('beforeunload', prevent)
  }, [buffers])
  useEffect(() => {
    if (!cap || cap.mode !== 'view' && !cap.workspace) return
    let disposed = false, refreshing = false
    const tick = async () => {
      if (refreshing) return
      refreshing = true
      try {
        if (disposed) return
        await refresh()
        if (disposed) return
        if (cap.capabilities.edit) {
          const revisions = Object.entries(buffersRef.current).map(([name, buffer]) => [name, buffer.disk.revision] as const)
          const next = await api.request<{ files: string[] }>('/files'); if (!disposed) setFiles(next.files)
          for (const [name, revision] of revisions) {
            const file = next.files.includes(name) ? await api.request<DiskFile>('/file?path=' + encodeURIComponent(name)) : null
            if (!disposed) setBuffers(previous => previous[name]?.disk.revision === revision ? { ...previous, [name]: external(previous[name], file) } : previous)
          }
        }
      } catch (failure) { if (!disposed) setError(message(failure)) } finally { refreshing = false }
    }
    const timer = setInterval(() => void tick(), 2000)
    return () => { disposed = true; clearInterval(timer) }
  }, [cap, refresh])
  useEffect(() => {
    if (!selected || selectedStatus !== 'succeeded') return
    const request = resultLatest.current.start(selected)
    const load = <T,>(resource: string, apply: (value: T) => void, failed: (error: string) => void) => {
      const cached = resultCache.current.get(selected, resource)
      if (cached !== undefined) { apply(cached as T); return }
      void api.request<T>(`/runs/${selected}/${resource}`, { signal: AbortSignal.any([request.signal, AbortSignal.timeout(30000)]) }).then(value => {
        if (!resultLatest.current.current(request)) return
        if (resource === 'chart') decode((value as ChartResponse).plotting)
        resultCache.current.set(selected, resource, value); apply(value)
      }).catch(failure => { if (resultLatest.current.current(request)) failed(message(failure)) })
    }
    load<Report>('summary', setReport, setReportError)
    load<unknown>('provenance', setProvenance, () => {})
    load<unknown>('logs', setLogs, () => {})
    load<ChartResponse>('chart', setChart, setChartError)
    const guard = resultLatest.current
    return () => guard.close()
  }, [selected, selectedStatus, resultAttempt])
  useEffect(() => {
    if (!selected || !cap?.capabilities.edit || selectedRun?.imported) return
    const controller = new AbortController()
    const check = () => api.request<{ runId: string; matches: boolean | null }>(`/runs/${selected}/workspace-match`, { signal: controller.signal }).then(setDiskMatch).catch(() => {})
    void check(); const timer = setInterval(() => void check(), 5000)
    return () => { clearInterval(timer); controller.abort() }
  }, [selected, cap, selectedRun?.imported])
  useEffect(() => {
    if (!configOpen || !cap?.capabilities.edit) return
    void Promise.all([api.request<{ items: { id: string; value: Preset }[] }>('/presets'), api.request<{ items: { id: string; value: DataProfile }[] }>('/profiles')]).then(([a, b]) => { setPresets(a.items); setProfiles(b.items) }).catch(failure => setError(message(failure)))
  }, [configOpen, cap])
  const openFile = async (name: string) => {
    const selection = ++fileSelection.current
    try {
      if (!buffersRef.current[name]) {
        let read = fileReads.current.get(name)
        if (!read) { read = api.request<DiskFile>('/file?path=' + encodeURIComponent(name)); fileReads.current.set(name, read) }
        let file: DiskFile
        try { file = await read } finally { if (fileReads.current.get(name) === read) fileReads.current.delete(name) }
        setBuffers(previous => previous[name] ? previous : { ...previous, [name]: { disk: file, draft: file.content } })
      }
    } catch (failure) { if (selection === fileSelection.current) throw failure; return }
    if (selection !== fileSelection.current) return
    setPath(name); setTab('editor'); setBottom(true); setDiscovery(null); setValues({}); setSettings({})
  }
  const saveBuffer = async (current: Buffer) => {
    if (current.conflict) throw Error('Resolve the file conflict before saving')
    const submitted = current.draft
    try {
      const file = await api.request<DiskFile>('/file', { method: 'PUT', body: JSON.stringify({ path: current.disk.path, baseRevision: current.disk.revision, content: submitted }) })
      setBuffers(previous => ({ ...previous, [file.path]: saved(previous[file.path] ?? current, file, submitted) })); return file
    } catch (failure) {
      if (failure instanceof ApiError && failure.code === 'FileConflict') {
        const disk = await api.request<DiskFile>('/file?path=' + encodeURIComponent(current.disk.path))
        setBuffers(previous => ({ ...previous, [disk.path]: { ...previous[disk.path], conflict: disk } })); setConflictOpen(true)
      }
      throw failure
    }
  }
  const source = (file: DiskFile) => ({ path: file.path, revision: file.revision, roots: sourceRoots.split(',').map(value => value.trim()).filter(Boolean), resources: sourceResources.split(',').map(value => value.trim()).filter(Boolean) })
  const discover = (file: DiskFile) => api.request<Discovery>('/discover', { method: 'POST', body: JSON.stringify(source(file)) })
  const discoverCurrent = async () => {
    setRunAfterReview(false)
    if (!buffer) return
    if (dirty(buffer) || buffer.conflict) throw Error('Save the strategy and resolve conflicts before discovering parameters')
    const found = await discover(buffer.disk)
    if (schema && schema.schemaHash !== found.description.schemaHash) { const next = migrate(schema, found.description, values); setMigration({ discovery: found, values: next.proposed, changes: next.changes }); return }
    setDiscovery(found); if (!schema) setValues(defaults(found.description)); setConfigOpen(true)
  }
  const submit = async (reviewedValues?: Drafts) => {
    if (!buffer) return
    if (!propertiesValid) throw Error('Correct the execution properties before running')
    if (data.kind === 'loader' && !dataValid || !validDataNumbers(data)) throw Error('Correct the data profile fields before running')
    if (!reviewedValues && schema?.inputs.some(input => input.confirm) && confirmedSchema !== schema.schemaHash) { setRunAfterReview(true); setConfigOpen(true); return }
    try {
      const ready = await prepareRun({ buffer, schema, values: reviewedValues ?? values, save: saveBuffer, discover })
      setDiscovery(ready.discovery)
      const run = await api.request<Run>('/runs', { method: 'POST', body: JSON.stringify({ source: source(ready.file), inputs: ready.inputs, settings, data, idempotencyKey: crypto.randomUUID(), parentRunId: selected || null }) })
      pendingRef.current = run.id
      setValues(ready.inputs.values); setPending(run.id); await refresh()
    } catch (failure) {
      if (failure instanceof ReviewRequired) {
        setRunAfterReview(true)
        if (!schema) { setDiscovery(failure.discovery); setValues(failure.values); setFormErrors({}); setConfigTab('inputs'); setConfigOpen(true) }
        else setMigration({ discovery: failure.discovery, values: failure.values, changes: failure.changes })
        return
      }
      throw failure
    }
  }
  const loadChart = async (start: number, fill?: string, end?: number) => {
    clearTimeout(viewportTimer.current)
    if (!Number.isSafeInteger(start) || start < 0 || end !== undefined && !Number.isSafeInteger(end)) { setError('The selected event has no valid chart bar'); return }
    const request = latest.current.start(selected), key = `${start}:${end ?? ''}`
    lastWindow.current = { runId: selected, start, fill, end }; setWindowError('')
    const cached = chartCache.current.get(selected, key)
    if (cached) { setChart(cached); setSelectedFill(fill); setChartLoading(false); return }
    setChartLoading(true)
    try {
      const value = await api.request<ChartResponse>(`/runs/${selected}/chart?start=${start}${end === undefined ? '' : '&end=' + end}`, { signal: AbortSignal.any([request.signal, AbortSignal.timeout(30000)]) })
      if (latest.current.current(request)) { decode(value.plotting); chartCache.current.set(selected, key, value); setChart(value); setSelectedFill(fill) }
    } catch (failure) { if (latest.current.current(request)) setWindowError(message(failure)) }
    finally { if (latest.current.current(request)) setChartLoading(false) }
  }
  const selectChart = (value: ChartSelection) => {
    if (pick) {
      try {
        if (!schema) return
        const next = pickedValues(schema, pick, value)
        setValues(previous => ({ ...previous, ...next })); setError(''); setPick(null); setConfigOpen(true)
      } catch (failure) { setError(message(failure)) }
    } else { setSelection(value); setClusterOffset(0) }
  }
  const exportRun = async () => {
    const blob = await api.download(`/runs/${selected}/export?${new URLSearchParams(Object.entries(exportOptions).map(([key, value]) => [key, String(value)]))}`)
    const url = URL.createObjectURL(blob), anchor = document.createElement('a'); anchor.href = url; anchor.download = `${selected}.obstudio`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setExportOpen(false)
  }
  const importFile = async (file: File) => { const run = await api.request<Run>('/imports', { method: 'POST', body: file, headers: { 'Content-Type': file.name.endsWith('.json') ? 'application/json' : 'application/octet-stream' } }); await refresh(); selectRun(run.id) }
  const applyConfiguration = () => {
    if (!schema || !propertiesValid) return
    const checked = validateInputs(schema, values)
    setFormErrors(checked.errors)
    if (Object.keys(checked.errors).length) { setConfigTab('inputs'); return }
    setValues(checked.values); setConfirmedSchema(schema.schemaHash); setConfigOpen(false); setRunAfterReview(false)
    if (runAfterReview) void runAction('Preparing run', () => submit(checked.values))
  }
  return <TooltipProvider><div className="flex h-dvh min-h-96 flex-col overflow-hidden bg-background text-xs text-foreground">
    <header className="flex h-12 shrink-0 items-center gap-2 border-b px-3">
      <Button variant="ghost" size="icon-sm" aria-label="Toggle file sidebar" onClick={() => setSidebar(!sidebar)}><PanelLeft /></Button>
      <Brand />
      <span className="min-w-0 truncate font-mono text-[11px] text-muted-foreground">{path || (cap?.mode === 'view' ? 'Read-only report' : 'Select a strategy')}</span>
      {buffer && dirty(buffer) && <Badge variant="outline">Unsaved</Badge>}
      <div className="ml-auto flex shrink-0 items-center gap-1">
        {cap?.capabilities.edit && <><Button variant="ghost" size="icon-sm" disabled={!buffer || !!busy || !dirty(buffer) || !!buffer.conflict} aria-label="Save strategy" onClick={() => void runAction('Saving', async () => { if (buffer) await saveBuffer(buffer) })}><Save /></Button><Button variant="ghost" size="icon-sm" aria-label="Strategy settings" disabled={!buffer || !!busy} onClick={() => void runAction('Discovering', discoverCurrent)}><Settings2 /></Button><Button size="sm" disabled={!buffer || !!busy || optimizerActive || !cap.capabilities.discover || !!buffer.conflict} onClick={() => void runAction('Preparing run', submit)}><Play className="size-3" /><span className="hidden sm:inline">{buffer && dirty(buffer) ? 'Save & Run' : 'Run'}</span></Button></>}
        <Button variant="ghost" size="icon-sm" aria-label="Toggle color theme" onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button>
        {cap?.capabilities.edit && <><Input ref={upload} type="file" accept=".obstudio,.json" className="hidden" aria-label="Import report file" onChange={event => { const file = event.target.files?.[0]; if (file) void runAction('Importing', () => importFile(file)); event.target.value = '' }} /><Button variant="ghost" size="icon-sm" aria-label="Import result" onClick={() => upload.current?.click()}><Upload /></Button></>}
        <Button variant="ghost" size="icon-sm" aria-label="Export result" disabled={!report} onClick={() => setExportOpen(true)}><Download /></Button>
      </div>
    </header>
    {error && <div role="alert" className="flex max-h-32 shrink-0 items-start gap-3 overflow-auto border-b border-destructive/30 bg-destructive/10 px-4 py-2 text-destructive"><pre className="min-w-0 flex-1 whitespace-pre-wrap font-sans">{error}</pre><Button variant="ghost" size="icon-xs" aria-label="Dismiss error" onClick={() => setError('')}><X /></Button></div>}
    {!cap && <div className="grid flex-1 place-content-center text-muted-foreground">{error ? 'Launch Studio again to establish a local session.' : 'Connecting to the local workspace…'}</div>}
    {cap && <div className="flex min-h-0 flex-1">
      {sidebar && <aside className="flex w-52 shrink-0 flex-col border-r bg-card max-sm:absolute max-sm:inset-y-12 max-sm:left-0 max-sm:z-20 max-sm:shadow-xl" aria-label="Workspace files and run history">
        <div className="shrink-0 border-b px-3 py-2">
          <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{cap.mode === 'view' ? 'Imported report' : 'Workspace'}{cap.mode !== 'view' && <Button variant="ghost" size="icon-xs" aria-label="Choose workspace directory" title={Object.values(buffers).some(dirty) ? 'Save file changes before switching directories' : 'Choose workspace directory'} disabled={optimizerActive || !!busy || Object.values(buffers).some(dirty) || runs.some(activeStatus)} onClick={() => setWorkspacePicker(true)}><FolderOpen className="size-3.5" /></Button>}</div>
          {cap.workspace && <p className="truncate pt-1 text-[10px] text-muted-foreground" title={cap.workspace}>{cap.workspace}</p>}
        </div>
        {!cap.workspace && cap.mode !== 'view' && <div className="p-3 text-muted-foreground">Choose a directory to load your strategy files.<Button variant="outline" className="mt-3 w-full" onClick={() => setWorkspacePicker(true)}>Choose directory</Button></div>}
        {cap.capabilities.edit && <>
          <div className="shrink-0 border-b px-2 py-2">
            <div className="relative">
              <Search aria-hidden="true" className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input ref={fileSearch} aria-label="Search workspace files by name or path" placeholder="Search files…" value={fileQuery} onChange={event => setFileQuery(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); setFileQuery('') } }} className="h-8 rounded-md pl-7 pr-7 text-xs md:text-xs" autoComplete="off" spellCheck={false} />
              {fileQuery && <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 size-6 -translate-y-1/2" aria-label="Clear file search" onClick={() => { setFileQuery(''); fileSearch.current?.focus() }}><X className="size-3" /></Button>}
            </div>
            {normalizedFileQuery && <p role="status" className="px-1 pt-1.5 text-[10px] text-muted-foreground">{visibleFiles.length} of {files.length} files</p>}
          </div>
          <div className="min-h-20 flex-1 overflow-auto py-2">
            {visibleFiles.length === 0 && <p className="px-3 py-4 text-muted-foreground">{files.length === 0 ? 'No editable files found.' : 'No matching files.'}</p>}
            {visibleFiles.map(name => <Button key={name} variant={path === name ? 'secondary' : 'ghost'} size="sm" className="w-full justify-start rounded-none px-3 font-mono text-[10px]" title={name} onClick={() => void runAction('Reading file', () => openFile(name))}><FileCode2 className="size-3 shrink-0" /><span className="truncate">{name}</span>{buffers[name] && dirty(buffers[name]) && <span className="ml-auto text-primary">●</span>}</Button>)}
          </div>
        </>}
        <div className="border-y px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Runs <span className="float-right font-mono">{runs.length}</span></div>
        <div className="min-h-24 flex-1 overflow-auto py-1">{runs.length === 0 && <p className="p-3 text-muted-foreground">Your saved runs will appear here.</p>}{runs.map(run => <div key={run.id} className={`flex items-center gap-1 px-1 ${selected === run.id ? 'bg-secondary' : ''}`}><Button variant="ghost" className="h-auto min-w-0 flex-1 justify-start py-2 text-left" onClick={() => { selectRun(run.id); setTab(run.status === 'succeeded' ? 'overview' : 'logs'); setBottom(true) }}><span className="min-w-0"><span className="block truncate font-mono text-[10px]">{run.id.slice(0, 10)}</span><span className={`block text-[10px] ${run.status === 'failed' ? 'text-loss' : 'text-muted-foreground'}`}>{run.status}{run.phase && activeStatus(run) ? ` · ${run.phase}` : ''}</span></span></Button>{['queued', 'running'].includes(run.status) && <Button variant="ghost" size="icon-xs" aria-label={`Cancel run ${run.id}`} onClick={() => void runAction('Cancelling', async () => { await api.request(`/runs/${run.id}/cancel`, { method: 'POST' }); await refresh() })}><Square className="size-3" /></Button>}</div>)}</div>
        <div className="border-t p-3 text-[10px] text-muted-foreground" title={cap.interpreter.executable}>{cap.mode === 'view' ? 'Read-only · no source execution' : cap.interpreter.compatible ? 'Local Python connected' : cap.interpreter.message}</div>
      </aside>}
      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-9 shrink-0 items-center gap-2 overflow-x-auto border-b px-3">
          <span className="font-medium">{report ? String(report.context.instrument.symbol ?? 'Market') : data.instrument.symbol}</span><span className="text-muted-foreground">{selected ? `Run ${selected.slice(0, 8)}` : 'No run selected'}</span>{selectedRun?.request && cap.capabilities.discover && <Button variant="ghost" size="sm" disabled={!!busy} onClick={() => void runAction('Preparing snapshot rerun', async () => { const run = await api.request<Run>(`/runs/${selected}/rerun`, { method: 'POST' }); pendingRef.current = run.id; setPending(run.id); await refresh() })}>Rerun saved snapshot</Button>}{outOfDate && <Badge variant="outline" className="text-amber-500">Out of date</Badge>}
          <div className="ml-auto flex items-center gap-3 whitespace-nowrap"><Label className="text-[10px]"><Checkbox disabled={!chart} checked={signals} onCheckedChange={value => setSignals(value === true)} />Signals</Label><Label className="text-[10px]"><Checkbox disabled={!chart} checked={trades} onCheckedChange={value => setTrades(value === true)} />Fills</Label>{selectedFill && <Button variant="ghost" size="icon-xs" aria-label="Clear fill selection" onClick={() => setSelectedFill(undefined)}><X /></Button>}{chart && <><Button variant="ghost" size="sm" onClick={() => void loadChart(0, undefined, chart.window.total)}>All bars</Button><Button variant="ghost" size="sm" disabled={chart.window.start === 0} onClick={() => void loadChart(Math.max(0, chart.window.start - 5000))}>Earlier</Button><span className="font-mono text-[10px] text-muted-foreground">{chart.window.start + 1}–{chart.window.end} / {chart.window.total}{chart.window.granularity > 1 ? ` · aggregated ×${chart.window.granularity}` : ''}</span><Button variant="ghost" size="sm" disabled={chart.window.end >= chart.window.total} onClick={() => void loadChart(chart.window.end)}>Later</Button></>}</div>
        </div>
        {chartLoading && <p role="status" className="border-b px-3 py-1 text-muted-foreground">Loading chart window…</p>}
        {windowError && <div role="alert" className="flex items-center gap-2 border-b px-3 py-2 text-destructive"><span>{windowError}</span><Button variant="outline" size="sm" onClick={() => { const request = lastWindow.current; if (request?.runId === selected) void loadChart(request.start, request.fill, request.end) }}>Retry chart window</Button></div>}
        {pick && <div className="flex items-center gap-2 border-b bg-primary/10 px-3 py-2 text-primary">Click the chart to set {pick.title} ({pick.kind}).<Button variant="ghost" size="sm" onClick={() => { setPick(null); setConfigOpen(true) }}>Cancel pick</Button></div>}
        <ResizablePanelGroup orientation={dock === 'right' ? 'horizontal' : 'vertical'} className="min-h-0 min-w-0 flex-1" defaultLayout={parseLayout(loadPreference('layout', ''))} onLayoutChanged={layout => { if (layout.chart >= 18 && layout.bottom >= 15) savePreference('layout', JSON.stringify(layout)) }}>
          <ResizablePanel id="chart" defaultSize="58%" minSize="18%"><div className="relative h-full">{chart ? <ChartBoundary key={selected + String(chart.window.start) + String(chart.window.end)}><MarketChart key={selected} data={chart.plotting} dark={dark} selectedFill={selectedFill} showSignals={signals} showTrades={trades} onSelect={selectChart} onViewport={range => { if (chart.window.granularity <= 1 || range.to - range.from > 4500) return; clearTimeout(viewportTimer.current); viewportTimer.current = setTimeout(() => void loadChart(Math.max(0, Math.floor(range.from)), undefined, Math.min(chart.window.total, Math.ceil(range.to) + 1)), 150) }} /></ChartBoundary> : <div className="grid h-full place-content-center px-6 text-center"><Activity className="mx-auto mb-4 size-8 text-muted-foreground/40" /><h2 className="text-sm font-medium">{displayedChartError ? 'Chart unavailable' : selected ? 'Loading result' : 'Your strategy, on the chart'}</h2><p className="mt-2 max-w-md text-xs text-muted-foreground">{displayedChartError || (selected ? 'The report and chart load independently.' : 'Choose a Python strategy, review its parameters and data, then run a backtest.')}</p>{displayedChartError && selectedStatus === 'succeeded' && <Button variant="outline" className="mt-3" onClick={retrySavedResult}>Retry chart</Button>}</div>}</div></ResizablePanel>
          {bottom && <><ResizableHandle withHandle aria-label="Resize chart and results" /><ResizablePanel id="bottom" defaultSize="42%" minSize="15%"><div className="@container flex h-full min-w-0 flex-col" aria-label="Backtest results panel"><div className="flex shrink-0 items-center border-b"><Tabs value={tab} onValueChange={value => { setTab(value); if (value === 'optimizer') setOptimizerMounted(true) }} className="min-w-0 flex-1 overflow-auto"><TabsList variant="line" className="h-9 justify-start rounded-none px-2">{[['overview', 'Overview'], ['performance', 'Performance'], ['trades', 'List of trades'], ['settings', 'Settings & Data'], ...(cap.capabilities.edit ? [['editor', 'Code'], ['optimizer', 'Optimizer']] : []), ['logs', 'Logs']].map(([id, title]) => <TabsTrigger key={id} value={id} className="text-[11px]">{title}</TabsTrigger>)}</TabsList></Tabs><Button variant="ghost" size="icon-xs" className="shrink-0" aria-label={dock === 'bottom' ? 'Move results to right' : 'Move results to bottom'} title={dock === 'bottom' ? 'Move results to right' : 'Move results to bottom'} onClick={() => { const next = dock === 'bottom' ? 'right' : 'bottom'; setDock(next); savePreference('resultsDock', next) }}>{dock === 'bottom' ? <PanelRight /> : <PanelBottom />}</Button><Button variant="ghost" size="icon-xs" className="shrink-0" aria-label="Collapse results panel" onClick={() => setBottom(false)}><ChevronDown /></Button></div>
            <div className="min-h-0 flex-1 overflow-auto">{optimizerMounted && cap.capabilities.edit && <div className={tab === 'optimizer' ? 'min-h-full' : 'hidden'}><OptimizerPanel key={cap.workspaceId} schema={schema} values={values} canPrepare={!!buffer && cap.capabilities.discover && !busy && !runs.some(activeStatus)} onConfigure={() => void runAction('Discovering strategy', discoverCurrent)} onActive={setOptimizerActive} onPrepare={async (search, constraint) => {
              if (!buffer || !propertiesValid || !validDataNumbers(data) || data.kind === 'loader' && !dataValid) throw Error('Review the strategy, execution settings and data before optimizing')
              if (actions.current.size) throw Error('Wait for the current action to finish')
              const actionId = ++actionSequence.current; actions.current.set(actionId, 'Preparing experiment'); setBusy('Preparing experiment')
              try {
                const ready = await prepareRun({ buffer, schema, values, save: saveBuffer, discover })
                setDiscovery(ready.discovery)
                return await api.request('/optimizations', { method: 'POST', body: JSON.stringify({ run: { source: source(ready.file), inputs: ready.inputs, settings, data, idempotencyKey: crypto.randomUUID() }, search, constraint }) })
              } catch (failure) {
                if (failure instanceof ReviewRequired) { setMigration({ discovery: failure.discovery, values: failure.values, changes: failure.changes }); setRunAfterReview(false) }
                throw failure
              } finally { actions.current.delete(actionId); setBusy([...actions.current.values()].at(-1) ?? '') }
            }} onOpenReport={async id => { await refresh(); selectRun(id); setTab('overview') }} onApply={(next, schemaHash, nextSettings) => {
              if (!schema || schema.schemaHash !== schemaHash) throw Error('Select the original strategy and rediscover its inputs before applying this trial')
              const checked = validateInputs(schema, next)
              if (Object.keys(checked.errors).length) throw Error('Trial inputs do not match the current strategy')
              setValues(checked.values); setSettings(nextSettings); setRunAfterReview(false); setConfigOpen(true)
            }} /></div>}{tab === 'optimizer' ? null : tab === 'editor' ? buffer ? <div className="flex h-full flex-col">{buffer.conflict && <div className="flex items-center gap-2 border-b bg-amber-500/10 px-3 py-2">{buffer.conflict === 'deleted' ? 'File deleted externally. Your draft is preserved; saving is disabled.' : 'The disk file changed. Resolve differences before saving.'}<Button variant="outline" size="sm" disabled={buffer.conflict === 'deleted'} onClick={() => setConflictOpen(true)}>Review conflict</Button></div>}<div className="flex-1"><Suspense fallback={<p className="p-4">Loading local editor…</p>}><CodeEditor path={path} value={buffer.draft} dark={dark} onChange={draft => setBuffers(previous => ({ ...previous, [path]: { ...previous[path], draft } }))} onSave={() => { const current = buffersRef.current[path]; if (current && !current.conflict && !actions.current.size) void runAction('Saving', async () => { await saveBuffer(current) }) }} /></Suspense></div></div> : <p className="p-6 text-muted-foreground">Select a file from the workspace.</p> : tab === 'logs' ? <LogPanel key={selected} value={displayedLogs} runId={selected} dark={dark} timezone={String(report?.context.timezone ?? 'UTC')} onBar={chart ? bar => { void loadChart(Math.max(0, bar - 100), undefined, Math.min(chart.window.total, bar + 101)) } : undefined} /> : report ? <><ReportView key={selected} runId={selected} report={report} dark={dark} tab={tab} onFill={(id, bar) => { if (chart && bar >= chart.window.start && bar < chart.window.end) setSelectedFill(id); else void loadChart(Math.max(0, bar - 2500), id) }} />{tab === 'settings' && <section className="m-4 border p-3"><h3 className="font-medium">Artifact provenance and available resources</h3><pre className="mt-3 overflow-auto whitespace-pre-wrap font-mono text-[10px]">{json(provenance)}</pre></section>}</> : <p className="p-6 text-muted-foreground">{displayedReportError ? `Report unavailable: ${displayedReportError}` : selected ? 'Loading saved report…' : busy || 'Run a strategy or import a report to inspect its results.'}{displayedReportError && selectedStatus === 'succeeded' && <Button variant="outline" className="ml-3" onClick={retrySavedResult}>Retry saved report</Button>}</p>}</div>
          </div></ResizablePanel></>}
        </ResizablePanelGroup>
        {!bottom && <Button variant="ghost" className="h-8 shrink-0 justify-start rounded-none border-t text-xs" onClick={() => setBottom(true)}><ChevronUp />Show results & code</Button>}
      </main>
    </div>}
    <footer className="flex h-6 shrink-0 items-center gap-3 border-t px-3 text-[10px] text-muted-foreground"><span className={`size-1.5 rounded-full ${busy || pendingRun ? 'bg-amber-400' : 'bg-profit'}`} /><span>{busy || (pendingRun ? `${pendingRun.status} · ${pendingRun.phase ?? 'waiting'} · ${Math.max(0, Math.floor(now / 1000 - (pendingRun.startedAt ?? pendingRun.createdAt ?? now / 1000)))}s` : 'Ready')}</span><span className="ml-auto hidden sm:inline">{cap?.mode === 'view' ? 'Read-only report · no source execution' : 'Local workspace · Python executes with your permissions'}</span><a className="hover:text-primary" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Charts by TradingView</a></footer>
    {workspacePicker && cap?.mode !== 'view' && cap && <WorkspacePicker open={workspacePicker} initialPath={cap.workspace ?? loadPreference('workspace', cap.suggestedWorkspace)} onOpenChange={setWorkspacePicker} onSelect={async directory => {
      const next = await api.request<Capabilities>('/workspace', { method: 'PUT', body: JSON.stringify({ path: directory }) })
      savePreference('workspace', next.workspace ?? directory)
      window.location.reload()
    }} />}
    <Dialog open={configOpen} onOpenChange={open => { setConfigOpen(open); if (!open) setRunAfterReview(false) }}><DialogContent className="flex max-h-[90dvh] flex-col sm:max-w-2xl"><DialogHeader><DialogTitle>Strategy settings</DialogTitle><DialogDescription>{runAfterReview ? 'Review inputs, execution properties and data, then apply and run the backtest.' : 'Changes configure the next run. Python source defaults stay unchanged.'}</DialogDescription></DialogHeader><Tabs value={configTab} onValueChange={setConfigTab} className="min-h-0 flex-1"><TabsList className="w-full"><TabsTrigger value="inputs">Inputs</TabsTrigger><TabsTrigger value="properties">Properties</TabsTrigger><TabsTrigger value="data">Data</TabsTrigger><TabsTrigger value="source">Source</TabsTrigger></TabsList><div className="max-h-[57dvh] overflow-auto px-1 py-4"><TabsContent value="inputs">{schema ? <ParameterForm schema={schema} values={values} errors={formErrors} onChange={(title, value) => setValues(previous => ({ ...previous, [title]: value }))} onPick={input => { if (!chart) { setError('Run or import a compatible chart before picking a value'); return }; setPick(input); setConfigOpen(false) }} /> : <p>Discover a saved strategy to configure its inputs.</p>}</TabsContent><TabsContent value="properties" forceMount className="data-[state=inactive]:hidden">{schema && <SettingsForm schema={schema} values={settings} onChange={setSettings} />}</TabsContent><TabsContent value="data" forceMount className="data-[state=inactive]:hidden"><DataForm key={data.name} value={data} onChange={setData} onValidity={setDataValid} /><div className="mt-4 flex gap-2"><Select onValueChange={id => { const profile = profiles.find(item => item.id === id); if (profile) { setData(profile.value); setDataValid(true) } }}><SelectTrigger className="flex-1" aria-label="Saved data profile"><SelectValue placeholder="Load data profile" /></SelectTrigger><SelectContent>{profiles.map(item => <SelectItem key={item.id} value={item.id}>{item.value.name}</SelectItem>)}</SelectContent></Select><Button variant="outline" disabled={!!busy || data.kind === 'loader' && !dataValid || !validDataNumbers(data)} onClick={() => void runAction('Saving data profile', async () => { await api.request(`/profiles/${encodeURIComponent(presetName)}`, { method: 'PUT', body: JSON.stringify({ ...data, name: presetName }) }); setProfiles((await api.request<{ items: { id: string; value: DataProfile }[] }>('/profiles')).items) })}>Save profile</Button></div></TabsContent><TabsContent value="source"><div className="space-y-4"><Label htmlFor="roots">Source roots (comma separated)</Label><Input id="roots" value={sourceRoots} onChange={event => setSourceRoots(event.target.value)} /><Label htmlFor="resources">Additional workspace resources</Label><Input id="resources" value={sourceResources} onChange={event => setSourceResources(event.target.value)} /><p className="text-muted-foreground">Python modules under these roots and declared resources are frozen before a run. External services and unlisted files cannot be reproduced by the snapshot.</p><p className="break-all font-mono text-[10px]">{cap?.interpreter.executable}</p></div></TabsContent></div></Tabs><div className="flex flex-wrap items-center gap-2 border-t pt-3"><Input className="w-28" value={presetName} onChange={event => setPresetName(event.target.value)} aria-label="Preset or data profile identifier" /><Select onValueChange={id => { const item = presets.find(preset => preset.id === id)?.value; if (!item || !schema || !discovery) return; if (item.inputs.schemaHash !== schema.schemaHash) { const checked = validateInputs(schema, item.inputs.values); setMigration({ discovery, values: { ...defaults(schema), ...checked.values }, changes: ['This preset belongs to another schema. Review retained values.', ...Object.entries(checked.errors).map(([key, value]) => `${key}: ${value}`)], settings: item.settings }) } else { setValues(item.inputs.values); setSettings(item.settings) } }}><SelectTrigger className="w-32" aria-label="Load preset"><SelectValue placeholder="Load preset" /></SelectTrigger><SelectContent>{presets.map(item => <SelectItem key={item.id} value={item.id}>{item.value.name}</SelectItem>)}</SelectContent></Select><Button variant="outline" size="sm" disabled={!schema || !propertiesValid || !!busy} onClick={() => void runAction('Saving preset', async () => { if (!schema) return; const checked = validateInputs(schema, values); setFormErrors(checked.errors); if (Object.keys(checked.errors).length) throw Error('Correct the input fields before saving'); await api.request(`/presets/${encodeURIComponent(presetName)}`, { method: 'PUT', body: JSON.stringify({ schemaVersion: 1, name: presetName, inputs: { schemaVersion: schema.schemaVersion, schemaHash: schema.schemaHash, values: checked.values }, settings }) }); setPresets((await api.request<{ items: { id: string; value: Preset }[] }>('/presets')).items) })}>Save preset</Button><Button variant="ghost" size="sm" disabled={!schema} onClick={() => { if (schema) setValues(defaults(schema)); setSettings({}); setFormErrors({}) }}><RefreshCw className="size-3" />Defaults</Button></div><DialogFooter><Button disabled={!schema || !propertiesValid || !!busy || data.kind === 'loader' && !dataValid || !validDataNumbers(data)} onClick={applyConfiguration}>{runAfterReview ? 'Apply & Run' : 'Apply to next run'}</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={!!migration} onOpenChange={open => { if (!open) { setMigration(null); setRunAfterReview(false) } }}><DialogContent><DialogHeader><DialogTitle>Review parameter schema</DialogTitle><DialogDescription>The strategy definition changed or has not been confirmed.</DialogDescription></DialogHeader><ul className="space-y-2 text-xs">{migration?.changes.map((change, index) => <li key={index}>{change}</li>)}</ul><DialogFooter><Button variant="outline" onClick={() => { setMigration(null); setRunAfterReview(false) }}>Cancel</Button><Button onClick={() => { if (migration) { setDiscovery(migration.discovery); setValues(migration.values); if (migration.settings) setSettings(migration.settings); setMigration(null); setConfigOpen(true) } }}>Review inputs</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={conflictOpen} onOpenChange={setConflictOpen}><DialogContent className="sm:max-w-5xl"><DialogHeader><DialogTitle>External file change</DialogTitle><DialogDescription>Left: current disk. Right: preserved editor draft. Review, then reload or use the current disk revision as the merge base.</DialogDescription></DialogHeader><div className="h-80">{buffer?.conflict && buffer.conflict !== 'deleted' && <Suspense fallback={<p>Loading diff…</p>}><CodeEditor path={path} value={buffer.draft} original={buffer.conflict.content} dark={dark} onChange={() => {}} onSave={() => {}} /></Suspense>}</div><DialogFooter><Button variant="outline" onClick={() => { if (buffer?.conflict && buffer.conflict !== 'deleted') { const disk = buffer.conflict; setBuffers(previous => ({ ...previous, [path]: { disk, draft: disk.content } })); setConflictOpen(false) } }}>Reload disk and discard draft</Button><Button onClick={() => { if (buffer?.conflict && buffer.conflict !== 'deleted') { setBuffers(previous => ({ ...previous, [path]: merge(buffer, buffer.draft) })); setConflictOpen(false); setTab('editor') } }}>Keep draft for manual merge</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={!!selection} onOpenChange={open => { if (!open) setSelection(null) }}><DialogContent><DialogHeader><DialogTitle>Bar {selection?.bar}</DialogTitle><DialogDescription>{selection?.label}</DialogDescription></DialogHeader><div className="max-h-80 space-y-3 overflow-auto">{selection?.cluster && <><p className="text-xs text-muted-foreground">Display cluster · {selection.cluster.fillCount} fills and {selection.cluster.signalCount} signals. Members retain their original bar and price.</p>{clusterResource.loading && <p role="status">Loading cluster members…</p>}{clusterResource.error && <div role="alert"><p>{clusterResource.error}</p><Button variant="outline" onClick={clusterResource.retry}>Retry cluster members</Button></div>}{clusterPage?.total === 0 && <p>No events in this cluster.</p>}{clusterPage?.rows.map((row, index) => <div key={index} className="border p-2"><pre className="overflow-auto text-[10px]">{json(row)}</pre>{row.kind === 'fill' && <Button variant="outline" size="sm" onClick={() => { void loadChart(Math.max(0, Number(row.value.bar_index) - 2500), String(row.value.fill_id)); setSelection(null) }}>Locate original fill</Button>}</div>)}<div className="flex gap-2"><Button variant="outline" size="sm" disabled={clusterResource.loading || !clusterOffset} onClick={() => setClusterOffset(Math.max(0, clusterOffset - 100))}>Previous members</Button><Button variant="outline" size="sm" disabled={clusterResource.loading || !clusterPage || clusterOffset + 100 >= clusterPage.total} onClick={() => setClusterOffset(clusterOffset + 100)}>Next members</Button></div></>}{selection?.fills.map(fill => <Button key={fill.fill_id} variant="outline" className="h-auto w-full justify-start whitespace-normal text-left" onClick={() => { setSelectedFill(fill.fill_id); setSelection(null); setTab('trades'); setBottom(true) }}><span><span className="block font-mono text-xs">{fill.fill_id}</span><span className="text-[11px] text-muted-foreground">{fill.side} {fill.qty} @ {fill.price} · fee {fill.fee} · {fill.phase}</span></span></Button>)}{selection?.markers.map(marker => <div key={marker.id} className="border p-3 text-xs"><span className="font-medium">Signal: {marker.text || marker.id}</span><p className="mt-1 text-muted-foreground">Anchored at bar {marker.anchorBar}; known at bar {marker.knownAtBar}</p><pre className="mt-2 overflow-auto">{json(marker)}</pre></div>)}{!selection?.cluster && !selection?.fills.length && !selection?.markers.length && <p className="text-muted-foreground">No fills or strategy markers at this bar.</p>}</div></DialogContent></Dialog>
    <Dialog open={exportOpen} onOpenChange={setExportOpen}><DialogContent><DialogHeader><DialogTitle>Export this run</DialogTitle><DialogDescription>The default archive contains the report, chart and provenance. Include private resources only when needed.</DialogDescription></DialogHeader>{(['source', 'data', 'logs'] as const).map(key => <Label key={key} className="py-1"><Checkbox checked={exportOptions[key]} onCheckedChange={value => setExportOptions(previous => ({ ...previous, [key]: value === true }))} />Include {key === 'source' ? 'Python source snapshot' : key === 'data' ? 'normalized data snapshot' : 'complete available logs'}</Label>)}<DialogFooter><Button disabled={!!busy} onClick={() => void runAction('Exporting', exportRun)}>Download .obstudio</Button></DialogFooter></DialogContent></Dialog>
  </div></TooltipProvider>
}
