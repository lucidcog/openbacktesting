import { it, expect } from 'vitest'
import { ChartSync, sampleAt } from './sync'
it('synchronizes original bars across sparse samples and stops recursive echoes', () => {
  const sync = new ChartSync(), seen: string[] = []
  sync.subscribe('market', event => { seen.push('market'); sync.publish('market', event) })
  const remove = sync.subscribe('equity', event => { seen.push('equity'); sync.publish('equity', event) })
  sync.publish('market', { kind: 'range', from: 10, to: 90 })
  expect(seen).toEqual(['equity'])
  sync.publish('equity', { kind: 'cursor', bar: 51 }); expect(seen).toEqual(['equity', 'market'])
  expect(sampleAt([{ bar: 1 }, { bar: 50 }, { bar: 90 }], 51)?.bar).toBe(50)
  remove(); sync.publish('market', { kind: 'cursor', bar: null }); expect(seen).toHaveLength(2)
})
