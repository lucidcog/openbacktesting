class RangeOnlyRenderer {
	constructor() {
		this._data = null;
	}

	draw(target, priceConverter) {
		if (this._data === null || this._data.visibleRange === null) {
			return;
		}

		target.useMediaCoordinateSpace(scope => {
			const ctx = scope.context;
			ctx.save();
			ctx.strokeStyle = '#7c3aed';
			ctx.lineWidth = 3;
			for (let i = this._data.visibleRange.from; i < this._data.visibleRange.to; i++) {
				const bar = this._data.bars[i];
				const top = priceConverter(bar.originalData.high);
				const bottom = priceConverter(bar.originalData.low);
				if (top === null || bottom === null) {
					continue;
				}

				ctx.beginPath();
				ctx.moveTo(bar.x, top);
				ctx.lineTo(bar.x, bottom);
				ctx.stroke();
			}
			ctx.restore();
		});
	}

	update(data) {
		this._data = data;
	}
}

class RangeOnlySeries {
	constructor() {
		this._renderer = new RangeOnlyRenderer();
	}

	priceValueBuilder(plotRow) {
		return [plotRow.high, plotRow.low];
	}

	isWhitespace(data) {
		return data.high === undefined || data.low === undefined;
	}

	renderer() {
		return this._renderer;
	}

	update(data, options) {
		void options;
		this._renderer.update(data);
	}

	defaultOptions() {
		return {};
	}
}

let clickPoint = null;
let pass = false;
let hoveredSeriesMatches = false;
let lastHoveredInfo = null;
let lastHoveredObjectId = null;

function isExpectedFallbackHover(mouseParams, customSeries) {
	const csData = mouseParams.seriesData.get(customSeries);
	if (!csData) {
		return false;
	}

	return Boolean(
		csData.high === 24 &&
		csData.low === 20 &&
		mouseParams.hoveredSeries === customSeries &&
		mouseParams.hoveredObjectId === undefined &&
		mouseParams.hoveredInfo &&
		mouseParams.hoveredInfo.type === 'custom' &&
		mouseParams.hoveredInfo.sourceKind === 'series' &&
		mouseParams.hoveredInfo.objectKind === 'series' &&
		mouseParams.hoveredInfo.series === customSeries &&
		mouseParams.hoveredInfo.objectId === undefined
	);
}

function initialInteractionsToPerform() {
	if (clickPoint === null) {
		return [];
	}

	return [{
		action: 'clickXY',
		target: 'pane',
		options: clickPoint,
	}];
}

function finalInteractionsToPerform() {
	return [];
}

function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container, {
		rightPriceScale: {
			visible: false,
		},
	});

	const customSeries = chart.addCustomSeries(new RangeOnlySeries(), {
		priceLineVisible: false,
		lastValueVisible: false,
		hitTestTolerance: 6,
	});

	const data = [
		{ time: '2024-01-01', high: 22, low: 18 },
		{ time: '2024-01-02', high: 24, low: 20 },
		{ time: '2024-01-03', high: 26, low: 21 },
	];

	customSeries.setData(data);
	chart.timeScale().fitContent();

	chart.subscribeClick(mouseParams => {
		if (!mouseParams) {
			return;
		}

		lastHoveredInfo = mouseParams.hoveredInfo ?? null;
		lastHoveredObjectId = mouseParams.hoveredObjectId ?? null;
		hoveredSeriesMatches = mouseParams.hoveredSeries === customSeries;

		if (isExpectedFallbackHover(mouseParams, customSeries)) {
			pass = true;
		}
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			const x = chart.timeScale().logicalToCoordinate(1);
			const top = customSeries.priceToCoordinate(24);
			const bottom = customSeries.priceToCoordinate(20);
			if (x === null || top === null || bottom === null) {
				throw new Error('Expected coordinates for fallback custom-series hit test.');
			}

			clickPoint = {
				x: Math.round(x),
				y: Math.round((top + bottom) / 2),
			};
			resolve();
		});
	});
}

function afterInitialInteractions() {
	return Promise.resolve();
}

function afterFinalInteractions() {
	if (!pass) {
		throw new Error(`Expected fallback custom-series hit testing to populate hovered series payloads. hoveredSeriesMatches=${String(hoveredSeriesMatches)} hoveredObjectId=${String(lastHoveredObjectId)} hoveredInfo=${JSON.stringify(lastHoveredInfo)}`);
	}

	if (!hoveredSeriesMatches) {
		throw new Error('Expected hoveredSeries to match the fallback custom series.');
	}

	return Promise.resolve();
}
