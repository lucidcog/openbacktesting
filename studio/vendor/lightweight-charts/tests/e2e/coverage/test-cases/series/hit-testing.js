/* global dispatchPointerAt, dispatchTargetSequence, interactivePaneElement, waitForNextFrame */

function interactionsToPerform() {
	return [];
}

let allSeriesChart;
let overlapChart;
let pointSeries;
let priceLineSeries;
let markerSeries;
let areaSeries;
let baselineSeries;
let barSeries;
let candlestickSeries;
let histogramSeries;
let steppedSeries;
let curvedSeries;
let singlePointSeries;
let markerPrimitives;

function createData() {
	return [
		{ time: '2024-01-01', value: 10 },
		{ time: '2024-01-02', value: 50 },
		{ time: '2024-01-03', value: 90 },
	];
}

function createBarData() {
	return [
		{ time: '2024-01-01', open: 80, high: 90, low: 70, close: 75 },
		{ time: '2024-01-02', open: 45, high: 60, low: 40, close: 55 },
		{ time: '2024-01-03', open: 20, high: 30, low: 10, close: 15 },
	];
}

function beforeInteractions(container) {
	container.innerHTML = '';

	const allSeriesContainer = document.createElement('div');
	allSeriesContainer.style.height = '1040px';
	allSeriesContainer.style.marginBottom = '12px';
	container.appendChild(allSeriesContainer);

	const overlapContainer = document.createElement('div');
	overlapContainer.style.height = '220px';
	container.appendChild(overlapContainer);

	allSeriesChart = LightweightCharts.createChart(allSeriesContainer, {
		addDefaultPane: false,
		hoveredSeriesOnTop: true,
		rightPriceScale: { visible: false },
	});

	const pointPane = allSeriesChart.addPane(true);
	const priceLinePane = allSeriesChart.addPane(true);
	const markerPane = allSeriesChart.addPane(true);
	const areaPane = allSeriesChart.addPane(true);
	const baselinePane = allSeriesChart.addPane(true);
	const barPane = allSeriesChart.addPane(true);
	const candlePane = allSeriesChart.addPane(true);
	const histogramPane = allSeriesChart.addPane(true);
	const steppedPane = allSeriesChart.addPane(true);
	const curvedPane = allSeriesChart.addPane(true);
	const singlePointPane = allSeriesChart.addPane(true);

	const lineData = createData();
	const barData = createBarData();

	pointSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		hitTestTolerance: 8,
		lineWidth: 4,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	}, pointPane.paneIndex());

	priceLineSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		lastValueVisible: false,
	}, priceLinePane.paneIndex());

	markerSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		lineWidth: 3,
		pointMarkersVisible: false,
	}, markerPane.paneIndex());

	areaSeries = allSeriesChart.addSeries(LightweightCharts.AreaSeries, {
		lineWidth: 4,
	}, areaPane.paneIndex());

	baselineSeries = allSeriesChart.addSeries(LightweightCharts.BaselineSeries, {
		lineWidth: 4,
	}, baselinePane.paneIndex());

	barSeries = allSeriesChart.addSeries(LightweightCharts.BarSeries, {
		hitTestTolerance: 8,
	}, barPane.paneIndex());

	candlestickSeries = allSeriesChart.addSeries(LightweightCharts.CandlestickSeries, {}, candlePane.paneIndex());

	histogramSeries = allSeriesChart.addSeries(LightweightCharts.HistogramSeries, {
		base: 0,
		hitTestTolerance: 8,
	}, histogramPane.paneIndex());

	steppedSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		lineType: LightweightCharts.LineType.WithSteps,
		lineWidth: 5,
	}, steppedPane.paneIndex());

	curvedSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		lineType: LightweightCharts.LineType.Curved,
		lineWidth: 10,
	}, curvedPane.paneIndex());

	singlePointSeries = allSeriesChart.addSeries(LightweightCharts.LineSeries, {
		lineWidth: 6,
		pointMarkersVisible: false,
	}, singlePointPane.paneIndex());

	pointSeries.setData(lineData);
	priceLineSeries.setData([
		{ time: '2024-01-01', value: 10 },
		{ time: '2024-01-02', value: 20 },
		{ time: '2024-01-03', value: 30 },
	]);
	markerSeries.setData(lineData);
	areaSeries.setData(lineData);
	baselineSeries.setData(lineData);
	barSeries.setData(barData);
	candlestickSeries.setData(barData);
	histogramSeries.setData([
		{ time: '2024-01-01', value: 90 },
		{ time: '2024-01-02', value: 50 },
		{ time: '2024-01-03', value: 10 },
	]);
	steppedSeries.setData(lineData);
	curvedSeries.setData([
		{ time: '2024-01-01', value: 10 },
		{ time: '2024-01-02', value: 85 },
		{ time: '2024-01-03', value: 20 },
		{ time: '2024-01-04', value: 75 },
		{ time: '2024-01-05', value: 40 },
	]);
	singlePointSeries.setData([
		{ time: '2024-01-02', value: 42 },
	]);

	priceLineSeries.createPriceLine({
		price: 50,
		color: '#111827',
		lineWidth: 2,
		axisLabelVisible: false,
		title: '',
		id: 'COVERAGE-BUILTIN-PRICE-LINE',
	});

	markerPrimitives = LightweightCharts.createSeriesMarkers(markerSeries, [
		{
			time: lineData[1].time,
			position: 'inBar',
			color: '#f97316',
			shape: 'circle',
			text: 'M',
			id: 'CENTER-MARKER',
		},
	]);

	allSeriesChart.timeScale().fitContent();

	overlapChart = LightweightCharts.createChart(overlapContainer, {
		hoveredSeriesOnTop: false,
		rightPriceScale: { visible: false },
	});

	const backSeries = overlapChart.addSeries(LightweightCharts.LineSeries, {
		color: '#2563eb',
		lineWidth: 5,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	});
	const frontSeries = overlapChart.addSeries(LightweightCharts.LineSeries, {
		color: '#dc2626',
		lineWidth: 3,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	});

	backSeries.setData(lineData);
	frontSeries.setData([
		{ time: '2024-01-01', value: 90 },
		{ time: '2024-01-02', value: 50 },
		{ time: '2024-01-03', value: 10 },
	]);
	overlapChart.timeScale().fitContent();

	for (const targetChart of [allSeriesChart, overlapChart]) {
		targetChart.subscribeCrosshairMove(mouseParams => {
			void mouseParams?.hoveredSeries;
			void mouseParams?.hoveredObjectId;
			void mouseParams?.hoveredInfo;
		});

		targetChart.subscribeClick(mouseParams => {
			void mouseParams?.hoveredSeries;
			void mouseParams?.hoveredObjectId;
			void mouseParams?.hoveredInfo;
		});
	}

	return new Promise(resolve => {
		requestAnimationFrame(resolve);
	});
}

function collectBuiltInPaneTargets() {
	const panes = allSeriesChart.panes();
	const centerX = allSeriesChart.timeScale().logicalToCoordinate(1);
	const rightX = allSeriesChart.timeScale().logicalToCoordinate(2);
	const pointY = pointSeries.priceToCoordinate(50);
	const pointStrokeX = centerX !== null && rightX !== null ? (centerX + rightX) / 2 : null;
	const pointStrokeY = pointSeries.priceToCoordinate(70);
	const priceLineY = priceLineSeries.priceToCoordinate(50);
	const markerY = markerSeries.priceToCoordinate(50);
	const areaY = areaSeries.priceToCoordinate(50);
	const baselineY = baselineSeries.priceToCoordinate(50);
	const barY = barSeries.priceToCoordinate(50);
	const candleY = candlestickSeries.priceToCoordinate(50);
	const histogramY = histogramSeries.priceToCoordinate(50);
	const steppedY = steppedSeries.priceToCoordinate(30);
	const curvedX = allSeriesChart.timeScale().logicalToCoordinate(1.5);
	const curvedY = curvedSeries.priceToCoordinate(45);
	const singlePointX = allSeriesChart.timeScale().logicalToCoordinate(1);
	const singlePointY = singlePointSeries.priceToCoordinate(42);

	const requiredCoordinates = [
		centerX,
		rightX,
		pointY,
		pointStrokeX,
		pointStrokeY,
		priceLineY,
		markerY,
		areaY,
		baselineY,
		barY,
		candleY,
		histogramY,
		steppedY,
		curvedX,
		curvedY,
		singlePointX,
		singlePointY,
	];

	if (requiredCoordinates.some(coordinate => coordinate === null)) {
		return [];
	}

	return [
		{ pane: interactivePaneElement(panes[0].getHTMLElement()), x: centerX, y: pointY },
		{ pane: interactivePaneElement(panes[0].getHTMLElement()), x: pointStrokeX, y: pointStrokeY },
		{ pane: interactivePaneElement(panes[1].getHTMLElement()), x: (centerX + rightX) / 2, y: priceLineY },
		{ pane: interactivePaneElement(panes[2].getHTMLElement()), x: centerX, y: markerY },
		{ pane: interactivePaneElement(panes[3].getHTMLElement()), x: centerX, y: areaY },
		{ pane: interactivePaneElement(panes[4].getHTMLElement()), x: centerX, y: baselineY },
		{ pane: interactivePaneElement(panes[5].getHTMLElement()), x: centerX, y: barY },
		{ pane: interactivePaneElement(panes[6].getHTMLElement()), x: centerX, y: candleY },
		{ pane: interactivePaneElement(panes[7].getHTMLElement()), x: centerX, y: histogramY },
		{ pane: interactivePaneElement(panes[8].getHTMLElement()), x: centerX, y: steppedY },
		{ pane: interactivePaneElement(panes[9].getHTMLElement()), x: curvedX, y: curvedY },
		{ pane: interactivePaneElement(panes[10].getHTMLElement()), x: singlePointX, y: singlePointY },
	];
}

async function afterInteractions() {
	await waitForNextFrame();
	await dispatchTargetSequence(collectBuiltInPaneTargets());

	const overlapPane = interactivePaneElement(overlapChart.panes()[0].getHTMLElement());
	const overlapX = overlapChart.timeScale().logicalToCoordinate(1);
	if (overlapPane !== null && overlapX !== null) {
		dispatchPointerAt(overlapPane, overlapX, 50);
		await waitForNextFrame(20);
	}

	markerPrimitives.detach();
	await waitForNextFrame(50);
}
