import type { ChartOptionsImpl, HorzScaleItemConverterToInternalObj, IHorzScaleBehavior, InternalHorzScaleItem, InternalHorzScaleItemKey, TickMark, TickMarkWeightValue, TimeScalePoint } from 'lightweight-charts'
import { exactLabel, type Axis } from './model'

export class BarScale implements IHorzScaleBehavior<number> {
  private configuration!: ChartOptionsImpl<number>
  constructor(private axis: Axis, private timezone = axis.timezone ?? 'UTC') {}
  options() { return this.configuration }
  setOptions(options: ChartOptionsImpl<number>) { this.configuration = options }
  preprocessData() { /* Values are canonical bar identities. */ }
  convertHorzItemToInternal(item: number) { return item as unknown as InternalHorzScaleItem }
  createConverterToInternalObj(): HorzScaleItemConverterToInternalObj<number> { return item => this.convertHorzItemToInternal(item) }
  key(item: InternalHorzScaleItem | number) { return item as InternalHorzScaleItemKey }
  cacheKey(item: InternalHorzScaleItem) { return item as unknown as number }
  updateFormatter() { /* Labels use the declared axis timezone. */ }
  formatHorzItem(item: InternalHorzScaleItem) { return exactLabel(this.axis, Number(item), this.timezone) }
  formatTickmark(item: TickMark) {
    const label = exactLabel(this.axis, Number(item.time), this.timezone)
    return this.axis.kind === 'utc-ns' ? label.slice(0, 11) : this.axis.kind === 'naive-datetime' ? label.slice(0, 10) : label
  }
  maxTickMarkWeight() { return 1 as TickMarkWeightValue }
  fillWeightsForPoints(points: readonly { -readonly [K in keyof TimeScalePoint]: TimeScalePoint[K] }[], start: number) { for (let i = start; i < points.length; i++) points[i].timeWeight = 1 as TickMarkWeightValue }
}
