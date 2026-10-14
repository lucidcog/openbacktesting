import { ensureNotNull } from '../../helpers/assertions';

import { BarPrice } from '../../model/bar';
import { Coordinate } from '../../model/coordinate';
import { InternalHitTestCandidate } from '../../model/internal-hit-test';
import { ISeriesBarColorer } from '../../model/series-bar-colorer';
import { TimePointIndex } from '../../model/time-data';
import { HistogramItem, PaneRendererHistogram, PaneRendererHistogramData } from '../../renderers/histogram-renderer';
import { hitTestSeriesRange } from '../../renderers/range-hit-test';

import { LinePaneViewBase } from './line-pane-view-base';

export class SeriesHistogramPaneView extends LinePaneViewBase<'Histogram', HistogramItem, PaneRendererHistogram> {
	protected readonly _renderer: PaneRendererHistogram = new PaneRendererHistogram();

	protected override _hitTestImpl(x: Coordinate, y: Coordinate): InternalHitTestCandidate | null {
		const histogramBase = this._series.priceScale().priceToCoordinate(this._series.options().base, ensureNotNull(this._series.firstValue()).value);
		if (histogramBase === null) {
			return null;
		}

		return hitTestSeriesRange(
			this._items,
			this._itemsVisibleRange,
			x,
			y,
			this._model.timeScale().barSpacing(),
			this._series.options().hitTestTolerance,
			(item: HistogramItem, out: [Coordinate, Coordinate]) => {
				out[0] = item.y;
				out[1] = histogramBase;
			}
		);
	}

	protected _createRawItem(time: TimePointIndex, price: BarPrice, colorer: ISeriesBarColorer<'Histogram'>): HistogramItem {
		return {
			...this._createRawItemBase(time, price),
			...colorer.barStyle(time),
		};
	}

	protected _prepareRendererData(): void {
		const data: PaneRendererHistogramData = {
			items: this._items,
			barSpacing: this._model.timeScale().barSpacing(),
			visibleRange: this._itemsVisibleRange,
			histogramBase: this._series.priceScale().priceToCoordinate(this._series.options().base, ensureNotNull(this._series.firstValue()).value),
		};

		this._renderer.setData(data);
	}
}
