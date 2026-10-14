/* global dispatchPointerAt, dispatchTargetSequence, interactivePaneElement, waitForNextFrame */

function interactionsToPerform() {
	return [];
}

class PrimitiveHitTestRenderer {
	_draw(target) {
		target.useMediaCoordinateSpace(scope => {
			const ctx = scope.context;
			ctx.save();
			const width = scope.mediaSize.width;
			const height = scope.mediaSize.height;
			const boxWidth = Math.round(width / 2);
			const boxHeight = Math.round(height / 2);
			const x = Math.round((width - boxWidth) / 2);
			const y = Math.round((height - boxHeight) / 2);

			ctx.fillStyle = 'rgba(0,0,0,0.5)';
			ctx.fillRect(x, y, boxWidth, boxHeight);
			this._hitBox = {
				x,
				y,
				height: boxHeight,
				width: boxWidth,
			};
			ctx.restore();
		});
	}

	draw(target) {
		this._draw(target);
	}

	hitTest(x, y) {
		if (
			!this._hitBox ||
			x < this._hitBox.x ||
			y < this._hitBox.y ||
			x > this._hitBox.x + this._hitBox.width ||
			y > this._hitBox.y + this._hitBox.height
		) {
			return null;
		}

		return {
			cursorStyle: 'pointer',
			externalId: 'PRIMITIVE-HIT',
			itemType: 'primitive',
		};
	}
}

function createPrimitiveHitTestPaneView() {
	const renderer = new PrimitiveHitTestRenderer();

	return {
		update() {},
		renderer: () => renderer,
		hitTest: (x, y) => renderer.hitTest(x, y),
		zOrder: () => 'normal',
	};
}

function createPrimitiveHitTest() {
	const paneView = createPrimitiveHitTestPaneView();

	return {
		updateAllViews() {
			paneView.update();
		},
		paneViews: () => [paneView],
		hitTest: (x, y) => paneView.hitTest(x, y),
	};
}

class ExplicitPointRenderer {
	constructor(withObjectId = true) {
		this._data = null;
		this._withObjectId = withObjectId;
	}

	draw(target, priceConverter) {
		if (this._data === null || this._data.visibleRange === null) {
			return;
		}

		target.useMediaCoordinateSpace(scope => {
			const ctx = scope.context;
			ctx.save();
			ctx.fillStyle = '#0ea5e9';
			for (let i = this._data.visibleRange.from; i < this._data.visibleRange.to; i++) {
				const bar = this._data.bars[i];
				const y = priceConverter(bar.originalData.value);
				if (y === null) {
					continue;
				}

				ctx.beginPath();
				ctx.arc(bar.x, y, 5, 0, Math.PI * 2);
				ctx.fill();
			}
			ctx.restore();
		});
	}

	hitTest(x, y, priceConverter) {
		if (this._data === null || this._data.visibleRange === null) {
			return null;
		}

		const middleIndex = Math.floor((this._data.visibleRange.from + this._data.visibleRange.to - 1) / 2);
		const bar = this._data.bars[middleIndex];
		const pointY = priceConverter(bar.originalData.value);
		if (pointY === null) {
			return null;
		}

		const distance = Math.hypot(x - bar.x, y - pointY);
		if (distance > 8) {
			return null;
		}

		return {
			distance,
			type: 'point',
			objectId: this._withObjectId ? 'CENTER-POINT' : undefined,
			hitTestData: {
				source: this._withObjectId ? 'explicit-custom-hit-test' : 'explicit-custom-hit-test-no-id',
			},
		};
	}

	update(data) {
		this._data = data;
	}
}

class ExplicitPointSeries {
	constructor(withObjectId = true) {
		this._renderer = new ExplicitPointRenderer(withObjectId);
	}

	priceValueBuilder(plotRow) {
		return [plotRow.value];
	}

	isWhitespace(data) {
		return data.value === undefined;
	}

	renderer() {
		return this._renderer;
	}

	update(data, options) {
		void options;
		this._renderer.update(data);
	}

	defaultOptions() {
		return {};
	}
}

class RangeRenderer {
	constructor(strokeStyle, lineWidth) {
		this._data = null;
		this._strokeStyle = strokeStyle;
		this._lineWidth = lineWidth;
	}

	draw(target, priceConverter) {
		if (this._data === null || this._data.visibleRange === null) {
			return;
		}

		target.useMediaCoordinateSpace(scope => {
			const ctx = scope.context;
			ctx.save();
			ctx.strokeStyle = this._strokeStyle;
			ctx.lineWidth = this._lineWidth;
			for (let i = this._data.visibleRange.from; i < this._data.visibleRange.to; i++) {
				const bar = this._data.bars[i];
				const top = priceConverter(bar.originalData.high);
				const bottom = priceConverter(bar.originalData.low);
				if (top === null || bottom === null) {
					continue;
				}

				ctx.beginPath();
				ctx.moveTo(bar.x, top);
				ctx.lineTo(bar.x, bottom);
				ctx.stroke();
			}
			ctx.restore();
		});
	}

	update(data) {
		this._data = data;
	}
}

class RangeSeries {
	constructor(strokeStyle, lineWidth) {
		this._renderer = new RangeRenderer(strokeStyle, lineWidth);
	}

	priceValueBuilder(plotRow) {
		return [plotRow.high, plotRow.low];
	}

	isWhitespace(data) {
		return data.high === undefined || data.low === undefined;
	}

	renderer() {
		return this._renderer;
	}

	update(data, options) {
		void options;
		this._renderer.update(data);
	}

	defaultOptions() {
		return {};
	}
}

let primitiveChart;
let primitiveSeries;
let customChart;
let explicitCustomSeries;
let explicitCustomSeriesWithoutId;
let fallbackCustomSeries;
let customPriceLineSeries;
let customPrimitiveSeries;

function beforeInteractions(container) {
	container.innerHTML = '';

	const primitiveContainer = document.createElement('div');
	primitiveContainer.style.height = '220px';
	primitiveContainer.style.marginBottom = '12px';
	container.appendChild(primitiveContainer);

	const customContainer = document.createElement('div');
	customContainer.style.height = '860px';
	container.appendChild(customContainer);

	primitiveChart = LightweightCharts.createChart(primitiveContainer, {
		rightPriceScale: { visible: false },
	});

	primitiveSeries = primitiveChart.addSeries(LightweightCharts.AreaSeries, {
		priceLineVisible: false,
		lastValueVisible: false,
	});
	primitiveSeries.setData(generateLineData());
	primitiveSeries.attachPrimitive(createPrimitiveHitTest());

	customChart = LightweightCharts.createChart(customContainer, {
		addDefaultPane: false,
		rightPriceScale: { visible: false },
	});

	const explicitPane = customChart.addPane(true);
	const explicitWithoutIdPane = customChart.addPane(true);
	const fallbackPane = customChart.addPane(true);
	const priceLinePane = customChart.addPane(true);
	const customPrimitivePane = customChart.addPane(true);

	explicitCustomSeries = customChart.addCustomSeries(new ExplicitPointSeries(), {
		priceLineVisible: false,
		lastValueVisible: false,
	}, explicitPane.paneIndex());

	explicitCustomSeriesWithoutId = customChart.addCustomSeries(new ExplicitPointSeries(false), {
		priceLineVisible: false,
		lastValueVisible: false,
	}, explicitWithoutIdPane.paneIndex());

	fallbackCustomSeries = customChart.addCustomSeries(new RangeSeries('#7c3aed', 4), {
		priceLineVisible: false,
		lastValueVisible: false,
		hitTestTolerance: 6,
	}, fallbackPane.paneIndex());

	customPriceLineSeries = customChart.addCustomSeries(new RangeSeries('#22c55e', 3), {
		lastValueVisible: false,
	}, priceLinePane.paneIndex());

	customPrimitiveSeries = customChart.addCustomSeries(new ExplicitPointSeries(), {
		priceLineVisible: false,
		lastValueVisible: false,
	}, customPrimitivePane.paneIndex());

	explicitCustomSeries.setData([
		{ time: '2024-01-01', value: 10 },
		{ time: '2024-01-02', value: 50 },
		{ time: '2024-01-03', value: 90 },
	]);
	explicitCustomSeriesWithoutId.setData([
		{ time: '2024-01-01', value: 10 },
		{ time: '2024-01-02', value: 50 },
		{ time: '2024-01-03', value: 90 },
	]);

	fallbackCustomSeries.setData([
		{ time: '2024-01-01', high: 90, low: 70 },
		{ time: '2024-01-02', high: 60, low: 40 },
		{ time: '2024-01-03', high: 30, low: 10 },
	]);

	customPriceLineSeries.setData([
		{ time: '2024-01-01', high: 30, low: 20 },
		{ time: '2024-01-02', high: 28, low: 18 },
		{ time: '2024-01-03', high: 26, low: 16 },
	]);
	customPrimitiveSeries.setData([
		{ time: '2024-01-01', value: 15 },
		{ time: '2024-01-02', value: 45 },
		{ time: '2024-01-03', value: 75 },
	]);
	customPrimitiveSeries.attachPrimitive(createPrimitiveHitTest());
	customPriceLineSeries.createPriceLine({
		price: 50,
		color: '#111827',
		lineWidth: 2,
		axisLabelVisible: false,
		title: '',
		id: 'COVERAGE-PRICE-LINE',
	});

	primitiveChart.timeScale().fitContent();
	customChart.timeScale().fitContent();

	for (const targetChart of [primitiveChart, customChart]) {
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

async function afterInteractions() {
	await waitForNextFrame();

	const primitivePane = interactivePaneElement(primitiveChart.panes()[0].getHTMLElement());
	if (primitivePane !== null) {
		dispatchPointerAt(primitivePane, primitivePane.clientWidth / 2, primitivePane.clientHeight / 2);
		await waitForNextFrame(20);
	}

	const panes = customChart.panes();
	const centerX = customChart.timeScale().logicalToCoordinate(1);
	const leftX = customChart.timeScale().logicalToCoordinate(1);
	const rightX = customChart.timeScale().logicalToCoordinate(2);
	const explicitY = explicitCustomSeries.priceToCoordinate(50);
	const explicitWithoutIdY = explicitCustomSeriesWithoutId.priceToCoordinate(50);
	const fallbackY = fallbackCustomSeries.priceToCoordinate(50);
	const priceLineY = customPriceLineSeries.priceToCoordinate(50);

	if (
		centerX !== null &&
		leftX !== null &&
		rightX !== null &&
		explicitY !== null &&
		explicitWithoutIdY !== null &&
		fallbackY !== null &&
		priceLineY !== null
	) {
		await dispatchTargetSequence([
			{ pane: interactivePaneElement(panes[0].getHTMLElement()), x: centerX, y: explicitY },
			{ pane: interactivePaneElement(panes[1].getHTMLElement()), x: centerX, y: explicitWithoutIdY },
			{ pane: interactivePaneElement(panes[2].getHTMLElement()), x: centerX + 4, y: fallbackY },
			{ pane: interactivePaneElement(panes[3].getHTMLElement()), x: (leftX + rightX) / 2, y: priceLineY },
		]);
	}

	const customPrimitivePane = interactivePaneElement(panes[4].getHTMLElement());
	if (customPrimitivePane !== null) {
		dispatchPointerAt(customPrimitivePane, customPrimitivePane.clientWidth / 2, customPrimitivePane.clientHeight / 2);
		await waitForNextFrame(20);
	}

	await waitForNextFrame(50);
}
