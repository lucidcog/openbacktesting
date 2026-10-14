import { describe, expect, it } from 'vitest'
import { requireProtocol } from './version'

describe('protocol compatibility', () => {
  it('accepts only the exact supported version', () => {
    expect(requireProtocol(1)).toBe(1)
    for (const version of [true, '1', 0, 2, null, undefined]) {
      expect(() => requireProtocol(version)).toThrow('Unsupported')
    }
  })
})
