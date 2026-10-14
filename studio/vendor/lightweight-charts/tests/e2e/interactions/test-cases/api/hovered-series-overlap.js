let initialHoverPoint = null;
let finalHoverPoint = null;
let redSeries = null;
let blueSeries = null;
let initialHoverMatched = false;
let finalHoverMatched = false;
const hoverSequence = [];

function initialInteractionsToPerform() {
	if (initialHoverPoint === null) {
		return [];
	}

	return [{
		action: 'moveMouseXY',
		target: 'pane',
		options: initialHoverPoint,
	}];
}

function finalInteractionsToPerform() {
	if (finalHoverPoint === null) {
		return [];
	}

	return [{
		action: 'moveMouseXY',
		target: 'pane',
		options: finalHoverPoint,
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
		hoveredSeriesOnTop: true,
	});

	redSeries = chart.addSeries(LightweightCharts.LineSeries, {
		color: '#d84f61',
		lineWidth: 4,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	});

	blueSeries = chart.addSeries(LightweightCharts.LineSeries, {
		color: '#2563eb',
		lineWidth: 4,
		pointMarkersVisible: true,
		pointMarkersRadius: 4,
	});

	const redData = [
		{ time: '2020-01-01', value: 18 },
		{ time: '2020-01-02', value: 12 },
		{ time: '2020-01-03', value: 14 },
	];

	const blueData = [
		{ time: '2020-01-01', value: 24 },
		{ time: '2020-01-02', value: 14 },
		{ time: '2020-01-03', value: 14 },
	];

	redSeries.setData(redData);
	blueSeries.setData(blueData);
	chart.timeScale().fitContent();

	chart.subscribeCrosshairMove(mouseParams => {
		if (!mouseParams?.point) {
			return;
		}

		hoverSequence.push(mouseParams.hoveredSeries ?? null);
		if (mouseParams.hoveredSeries === redSeries) {
			initialHoverMatched = true;
		}
		if (
			mouseParams.hoveredSeries === blueSeries &&
			mouseParams.hoveredInfo &&
			mouseParams.hoveredInfo.type === 'series-point' &&
			mouseParams.hoveredInfo.sourceKind === 'series' &&
			mouseParams.hoveredInfo.objectKind === 'series' &&
			mouseParams.hoveredInfo.series === blueSeries
		) {
			finalHoverMatched = true;
		}
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			const initialX = chart.timeScale().logicalToCoordinate(0);
			const initialY = redSeries.priceToCoordinate(redData[0].value);
			const finalX = chart.timeScale().logicalToCoordinate(2);
			const finalY = blueSeries.priceToCoordinate(blueData[2].value);
			if (initialX === null || initialY === null || finalX === null || finalY === null) {
				throw new Error('Expected hover coordinates for the overlapping built-in series.');
			}

			initialHoverPoint = {
				x: Math.round(initialX),
				y: Math.round(initialY),
			};

			finalHoverPoint = {
				x: Math.round(finalX),
				y: Math.round(finalY),
			};

			resolve();
		});
	});
}

function afterInitialInteractions() {
	if (!initialHoverMatched) {
		throw new Error(`Expected the first hover to select the initially hovered lower series. sequence=${hoverSequence.map(item => item === redSeries ? 'red' : item === blueSeries ? 'blue' : 'none').join(',')}`);
	}

	return Promise.resolve();
}

function afterFinalInteractions() {
	if (!finalHoverMatched) {
		throw new Error(`Expected hover to switch to the visually top overlapping series instead of staying sticky on the previous hovered series. sequence=${hoverSequence.map(item => item === redSeries ? 'red' : item === blueSeries ? 'blue' : 'none').join(',')}`);
	}

	return Promise.resolve();
}
