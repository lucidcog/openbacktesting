function generateData(start, step, wobble) {
	const data = [];
	const time = new Date(Date.UTC(2020, 0, 1, 0, 0, 0, 0));

	for (let i = 0; i < 80; ++i) {
		data.push({
			time: time.getTime() / 1000,
			value: start + i * step + (i % 6) * wobble,
		});

		time.setUTCDate(time.getUTCDate() + 1);
	}

	return data;
}

function runTestCase(container) {
	const chart = window.chart = LightweightCharts.createChart(container, {
		defaultVisiblePriceScaleId: 'left',
		layout: {
			background: { type: LightweightCharts.ColorType.Solid, color: '#ffffff' },
			attributionLogo: false,
		},
		grid: {
			vertLines: {
				color: '#f3f4f6',
			},
			horzLines: {
				color: '#111827',
				style: LightweightCharts.LineStyle.Solid,
			},
		},
		leftPriceScale: {
			visible: true,
			scaleMargins: {
				top: 0.08,
				bottom: 0.58,
			},
			borderColor: '#d1d4dc',
		},
		rightPriceScale: {
			visible: true,
			scaleMargins: {
				top: 0.58,
				bottom: 0.08,
			},
			borderColor: '#d1d4dc',
		},
	});

	const primarySeries = chart.addSeries(LightweightCharts.LineSeries, {
		priceScaleId: 'left',
		color: '#c62828',
		lineWidth: 2,
		lastValueVisible: false,
		priceLineVisible: false,
	});
	primarySeries.setData(generateData(100, 2.5, 1.2));

	const secondarySeries = chart.addSeries(LightweightCharts.HistogramSeries, {
		priceScaleId: 'right',
		color: '#1565c0',
		lastValueVisible: false,
		priceLineVisible: false,
	});
	secondarySeries.setData(generateData(1200, 18, 11));

	chart.timeScale().fitContent();
}
