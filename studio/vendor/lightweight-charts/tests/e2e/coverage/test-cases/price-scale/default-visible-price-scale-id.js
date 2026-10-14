function interactionsToPerform() {
	return [];
}

function generateData(multiplier) {
	const data = [];
	const time = new Date(Date.UTC(2020, 0, 1, 0, 0, 0, 0));

	for (let i = 0; i < 30; ++i) {
		data.push({
			time: time.getTime() / 1000,
			value: (i + 1) * multiplier,
		});

		time.setUTCDate(time.getUTCDate() + 1);
	}

	return data;
}

function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container, {
		defaultVisiblePriceScaleId: 'left',
		leftPriceScale: {
			visible: true,
			invertScale: true,
		},
		rightPriceScale: {
			visible: true,
			invertScale: false,
		},
	});

	const defaultLeftSeries = chart.addSeries(LightweightCharts.LineSeries);
	defaultLeftSeries.setData(generateData(1));

	const explicitRightSeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceScaleId: 'right',
	});
	explicitRightSeries.setData(generateData(10));

	console.assert(defaultLeftSeries.priceScale().options().invertScale === true, 'implicit series should use the configured left default price scale');
	console.assert(explicitRightSeries.priceScale().options().invertScale === false, 'explicit price scale should still override the default price scale');

	chart.applyOptions({
		defaultVisiblePriceScaleId: 'right',
	});

	const defaultRightSeries = chart.addSeries(LightweightCharts.HistogramSeries);
	defaultRightSeries.setData(generateData(100));

	console.assert(defaultRightSeries.priceScale().options().invertScale === false, 'implicit series should use the updated right default price scale');
	console.assert(chart.priceScale('left').width() > 0, 'left price scale should stay visible');
	console.assert(chart.priceScale('right').width() > 0, 'right price scale should stay visible');

	return Promise.resolve();
}

function afterInteractions() {
	return Promise.resolve();
}
