import { expect, it } from 'vitest'
import { PriceScale } from '../../../vendor/lightweight-charts/src/model/price-scale'
import { PriceRangeImpl } from '../../../vendor/lightweight-charts/src/model/price-range-impl'
import { ColorParser } from '../../../vendor/lightweight-charts/src/model/colors'
import { priceScaleOptionsDefaults } from '../../../vendor/lightweight-charts/src/api/options/price-scale-options-defaults'
import { layoutOptionsDefaults } from '../../../vendor/lightweight-charts/src/api/options/layout-options-defaults'

it.each([2, 20, 80, 200, 800])('marker autoscale preserves price direction in a %s px pane', height => {
  const scale = new PriceScale('right', { ...priceScaleOptionsDefaults }, layoutOptionsDefaults, { locale: 'en-US' }, new ColorParser([], new Map()))
  // Isolate the geometry with the same extra margins returned by marker autoscaling.
  Object.assign(scale, { _marginAbove: 60, _marginBelow: 45 })
  scale.setHeight(height); scale.setPriceRange(new PriceRangeImpl(90, 110))
  expect(scale.internalHeight()).toBeGreaterThan(1)
  expect(scale.priceToCoordinate(110, 100)).toBeLessThan(scale.priceToCoordinate(90, 100))
  expect(scale.coordinateToPrice(scale.priceToCoordinate(103, 100), 100)).toBeCloseTo(103)
  if (height === 800) expect(scale.internalHeight()).toBe(455)
  scale.applyOptions({ invertScale: true })
  expect(scale.priceToCoordinate(110, 100)).toBeGreaterThan(scale.priceToCoordinate(90, 100))
})
