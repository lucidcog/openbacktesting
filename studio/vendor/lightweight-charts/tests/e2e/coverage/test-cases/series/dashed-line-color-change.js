function interactionsToPerform() {
	return [];
}

async function awaitNewFrame() {
	return new Promise(resolve => {
		requestAnimationFrame(resolve);
	});
}

let lineSeries;
let areaSeries;
let baselineSeries;

async function beforeInteractions(container) {
	const chart = LightweightCharts.createChart(container);

	const lineDataWithColors = generateLineData().map((item, index) => ({
		...item,
		color: index % 5 === 0 ? 'green' : 'purple',
	}));

	lineSeries = chart.addSeries(LightweightCharts.LineSeries, {
		lineWidth: 2,
		lineStyle: LightweightCharts.LineStyle.Dashed,
		color: '#ff0000',
	});
	lineSeries.setData(lineDataWithColors);

	await awaitNewFrame();
	lineSeries.applyOptions({ lineStyle: LightweightCharts.LineStyle.Dotted });
	await awaitNewFrame();
	lineSeries.applyOptions({ lineStyle: LightweightCharts.LineStyle.LargeDashed });
	await awaitNewFrame();
	lineSeries.applyOptions({ lineStyle: LightweightCharts.LineStyle.SparseDotted });

	areaSeries = chart.addSeries(LightweightCharts.AreaSeries, {
		lineWidth: 2,
		lineStyle: LightweightCharts.LineStyle.Dashed,
		lineColor: '#ff0000',
		topColor: 'rgba(255, 0, 0, 0.3)',
		bottomColor: 'rgba(255, 0, 0, 0.05)',
	});
	areaSeries.setData(lineDataWithColors);

	baselineSeries = chart.addSeries(LightweightCharts.BaselineSeries, {
		baseValue: { type: 'price', price: 50 },
		lineWidth: 2,
		lineStyle: LightweightCharts.LineStyle.Dashed,
	});
	baselineSeries.setData(generateLineData());

	return Promise.resolve();
}

async function afterInteractions() {
	lineSeries.applyOptions({ lineType: LightweightCharts.LineType.WithSteps });
	await awaitNewFrame();
	lineSeries.applyOptions({ lineType: LightweightCharts.LineType.Curved });
	await awaitNewFrame();
	areaSeries.applyOptions({ lineStyle: LightweightCharts.LineStyle.SparseDotted });
	await awaitNewFrame();
	baselineSeries.applyOptions({ lineStyle: LightweightCharts.LineStyle.LargeDashed });
	await awaitNewFrame();
}
