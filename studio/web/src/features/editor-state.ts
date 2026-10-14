export interface DiskFile { path: string; content: string; revision: string }
export interface Buffer { disk: DiskFile; draft: string; conflict?: DiskFile | 'deleted' }
export const dirty = (buffer: Buffer) => buffer.draft !== buffer.disk.content
export function external(buffer: Buffer, file: DiskFile | null): Buffer {
  if (!file) return { ...buffer, conflict: 'deleted' }
  if (file.revision === buffer.disk.revision) return buffer.conflict ? { disk: file, draft: buffer.draft } : buffer
  return dirty(buffer) ? { ...buffer, conflict: file } : { disk: file, draft: file.content }
}
export function saved(buffer: Buffer, file: DiskFile, submitted: string): Buffer {
  return { disk: file, draft: buffer.draft === submitted ? file.content : buffer.draft }
}
export function merge(buffer: Buffer, merged: string): Buffer {
  if (!buffer.conflict || buffer.conflict === 'deleted') throw new Error('No disk version to merge')
  return { disk: buffer.conflict, draft: merged }
}
export function isSaveShortcut(event: { key: string; metaKey: boolean; ctrlKey: boolean }, editorFocused: boolean) {
  return editorFocused && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's'
}
export function stale(sourceHash: string | undefined, currentHash: string | undefined, changed: boolean) {
  return !!sourceHash && (changed || sourceHash !== currentHash)
}
