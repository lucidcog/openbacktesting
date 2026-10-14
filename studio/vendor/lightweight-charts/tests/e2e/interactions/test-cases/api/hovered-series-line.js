let hoverPoint = null;
let clickHoverMatched = false;
let lastClickPoint = null;
let lastClickHoveredObjectId = null;
let lastHoveredInfo = null;
let lineSeries = null;

function initialInteractionsToPerform() {
	return [];
}

function finalInteractionsToPerform() {
	if (hoverPoint === null) {
		return [];
	}

	return [{
		action: 'clickXY',
		target: 'pane',
		options: hoverPoint,
	}];
}

function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container, {
		layout: {
			attributionLogo: false,
		},
		rightPriceScale: {
			visible: false,
		},
	});

	lineSeries = chart.addSeries(LightweightCharts.LineSeries, {
		color: '#d84f61',
		lineWidth: 4,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	});

	const data = [
		{ time: '2020-01-01', value: 20 },
		{ time: '2020-01-02', value: 24 },
		{ time: '2020-01-03', value: 28 },
		{ time: '2020-01-04', value: 26 },
		{ time: '2020-01-05', value: 31 },
	];

	lineSeries.setData(data);
	chart.timeScale().fitContent();

	chart.subscribeCrosshairMove(mouseParams => {
		void mouseParams;
	});

	chart.subscribeClick(mouseParams => {
		if (!mouseParams || !mouseParams.point) {
			return;
		}

		lastClickPoint = mouseParams.point;
		lastClickHoveredObjectId = mouseParams.hoveredObjectId ?? null;
		lastHoveredInfo = mouseParams.hoveredInfo ?? null;
		clickHoverMatched = mouseParams.hoveredSeries === lineSeries;
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			const hoverX = chart.timeScale().logicalToCoordinate(2);
			const hoverY = lineSeries.priceToCoordinate(data[2].value);
			if (hoverX === null || hoverY === null) {
				throw new Error('Expected hover coordinates for the built-in line series.');
			}

			hoverPoint = {
				x: Math.round(hoverX),
				y: Math.round(hoverY),
			};
			resolve();
		});
	});
}

function afterInitialInteractions() {
	return Promise.resolve();
}

function afterFinalInteractions() {
	if (!clickHoverMatched) {
		throw new Error(`Expected subscribeClick to expose hoveredSeries for the built-in line series. point=${JSON.stringify(lastClickPoint)} hoveredObjectId=${String(lastClickHoveredObjectId)}`);
	}

	if (
		!lastHoveredInfo ||
		lastHoveredInfo.type !== 'series-point' ||
		lastHoveredInfo.sourceKind !== 'series' ||
		lastHoveredInfo.objectKind !== 'series' ||
		lastHoveredInfo.series !== lineSeries ||
		!(lastHoveredInfo.objectId == null && lastClickHoveredObjectId == null)
	) {
		throw new Error(`Expected hoveredInfo to classify the built-in line hit as a series point. type=${String(lastHoveredInfo && lastHoveredInfo.type)} sourceKind=${String(lastHoveredInfo && lastHoveredInfo.sourceKind)} objectKind=${String(lastHoveredInfo && lastHoveredInfo.objectKind)} objectId=${String(lastHoveredInfo && lastHoveredInfo.objectId)}`);
	}

	return Promise.resolve();
}
