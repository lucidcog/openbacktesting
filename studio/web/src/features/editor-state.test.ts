import { expect, it } from 'vitest'
import { external, saved, merge, isSaveShortcut, type Buffer } from './editor-state'
const buffer: Buffer = { disk: { path: 'a.py', content: 'one', revision: '1' }, draft: 'draft' }
it('preserves dirty drafts, external versions and deletion state', () => {
  const disk = { ...buffer.disk, content: 'external', revision: '2' }
  expect(external(buffer, disk)).toEqual({ ...buffer, conflict: disk })
  expect(external(buffer, null).draft).toBe('draft')
  expect(merge(external(buffer, disk), 'merged').disk.revision).toBe('2')
  expect(external({ ...buffer, draft: 'one' }, disk).draft).toBe('external')
})
it('preserves edits made while a save was in flight and scopes shortcuts', () => {
  expect(saved(buffer, { ...buffer.disk, content: 'submitted', revision: '2' }, 'submitted').draft).toBe('draft')
  expect(isSaveShortcut({ key: 's', metaKey: true, ctrlKey: false }, false)).toBe(false)
  expect(isSaveShortcut({ key: 's', metaKey: true, ctrlKey: false }, true)).toBe(true)
})
it('clears conflicts when the original disk revision is restored without discarding the draft', () => {
  for (const conflict of ['deleted', { ...buffer.disk, content: 'external', revision: '2' }] as const) {
    expect(external({ ...buffer, conflict }, buffer.disk)).toEqual(buffer)
  }
})
