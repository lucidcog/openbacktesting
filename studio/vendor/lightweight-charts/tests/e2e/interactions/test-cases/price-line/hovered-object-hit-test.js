function generateData() {
	const res = [];
	const time = new Date(Date.UTC(2018, 0, 1, 0, 0, 0, 0));
	for (let i = 0; i < 500; ++i) {
		res.push({
			time: time.getTime() / 1000,
			value: i,
		});

		time.setUTCDate(time.getUTCDate() + 1);
	}
	return res;
}

function initialInteractionsToPerform() {
	return [{ action: 'click' }];
}

function finalInteractionsToPerform() {
	if (clickPoint === null) {
		return [];
	}

	return [{
		action: 'clickXY',
		target: 'pane',
		options: clickPoint,
	}];
}

let chart;
let createdPriceLine = false;
let pass = false;
let lastHoveredObjectId = null;
let lastHoveredSeriesMatched = false;
let lastHoveredInfo = null;
let clickPoint = null;

function beforeInteractions(container) {
	chart = LightweightCharts.createChart(container);

	const mainSeries = chart.addSeries(LightweightCharts.LineSeries);

	mainSeries.setData(generateData());

	chart.subscribeClick(mouseParams => {
		if (!mouseParams) {
			return;
		}
		lastHoveredObjectId = mouseParams.hoveredObjectId ?? null;
		lastHoveredSeriesMatched = mouseParams.hoveredSeries === mainSeries;
		lastHoveredInfo = mouseParams.hoveredInfo ?? null;
		if (
			mouseParams.hoveredObjectId === 'TEST' &&
			mouseParams.hoveredInfo &&
			mouseParams.hoveredInfo.type === 'price-line' &&
			mouseParams.hoveredInfo.sourceKind === 'series' &&
			mouseParams.hoveredInfo.objectKind === 'custom-price-line' &&
			mouseParams.hoveredInfo.objectId === 'TEST' &&
			mouseParams.hoveredInfo.series === mainSeries
		) {
			pass = true;
			return;
		}
		if (!createdPriceLine) {
			const price = mainSeries.coordinateToPrice(mouseParams.point.y);
			const myPriceLine = {
				price,
				color: '#000',
				lineWidth: 2,
				lineStyle: 2,
				axisLabelVisible: false,
				title: '',
				id: 'TEST',
			};
			mainSeries.createPriceLine(myPriceLine);
			clickPoint = {
				x: Math.round(mouseParams.point.x),
				y: Math.round(mainSeries.priceToCoordinate(price)),
			};
			createdPriceLine = true;
		}
	});

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			resolve();
		});
	});
}

function afterInitialInteractions() {
	return new Promise(resolve => {
		requestAnimationFrame(() => {
			setTimeout(resolve, 500); // large enough so the browser doesn't think it is a double click
		});
	});
}

function afterFinalInteractions() {
	if (!createdPriceLine) {
		throw new Error('Expected price line to be created and added to series.');
	}

	if (!pass) {
		throw new Error(`Expected hoveredObjectId to be equal to 'TEST'. Received ${String(lastHoveredObjectId)}. hoveredSeriesMatched=${String(lastHoveredSeriesMatched)} hoveredInfo=${JSON.stringify(lastHoveredInfo)}.`);
	}

	return Promise.resolve();
}
