/*
	This test checks that the bottom series is drawn above the top series
	when hovering over a 'pointMarker'. Since both lines (series) are on the
	same point normally the top series would be drawn on top, however we
	consider series with point markers to be a higher importance and this will
	promote it to the top.
*/
let hoverPoint;

function initialInteractionsToPerform() {
	return [{ action: 'moveMouseXY', target: 'pane', options: hoverPoint }];
}

function runTestCase(container) {
	window.ignoreMouseMove = true;

	const chart = window.chart = LightweightCharts.createChart(container, {
		layout: { attributionLogo: false },
	});

	const hoveredSeries = chart.addSeries(LightweightCharts.LineSeries, {
		color: '#ff0000',
		lineWidth: 8,
		pointMarkersVisible: true,
		pointMarkersRadius: 6,
	});
	const topSeries = chart.addSeries(LightweightCharts.LineSeries, {
		color: '#0000ff',
		lineWidth: 8,
	});

	const hoveredSeriesData = [
		{ time: '2020-01-01', value: 80 },
		{ time: '2020-01-02', value: 70 },
		{ time: '2020-01-03', value: 60 },
		{ time: '2020-01-04', value: 50 },
		{ time: '2020-01-05', value: 40 },
	];
	const topSeriesData = [
		{ time: '2020-01-01', value: 85 },
		{ time: '2020-01-02', value: 70 },
		{ time: '2020-01-03', value: 60 },
		{ time: '2020-01-04', value: 50 },
		{ time: '2020-01-05', value: 45 },
	];

	hoveredSeries.setData(hoveredSeriesData);
	topSeries.setData(topSeriesData);
	chart.timeScale().fitContent();

	return new Promise(resolve => {
		requestAnimationFrame(() => {
			setTimeout(() => {
				const hoverX = chart.timeScale().timeToCoordinate(hoveredSeriesData[2].time);
				const hoverY = hoveredSeries.priceToCoordinate(hoveredSeriesData[2].value);
				if (hoverX === null || hoverY === null) {
					throw new Error('Expected hover coordinates to be available.');
				}

				hoverPoint = {
					x: Math.round(hoverX),
					y: Math.round(hoverY),
				};
				resolve();
			}, 250);
		});
	});
}
