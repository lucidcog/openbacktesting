export type ViewEvent = { kind: 'range'; from: number; to: number } | { kind: 'cursor'; bar: number | null }
/** Shared original bar identities, never sample indices; equal echoes cannot loop. */
export class ChartSync {
  private listeners = new Map<string, (event: ViewEvent) => void>()
  private dispatching = false
  private last = new Map<string, string>()
  private range: Extract<ViewEvent, { kind: 'range' }> | undefined
  subscribe(id: string, listener: (event: ViewEvent) => void, restoreRange = false) { this.listeners.set(id, listener); if (restoreRange && this.range) listener(this.range); return () => { this.listeners.delete(id) } }
  publish(source: string, event: ViewEvent) {
    if (this.dispatching) return
    const signature = JSON.stringify(event)
    if (this.last.get(event.kind) === signature) return
    this.last.set(event.kind, signature)
    if (event.kind === 'range') this.range = event
    this.dispatching = true
    try { for (const [id, listener] of this.listeners) if (id !== source) listener(event) } finally { this.dispatching = false }
  }
  reset() { this.last.clear(); this.range = undefined }
}
/** Library range notifications are deferred; only gestures may start a new sync. */
export function rangeInteraction(element: HTMLElement) {
  let active = false
  const begin = () => { active = true }
  element.addEventListener('pointerdown', begin)
  element.addEventListener('wheel', begin, { passive: true })
  return { active: () => active, suppress: () => { active = false }, dispose: () => { element.removeEventListener('pointerdown', begin); element.removeEventListener('wheel', begin) } }
}
export const chartSync = new ChartSync()
export function sampleAt<T extends { bar: number }>(points: T[], bar: number): T | undefined {
  let low = 0, high = points.length - 1, found: T | undefined
  while (low <= high) { const middle = (low + high) >> 1; if (points[middle].bar <= bar) { found = points[middle]; low = middle + 1 } else high = middle - 1 }
  return found
}
