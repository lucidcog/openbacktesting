import { IPaneRenderer } from '../../renderers/ipane-renderer';
import { hitTestLineSeries } from '../../renderers/line-hit-test';

import { Coordinate } from '../coordinate';
import { InternalHitTestCandidate } from '../internal-hit-test';
import { PricedValue } from '../price-scale';
import { TimedValue } from '../time-data';
import { LinePaneViewBase } from './line-pane-view-base';

export abstract class LineHitTestPaneViewBase<
	TSeriesType extends 'Line' | 'Area' | 'Baseline',
	ItemType extends PricedValue & TimedValue,
	TRenderer extends IPaneRenderer
> extends LinePaneViewBase<TSeriesType, ItemType, TRenderer> {
	protected override _hitTestImpl(x: Coordinate, y: Coordinate): InternalHitTestCandidate | null {
		const options = this._series.options();
		return hitTestLineSeries(
			this._items,
			this._itemsVisibleRange,
			x,
			y,
			options.lineType,
			options.lineVisible ? options.lineWidth : 1,
			options.pointMarkersVisible ? (options.pointMarkersRadius || options.lineWidth / 2 + 2) : undefined,
			this._model.timeScale().barSpacing(),
			options.hitTestTolerance
		);
	}
}
