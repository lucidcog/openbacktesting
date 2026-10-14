function interactionsToPerform() {
	return [];
}

let mainSeries;

function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container);

	mainSeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceFormat: {
			type: 'price',
			minMove: 0.25,
			precision: undefined,
		},
	});

	mainSeries.setData(generateLineData());
	mainSeries.priceFormatter().format(1.25);
	mainSeries.priceFormatter().format(1.5);

	const overlaySeries = chart.addSeries(LightweightCharts.AreaSeries, {
		priceScaleId: 'overlay-id',
		priceFormat: {
			type: 'volume',
		},
	});
	overlaySeries.setData(generateLineData());

	// Should be a volume, therefore test the various states for the formatter.
	overlaySeries.priceFormatter().format(1);
	overlaySeries.priceFormatter().format(0.001);
	overlaySeries.priceFormatter().format(1234);
	overlaySeries.priceFormatter().format(1234567);
	overlaySeries.priceFormatter().format(1234567890);

	return new Promise(resolve => {
		requestAnimationFrame(resolve);
	});
}

function afterInteractions() {
	mainSeries.applyOptions({
		priceFormat: {
			type: 'price',
			minMove: 0.125,
			precision: undefined,
		},
	});
	mainSeries.priceFormatter().format(1.125);
	mainSeries.priceFormatter().format(1.375);

	mainSeries.applyOptions({
		priceFormat: {
			type: 'price',
			minMove: 1,
			precision: undefined,
		},
	});
	mainSeries.priceFormatter().format(2);

	return new Promise(resolve => {
		requestAnimationFrame(resolve);
	});
}
