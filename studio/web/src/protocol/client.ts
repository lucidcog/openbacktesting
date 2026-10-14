import { requireProtocol } from './version'

export class ApiError extends Error {
  constructor(public code: string, message: string, public fields: Record<string, string[]> = {}, public details: Record<string, unknown> = {}) { super(message) }
}

export class StudioClient {
  private csrf = ''
  workspaceId = ''
  private connection?: Promise<void>
  connect(token?: string) {
    return this.connection ??= this.establish(token).catch(error => { this.connection = undefined; throw error })
  }
  private async establish(token?: string) {
    const session = await this.request<{ protocolVersion: number; csrf: string }>('/session', token ? { method: 'POST', body: JSON.stringify({ token }) } : {})
    requireProtocol(session.protocolVersion)
    this.csrf = session.csrf
  }
  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`/api/v1${path}`, {
      ...options, credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-Studio-Protocol': '1', 'X-Studio-CSRF': this.csrf, 'X-Studio-Workspace': this.workspaceId, ...options.headers },
    })
    const payload = await response.json()
    if (!response.ok) throw new ApiError(payload.code, payload.message, payload.fieldErrors, payload.details)
    return payload as T
  }
  async download(path: string): Promise<Blob> {
    const response = await fetch(`/api/v1${path}`, { credentials: 'same-origin', headers: { 'X-Studio-Protocol': '1', 'X-Studio-Workspace': this.workspaceId } })
    if (!response.ok) { const error = await response.json(); throw new ApiError(error.code, error.message) }
    return response.blob()
  }
}

export const api = new StudioClient()
