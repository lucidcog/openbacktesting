const dayLength = 24 * 60 * 60;

function quartileDataPoint(q0, q1, q2, q3, q4, basePoint) {
	return [
		basePoint + q0,
		basePoint + q1,
		basePoint + q2,
		basePoint + q3,
		basePoint + q4,
	];
}

function whiskerDataSection(startDate, basePoint) {
	return [
		{ quartiles: quartileDataPoint(55, 70, 80, 85, 95, basePoint) },
		{ quartiles: quartileDataPoint(50, 70, 78, 83, 90, basePoint) },
		{
			quartiles: quartileDataPoint(58, 68, 75, 85, 90, basePoint),
			outliers: [45 + basePoint, 50 + basePoint],
		},
		{ quartiles: quartileDataPoint(55, 65, 70, 80, 88, basePoint) },
		{ quartiles: quartileDataPoint(52, 63, 68, 77, 85, basePoint) },
		{
			quartiles: quartileDataPoint(50, 65, 72, 76, 88, basePoint),
			outliers: [45 + basePoint, 95 + basePoint, 100 + basePoint],
		},
		{ quartiles: quartileDataPoint(40, 60, 78, 85, 90, basePoint) },
		{ quartiles: quartileDataPoint(45, 72, 80, 88, 95, basePoint) },
		{ quartiles: quartileDataPoint(47, 70, 82, 86, 97, basePoint) },
		{
			quartiles: quartileDataPoint(53, 68, 83, 87, 92, basePoint),
			outliers: [45 + basePoint, 100 + basePoint],
		},
	].map((d, index) => ({
		...d,
		time: startDate + index * dayLength,
	}));
}

function sampleWhiskerData() {
	return [
		...whiskerDataSection(1677628800, 0),
		...whiskerDataSection(1677628800 + 1 * 10 * dayLength, 20),
		...whiskerDataSection(1677628800 + 2 * 10 * dayLength, 40),
		...whiskerDataSection(1677628800 + (3 * 10 + 1) * dayLength, 30),
	];
}

function determinePadding(halfWidth) {
	if (halfWidth < 2) {return 0;}
	if (halfWidth < 5) {return 1;}
	return Math.ceil(halfWidth / 3);
}

function determineBodyWidth(remainingWidth) {
	if (remainingWidth < 1) {return 0.5;}
	return remainingWidth;
}

function determineLineWidths(bodyWidth) {
	if (bodyWidth < 1) {return 0;}
	if (bodyWidth <= 3) {return bodyWidth;}
	return Math.ceil(bodyWidth / 2);
}

function determineMedianWidth(bodyWidth) {
	if (bodyWidth < 1) {return 0;}
	if (bodyWidth < 4) {return bodyWidth;}
	return bodyWidth + 2;
}

function determineOutlierRadius(lineWidth) {
	if (lineWidth > 6) {return 6;}
	if (lineWidth < 1) {return 0;}
	return lineWidth;
}

function desiredWidths(barSpacing) {
	const widthExcludingWhisker = barSpacing - 1;
	const halfWidth = Math.floor(widthExcludingWhisker / 2);

	const padding = determinePadding(halfWidth);
	const bodyWidth = determineBodyWidth(halfWidth - padding);
	const medianWidth = determineMedianWidth(bodyWidth);
	const lineWidth = determineLineWidths(bodyWidth);
	const outlierRadius = determineOutlierRadius(bodyWidth);

	return {
		body: Math.ceil(bodyWidth),
		medianLine: Math.round(medianWidth),
		extremeLines: Math.round(lineWidth),
		outlierRadius: Math.floor(outlierRadius),
	};
}

class WhiskerBoxSeriesRenderer {
	constructor() {
		this._data = null;
		this._options = null;
		this._hitTestCalls = 0;
	}

	draw(
		target,
		priceConverter
	) {
		target.useMediaCoordinateSpace(scope =>
			this._drawImpl(scope, priceConverter)
		);
	}

	hitTest(
		x,
		y,
		priceConverter
	) {
		if (
			this._data === null ||
			this._data.visibleRange === null
		) {
			return null;
		}

		this._hitTestCalls += 1;
		const radius = desiredWidths(this._data.barSpacing).outlierRadius + 2;
		let bestDistance = Number.POSITIVE_INFINITY;

		for (
			let i = this._data.visibleRange.from;
			i < this._data.visibleRange.to;
			i++
		) {
			const bar = this._data.bars[i];
			const outliers = bar.originalData.outliers || [];
			for (const outlier of outliers) {
				const outlierY = priceConverter(outlier);
				if (outlierY === null) {
					continue;
				}
				const distance = Math.hypot(x - bar.x, y - outlierY);
				if (distance <= radius) {
					bestDistance = Math.min(bestDistance, distance);
				}
			}
		}

		if (!Number.isFinite(bestDistance)) {
			return null;
		}

		return {
			distance: bestDistance,
			type: 'point',
			objectId: 'outlier-100',
			hitTestData: {
				type: 'outlier',
			},
		};
	}

	update(
		data,
		options
	) {
		this._data = data;
		this._options = options;
	}

	_drawImpl(
		renderingScope,
		priceToCoordinate
	) {
		if (
			this._data === null ||
			this._data.bars.length === 0 ||
			this._data.visibleRange === null ||
			this._options === null
		) {
			return;
		}
		const options = this._options;
		const bars = this._data.bars.map(bar => ({
			quartilesY: bar.originalData.quartiles.map(price => Math.round((priceToCoordinate(price) ?? 0))),
			outliers: (bar.originalData.outliers || []).map(price => Math.round((priceToCoordinate(price) ?? 0))),
			x: bar.x,
		}));

		const widths = desiredWidths(this._data.barSpacing);

		renderingScope.context.save();
		for (
			let i = this._data.visibleRange.from;
			i < this._data.visibleRange.to;
			i++
		) {
			const bar = bars[i];
			this._drawOutliers(
				renderingScope.context,
				bar,
				widths.outlierRadius,
				options
			);
			this._drawWhisker(
				renderingScope.context,
				bar,
				widths.extremeLines,
				options
			);
			this._drawBox(renderingScope.context, bar, widths.body, options);
			this._drawMedianLine(
				renderingScope.context,
				bar,
				widths.medianLine,
				options
			);
		}
		renderingScope.context.restore();
	}

	_drawWhisker(
		ctx,
		bar,
		extremeLineWidth,
		options
	) {
		ctx.save();
		ctx.lineWidth = 1;
		ctx.strokeStyle = options.whiskerColor;
		ctx.beginPath();
		ctx.moveTo(bar.x, bar.quartilesY[0]);
		ctx.lineTo(bar.x, bar.quartilesY[1]);
		ctx.moveTo(bar.x, bar.quartilesY[3]);
		ctx.lineTo(bar.x, bar.quartilesY[4]);

		ctx.moveTo(bar.x - extremeLineWidth, bar.quartilesY[0]);
		ctx.lineTo(bar.x + extremeLineWidth, bar.quartilesY[0]);
		ctx.moveTo(bar.x - extremeLineWidth, bar.quartilesY[4]);
		ctx.lineTo(bar.x + extremeLineWidth, bar.quartilesY[4]);
		ctx.stroke();
		ctx.restore();
	}

	_drawBox(
		ctx,
		bar,
		bodyWidth,
		options
	) {
		ctx.save();
		ctx.fillStyle = options.lowerQuartileFill;
		ctx.fillRect(
			bar.x - bodyWidth,
			bar.quartilesY[1],
			bodyWidth * 2,
			bar.quartilesY[2] - bar.quartilesY[1]
		);
		ctx.fillStyle = options.upperQuartileFill;
		ctx.fillRect(
			bar.x - bodyWidth,
			bar.quartilesY[2],
			bodyWidth * 2,
			bar.quartilesY[3] - bar.quartilesY[2]
		);
		ctx.restore();
	}

	_drawMedianLine(
		ctx,
		bar,
		medianLineWidth,
		options
	) {
		ctx.save();
		ctx.lineWidth = 1;
		ctx.strokeStyle = options.whiskerColor;
		ctx.beginPath();
		ctx.moveTo(bar.x - medianLineWidth, bar.quartilesY[2]);
		ctx.lineTo(bar.x + medianLineWidth, bar.quartilesY[2]);
		ctx.stroke();
		ctx.restore();
	}

	_drawOutliers(
		ctx,
		bar,
		extremeLineWidth,
		options
	) {
		ctx.save();
		ctx.fillStyle = options.outlierColor;
		ctx.lineWidth = 0;
		bar.outliers.forEach(outlier => {
			ctx.beginPath();
			ctx.arc(bar.x, outlier, extremeLineWidth, 0, 2 * Math.PI);
			ctx.fill();
			ctx.closePath();
		});
		ctx.restore();
	}
}

const defaultOptions = {
	whiskerColor: '#456599',
	lowerQuartileFill: '#846ED4',
	upperQuartileFill: '#C44760',
	outlierColor: '#777777',
};

class WhiskerBoxSeries {
	constructor() {
		this._renderer = new WhiskerBoxSeriesRenderer();
	}

	priceValueBuilder(plotRow) {
		// we don't consider outliers here
		return [plotRow.quartiles[4], plotRow.quartiles[0], plotRow.quartiles[2]];
	}

	isWhitespace(data) {
		return (data).quartiles === undefined;
	}

	renderer() {
		return this._renderer;
	}

	update(
		data,
		options
	) {
		this._renderer.update(data, options);
	}

	defaultOptions() {
		return defaultOptions;
	}
}

let clickPoint = null;

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

let pass = false;
let hoveredSeriesMatches = false;
let customHitTestUsed = false;
let lastHoveredInfo = null;

function isExpectedCustomHover(mouseParams, myCustomSeries) {
	const csdata = mouseParams.seriesData.get(myCustomSeries);
	if (!csdata) {
		return false;
	}

	return Boolean(
		csdata.quartiles &&
		csdata.quartiles.length === 5 &&
		csdata.time &&
		mouseParams.hoveredInfo &&
		mouseParams.hoveredInfo.type === 'custom' &&
		mouseParams.hoveredInfo.sourceKind === 'series' &&
		mouseParams.hoveredInfo.objectKind === 'custom-object' &&
		mouseParams.hoveredInfo.series === myCustomSeries &&
		mouseParams.hoveredInfo.objectId === 'outlier-100' &&
		mouseParams.hoveredObjectId === 'outlier-100'
	);
}

function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container, {
		rightPriceScale: {
			visible: false,
		},
	});

	const customSeriesView = new WhiskerBoxSeries();
	const myCustomSeries = chart.addCustomSeries(customSeriesView, {
		baseLineColor: '',
		priceLineVisible: false,
		lastValueVisible: false,
	});

	const data = sampleWhiskerData();
	myCustomSeries.setData(data);
	chart.timeScale().fitContent();

	chart.subscribeClick(mouseParams => {
		if (!mouseParams) {
			return;
		}
		lastHoveredInfo = mouseParams.hoveredInfo ?? null;
		hoveredSeriesMatches = mouseParams.hoveredSeries === myCustomSeries;
		if (isExpectedCustomHover(mouseParams, myCustomSeries)) {
			pass = true;
			customHitTestUsed = customSeriesView._renderer._hitTestCalls > 0;
			return;
		}
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			const outlierBar = data.find(item => Array.isArray(item.outliers) && item.outliers.includes(100));
			if (outlierBar) {
				const x = chart.timeScale().timeToCoordinate(outlierBar.time);
				const y = myCustomSeries.priceToCoordinate(100);
				if (x !== null && y !== null) {
					clickPoint = {
						x: Math.round(x),
						y: Math.round(y),
					};
				}
			}
			resolve();
		});
	});
}

function afterInitialInteractions() {
	return Promise.resolve();
}

function afterFinalInteractions() {
	if (!pass) {
		throw new Error(`Expected custom series hover to preserve custom hover semantics. hoveredSeriesMatches=${String(hoveredSeriesMatches)} hoveredInfo=${JSON.stringify(lastHoveredInfo)} customHitTestUsed=${String(customHitTestUsed)}`);
	}
	if (!hoveredSeriesMatches) {
		throw new Error('Expected hoveredSeries to match the custom series.');
	}
	if (!customHitTestUsed) {
		throw new Error('Expected the custom series hitTest hook to be used.');
	}

	return Promise.resolve();
}
