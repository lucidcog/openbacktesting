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
let lastHoveredInfo = null;
let lastHoveredObjectId = null;
let hoveredSeriesMatches = false;

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
		lastValueVisible: false,
	});

	customSeries.setData([
		{ time: '2024-01-01', high: 22, low: 18 },
		{ time: '2024-01-02', high: 24, low: 20 },
		{ time: '2024-01-03', high: 26, low: 21 },
	]);

	customSeries.createPriceLine({
		price: 24,
		color: '#111827',
		lineWidth: 2,
		axisLabelVisible: false,
		title: '',
		id: 'CUSTOM-PRICE-LINE',
	});

	chart.timeScale().fitContent();

	chart.subscribeClick(mouseParams => {
		if (!mouseParams) {
			return;
		}

		lastHoveredInfo = mouseParams.hoveredInfo ?? null;
		lastHoveredObjectId = mouseParams.hoveredObjectId ?? null;
		hoveredSeriesMatches = mouseParams.hoveredSeries === customSeries;

		if (
			mouseParams.hoveredObjectId === 'CUSTOM-PRICE-LINE' &&
			mouseParams.hoveredInfo &&
			mouseParams.hoveredInfo.type === 'price-line' &&
			mouseParams.hoveredInfo.sourceKind === 'series' &&
			mouseParams.hoveredInfo.objectKind === 'custom-price-line' &&
			mouseParams.hoveredInfo.objectId === 'CUSTOM-PRICE-LINE' &&
			mouseParams.hoveredInfo.series === customSeries
		) {
			pass = true;
		}
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			const leftX = chart.timeScale().logicalToCoordinate(1);
			const rightX = chart.timeScale().logicalToCoordinate(2);
			const y = customSeries.priceToCoordinate(24);
			if (leftX === null || rightX === null || y === null) {
				throw new Error('Expected coordinates for custom-series price line hit test.');
			}

			clickPoint = {
				x: Math.round((leftX + rightX) / 2),
				y: Math.round(y),
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
		throw new Error(`Expected custom-series price line hit to preserve price-line semantics. hoveredSeriesMatches=${String(hoveredSeriesMatches)} hoveredObjectId=${String(lastHoveredObjectId)} hoveredInfo=${JSON.stringify(lastHoveredInfo)}`);
	}

	return Promise.resolve();
}
