function generateData(start, step, wobble) {
	const data = [];
	const time = new Date(Date.UTC(2020, 0, 1, 0, 0, 0, 0));

	for (let i = 0; i < 70; ++i) {
		data.push({
			time: time.getTime() / 1000,
			value: start + i * step + (i % 5) * wobble,
		});

		time.setUTCDate(time.getUTCDate() + 1);
	}

	return data;
}

function runTestCase(container) {
	const chart = window.chart = LightweightCharts.createChart(container, {
		defaultVisiblePriceScaleId: 'left',
		layout: { attributionLogo: false },
		leftPriceScale: {
			visible: true,
			borderColor: '#d1d4dc',
		},
		rightPriceScale: {
			visible: true,
			borderColor: '#d1d4dc',
		},
	});

	const leftSeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceScaleId: 'left',
		color: '#c62828',
		lineWidth: 2,
		lastValueVisible: false,
		priceLineVisible: false,
	});
	leftSeries.setData(generateData(110, 1.8, 0.9));

	const rightSeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceScaleId: 'right',
		color: '#1565c0',
		lineWidth: 2,
		lastValueVisible: false,
		priceLineVisible: false,
	});
	rightSeries.setData(generateData(1200, 17, 6));

	const overlaySeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceScaleId: 'overlay-scale',
		color: '#2e7d32',
		lineWidth: 2,
		title: 'OVR',
		lastValueVisible: true,
		priceLineVisible: false,
	});
	overlaySeries.setData(generateData(160, 1.2, 0.5));

	chart.timeScale().fitContent();
}
