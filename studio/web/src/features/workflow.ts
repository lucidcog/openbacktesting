import { defaults, migrate, validateInputs, type Description, type Drafts } from './inputs'
import { dirty, type Buffer, type DiskFile } from './editor-state'
export interface Discovery { description: Description; sourceHash: string; sourceFiles: Record<string, string> }
export class ReviewRequired extends Error {
  constructor(public discovery: Discovery, public values: Drafts, public changes: string[]) { super('Review the updated strategy parameters before running') }
}
/** Stop on conflicts, failed discovery, changed schemas or invalid inputs. Never reuse an old description. */
export async function prepareRun(options: {
  buffer: Buffer; schema?: Description; values: Drafts;
  save: (buffer: Buffer) => Promise<DiskFile>; discover: (file: DiskFile) => Promise<Discovery>;
}) {
  if (options.buffer.conflict) throw new Error('Resolve the file conflict before running')
  const file = dirty(options.buffer) ? await options.save(options.buffer) : options.buffer.disk
  const discovery = await options.discover(file), schema = discovery.description
  if (!options.schema || options.schema.schemaHash !== schema.schemaHash) {
    const next = options.schema ? migrate(options.schema, schema, options.values) : { proposed: defaults(schema), changes: ['Review the discovered parameters and execution properties'] }
    throw new ReviewRequired(discovery, next.proposed, next.changes)
  }
  const result = validateInputs(schema, options.values)
  if (Object.keys(result.errors).length) throw new Error(Object.entries(result.errors).map(([key, error]) => `${key}: ${error}`).join('; '))
  return { file, discovery, inputs: { schemaVersion: schema.schemaVersion, schemaHash: schema.schemaHash, values: result.values } }
}
export function configurationIdentity(path: string, revision: string, values: Drafts, settings: object, data: object) {
  return JSON.stringify({ path, revision, values, settings, data })
}
/** Sequence tokens also isolate caches between runs and ignore responses after disposal. */
export class LatestRequest {
  private sequence = 0
  private controller?: AbortController
  start(runId: string) { this.controller?.abort(); this.controller = new AbortController(); return { runId, sequence: ++this.sequence, signal: this.controller.signal } }
  current(token: { sequence: number; signal: AbortSignal }) { return token.sequence === this.sequence && !token.signal.aborted }
  close() { this.controller?.abort(); this.sequence++ }
}
