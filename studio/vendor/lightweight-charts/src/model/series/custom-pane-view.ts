import { CanvasRenderingTarget2D } from 'fancy-canvas';

import { undefinedIfNull } from '../../helpers/strict-type-checks';

import { Coordinate } from '../../model/coordinate';
import { HitTestPriority, InternalHitTestCandidate } from '../../model/internal-hit-test';
import { IPaneRenderer } from '../../renderers/ipane-renderer';
import { hitTestSeriesRange } from '../../renderers/range-hit-test';

import { IChartModelBase } from '../chart-model';
import {
	CustomBarItemData,
	CustomConflationContext,
	CustomData,
	CustomSeriesHitTestResult,
	CustomSeriesPricePlotValues,
	CustomSeriesWhitespaceData,
	ICustomSeriesPaneRenderer,
	ICustomSeriesPaneView,
	PriceToCoordinateConverter,
} from '../icustom-series';
import { ISeries } from '../iseries';
import { PriceScale } from '../price-scale';
import { SeriesPlotRow } from '../series-data';
import { SeriesOptionsMap } from '../series-options';
import { TimedValue } from '../time-data';
import { ITimeScale } from '../time-scale';
import { ISeriesCustomPaneView } from './pane-view';
import { SeriesPaneViewBase } from './series-pane-view-base';

type CustomBarItemBase = TimedValue;

interface CustomBarItem extends CustomBarItemBase {
	barColor: string;
	originalData?: Record<string, unknown>;
}

class CustomSeriesPaneRendererWrapper implements IPaneRenderer {
	private readonly _sourceRenderer: ICustomSeriesPaneRenderer;
	private readonly _priceScale: PriceToCoordinateConverter;

	public constructor(
		sourceRenderer: ICustomSeriesPaneRenderer,
		priceScale: PriceToCoordinateConverter
	) {
		this._sourceRenderer = sourceRenderer;
		this._priceScale = priceScale;
	}

	public draw(
		target: CanvasRenderingTarget2D,
		isHovered: boolean,
		hitTestData?: unknown
	): void {
		this._sourceRenderer.draw(target, this._priceScale, isHovered, hitTestData);
	}
}

function customHitPriority(type: CustomSeriesHitTestResult['type']): HitTestPriority {
	switch (type) {
		case 'point':
			return HitTestPriority.Point;
		case 'range':
			return HitTestPriority.Range;
		case 'line':
		case 'custom':
		default:
			return HitTestPriority.Line;
	}
}

function normalizeCustomHit(
	result: CustomSeriesHitTestResult
): InternalHitTestCandidate {
	return {
		distance: result.distance,
		priority: customHitPriority(result.type),
		itemType: 'custom',
		cursorStyle: result.cursorStyle,
		externalId: result.objectId,
		hitTestData: result.hitTestData,
	};
}

export class SeriesCustomPaneView extends SeriesPaneViewBase<
	'Custom'& keyof SeriesOptionsMap,
	CustomBarItem,
	CustomSeriesPaneRendererWrapper
> implements ISeriesCustomPaneView {
	protected readonly _renderer: CustomSeriesPaneRendererWrapper;
	private readonly _paneView: ICustomSeriesPaneView<unknown>;
	private readonly _sourceRenderer: ICustomSeriesPaneRenderer;

	public constructor(
		series: ISeries<'Custom' & keyof SeriesOptionsMap>,
		model: IChartModelBase,
		paneView: ICustomSeriesPaneView<unknown>
	) {
		super(series, model, false);
		this._paneView = paneView;
		this._sourceRenderer = this._paneView.renderer();
		this._renderer = new CustomSeriesPaneRendererWrapper(
			this._sourceRenderer,
			(price: number) => this._rendererPriceCoordinate(price)
		);
	}

	public get conflationReducer(): ((item1: CustomConflationContext<unknown, CustomData<unknown>>, item2: CustomConflationContext<unknown, CustomData<unknown>>) => CustomData<unknown>) | undefined {
		// eslint-disable-next-line @typescript-eslint/unbound-method
		return this._paneView.conflationReducer;
	}

	public priceValueBuilder(plotRow: CustomData<unknown> | CustomSeriesWhitespaceData<unknown>): CustomSeriesPricePlotValues {
		return this._paneView.priceValueBuilder(plotRow);
	}

	public isWhitespace(data: CustomData<unknown> | CustomSeriesWhitespaceData<unknown>): data is CustomSeriesWhitespaceData<unknown> {
		return this._paneView.isWhitespace(data);
	}

	protected override _hitTestImpl(x: Coordinate, y: Coordinate): InternalHitTestCandidate | null {
		const customHit = this._sourceRenderer.hitTest?.(x, y, (price: number) => this._rendererPriceCoordinate(price));
		if (customHit !== null && customHit !== undefined) {
			return normalizeCustomHit(customHit);
		}

		const fallbackHit = hitTestSeriesRange(
			this._items,
			this._itemsVisibleRange,
			x,
			y,
			this._model.timeScale().barSpacing(),
			this._series.options().hitTestTolerance,
			(bar: CustomBarItem, out: [Coordinate, Coordinate]) => {
				const originalData = bar.originalData as unknown as CustomData<unknown> | CustomSeriesWhitespaceData<unknown> | undefined;
				let top = NaN;
				let bottom = NaN;

				if (originalData !== undefined && !this._paneView.isWhitespace(originalData)) {
					for (const price of this._paneView.priceValueBuilder(originalData)) {
						const coordinate = this._rendererPriceCoordinate(price);
						if (coordinate === null) {
							continue;
						}
						top = Number.isNaN(top) ? coordinate : Math.min(top, coordinate);
						bottom = Number.isNaN(bottom) ? coordinate : Math.max(bottom, coordinate);
					}
				}

				out[0] = top as Coordinate;
				out[1] = bottom as Coordinate;
			}
		);

		return fallbackHit === null ? null : {
			...fallbackHit,
			itemType: 'custom',
		};
	}

	protected _fillRawPoints(): void {
		const colorer = this._series.barColorer();
		this._items = this._series
			.conflatedBars()
			.rows()
			.map((row: SeriesPlotRow<'Custom'>) => {
				return {
					time: row.index,
					x: NaN as Coordinate,
					...colorer.barStyle(row.index),
					originalData: row.data,
				};
			});
	}

	protected override _convertToCoordinates(
		priceScale: PriceScale,
		timeScale: ITimeScale
	): void {
		timeScale.indexesToCoordinates(
			this._items,
			undefinedIfNull(this._itemsVisibleRange)
		);
	}

	protected _prepareRendererData(): void {
		this._paneView.update(
			{
				bars: this._items.map(unwrapItemData),
				barSpacing: this._model.timeScale().barSpacing(),
				visibleRange: this._itemsVisibleRange,
				conflationFactor: this._model.timeScale().conflationFactor(),
			},
			this._series.options()
		);
	}

	private _rendererPriceCoordinate(price: number): Coordinate | null {
		const firstValue = this._series.firstValue();
		if (firstValue === null) {
			return null;
		}

		return this._series.priceScale().priceToCoordinate(price, firstValue.value);
	}
}

function unwrapItemData(
	item: CustomBarItem
): CustomBarItemData<unknown> {
	return {
		x: item.x,
		time: item.time,
		originalData: item.originalData as unknown as CustomData<unknown>,
		barColor: item.barColor,
	};
}
