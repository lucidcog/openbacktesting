import type { IPrimitivePaneRenderer, ISeriesPrimitive, SeriesAttachedParameter } from 'lightweight-charts'
import { interpolatedCoordinate, type Point } from './model'

export class Bands implements ISeriesPrimitive<number> {
  private attachedTo?: SeriesAttachedParameter<number>
  constructor(private polygons: Point[][], private color: string, private backgrounds?: Map<number, string | null>, private times: number[] = []) {}
  attached(parameters: SeriesAttachedParameter<number>) { this.attachedTo = parameters }
  detached() { this.attachedTo = undefined }
  paneViews() { return [{ zOrder: () => 'bottom' as const, renderer: () => ({ draw: (target: Parameters<IPrimitivePaneRenderer['draw']>[0]) => {
    const api = this.attachedTo
    if (!api) return
    target.useMediaCoordinateSpace(({ context, mediaSize }) => {
      const x = (time: number) => interpolatedCoordinate(time, this.times, value => api.chart.timeScale().timeToCoordinate(value))
      if (this.backgrounds) {
        const width = api.chart.timeScale().options().barSpacing
        for (const [time, color] of this.backgrounds) {
          const coordinate = x(time)
          if (color !== null && coordinate !== null) { context.fillStyle = color; context.fillRect(coordinate - width / 2, 0, width, mediaSize.height) }
        }
      }
      context.fillStyle = this.color
      for (const polygon of this.polygons) {
        const coordinates = polygon.map(point => ({ x: x(point.time), y: api.series.priceToCoordinate(point.value) }))
        if (coordinates.some(point => point.x === null || point.y === null)) continue
        context.beginPath()
        coordinates.forEach((point, index) => { if (index === 0) context.moveTo(point.x!, point.y!); else context.lineTo(point.x!, point.y!) })
        context.closePath(); context.fill()
      }
    })
  } }) }] }
}
