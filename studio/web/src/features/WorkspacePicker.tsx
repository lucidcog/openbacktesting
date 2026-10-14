import { useEffect, useState } from 'react'
import { ArrowUp, Folder } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { api } from '@/protocol/client'

interface Directory { path: string; parent: string; directories: string[] }
export function WorkspacePicker({ open, initialPath, onOpenChange, onSelect }: {
  open: boolean; initialPath: string; onOpenChange: (open: boolean) => void; onSelect: (path: string) => Promise<void>;
}) {
  const [path, setPath] = useState(initialPath), [listing, setListing] = useState<Directory | null>(null)
  const [target, setTarget] = useState(initialPath), [error, setError] = useState(''), [loading, setLoading] = useState(true), [opening, setOpening] = useState(false)
  const [visit, setVisit] = useState(0)
  const navigate = (next: string) => { setLoading(true); setError(''); setTarget(next); setVisit(value => value + 1) }
  useEffect(() => {
    if (!open) return
    const controller = new AbortController()
    void api.request<Directory>('/directories?path=' + encodeURIComponent(target), { signal: controller.signal }).then(value => {
      if (!controller.signal.aborted) { setListing(value); setPath(value.path) }
    }).catch(failure => { if (!controller.signal.aborted) { setListing(null); setError(failure.message) } }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [open, target, visit])
  return <Dialog open={open} onOpenChange={value => { if (!opening) onOpenChange(value) }}><DialogContent className="sm:max-w-xl"><DialogHeader><DialogTitle>Choose workspace directory</DialogTitle><DialogDescription>Only this directory will be loaded. Remembered in this browser on this Studio address.</DialogDescription></DialogHeader>
    <form className="flex gap-2" onSubmit={event => { event.preventDefault(); navigate(path) }}><Input aria-label="Workspace directory path" value={path} onChange={event => setPath(event.target.value)} placeholder="/path/to/strategies" /><Button type="submit" variant="outline" disabled={loading || opening}>Browse</Button></form>
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
    <div className="h-64 overflow-auto rounded-md border p-1" aria-label="Workspace directories">
      {loading ? <p role="status" className="p-3 text-muted-foreground">Loading directories…</p> : listing && <>
        <Button variant="ghost" className="w-full justify-start" disabled={opening || listing.path === listing.parent} onClick={() => navigate(listing.parent)}><ArrowUp className="size-4" />Parent directory</Button>
        {listing.directories.map(name => <Button key={name} variant="ghost" className="w-full justify-start" disabled={opening} onClick={() => navigate(listing.path.replace(/\/$/, '') + '/' + name)}><Folder className="size-4 shrink-0" /><span className="truncate">{name}</span></Button>)}
        {!listing.directories.length && <p className="p-3 text-muted-foreground">No subdirectories. You can select this directory.</p>}
      </>}
    </div>
    <Button disabled={!path.trim() || loading || opening} onClick={() => { setOpening(true); setError(''); void onSelect(path.trim()).catch(failure => setError(failure.message)).finally(() => setOpening(false)) }}>{opening ? 'Opening workspace…' : 'Open directory'}</Button>
  </DialogContent></Dialog>
}
