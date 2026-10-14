import { useEffect, useState } from 'react'
import { api } from '@/protocol/client'

/** Tie values and failures to their request, even when a transport ignores abort. */
export function useSavedResource<T>(path: string | null) {
  const [attempt, setAttempt] = useState(0)
  const key = `${path}:${attempt}`
  const [state, setState] = useState<{ key: string; value?: T; error?: string } | null>(null)
  useEffect(() => {
    if (path === null) return
    let active = true
    const controller = new AbortController()
    void api.request<T>(path, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(30000)]) }).then(value => {
      if (active) setState({ key, value })
    }).catch(failure => { if (active) setState({ key, error: failure instanceof Error ? failure.message : String(failure) }) })
    return () => { active = false; controller.abort() }
  }, [path, key])
  const current = state?.key === key ? state : null
  return { value: current?.value ?? null, error: current?.error ?? '', loading: path !== null && current === null, retry: () => setAttempt(value => value + 1) }
}
