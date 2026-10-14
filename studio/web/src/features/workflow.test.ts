import { describe, it, expect, vi } from 'vitest'
import { prepareRun, ReviewRequired, LatestRequest, configurationIdentity } from './workflow'
import type { Description } from './inputs'
const schema: Description = { schemaVersion: '1.0.0', schemaHash: 'one', inputs: [], backtest: { settings: {} } }
const file = { path: 's.py', content: 'saved', revision: 'revision' }
describe('execution orchestration', () => {
  it('saves before discovering and prevents any run after a failure', async () => {
    const order: string[] = []
    const result = await prepareRun({ buffer: { disk: file, draft: 'new' }, schema, values: {}, save: async () => { order.push('save'); return { ...file, content: 'new' } }, discover: async saved => { order.push('discover'); expect(saved.content).toBe('new'); return { description: schema, sourceHash: 'snapshot', sourceFiles: {} } } })
    expect(order).toEqual(['save', 'discover']); expect(result.inputs.schemaHash).toBe('one')
    const discover = vi.fn()
    await expect(prepareRun({ buffer: { disk: file, draft: 'new' }, schema, values: {}, save: async () => { throw Error('conflict') }, discover })).rejects.toThrow('conflict')
    expect(discover).not.toHaveBeenCalled()
  })
  it('requires explicit review for changed or first schemas', async () => {
    await expect(prepareRun({ buffer: { disk: file, draft: file.content }, values: {}, save: vi.fn(), discover: async () => ({ description: schema, sourceHash: 's', sourceFiles: {} }) })).rejects.toBeInstanceOf(ReviewRequired)
  })
  it('isolates late responses and identities for edited inputs, code and data', () => {
    const latest = new LatestRequest(), old = latest.start('a'), current = latest.start('b')
    expect(latest.current(old)).toBe(false); expect(latest.current(current)).toBe(true); latest.close(); expect(latest.current(current)).toBe(false)
    const base = configurationIdentity('s.py', 'a', {}, {}, {})
    expect(configurationIdentity('s.py', 'b', {}, {}, {})).not.toBe(base)
    expect(configurationIdentity('s.py', 'a', { N: 1 }, {}, {})).not.toBe(base)
    expect(configurationIdentity('s.py', 'a', {}, {}, { path: 'new' })).not.toBe(base)
  })
})
