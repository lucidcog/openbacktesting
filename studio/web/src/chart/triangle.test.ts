import { expect, it } from 'vitest'
import { hitTestTriangle } from '../../../vendor/lightweight-charts/src/plugins/series-markers/series-markers-square'

it('hits the triangle instead of its bounding rectangle or an arrow shaft', () => {
  expect(hitTestTriangle(true, 0, 0, 20, 0, -8)).toBe(true)
  expect(hitTestTriangle(true, 0, 0, 20, 8, -8)).toBe(false)
  expect(hitTestTriangle(true, 0, 0, 20, 8, 8)).toBe(true)
  expect(hitTestTriangle(false, 0, 0, 20, 8, 8)).toBe(false)
  expect(hitTestTriangle(false, 0, 0, 20, 8, -8)).toBe(true)
})
