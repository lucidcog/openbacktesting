import { HoveredItemType, HoveredSource, ObjectKind, SourceKind } from '../model/chart-model';
import { Pane } from '../model/pane';
import { Series } from '../model/series';
import { SeriesType } from '../model/series-options';

export interface HoveredInfoImpl {
	type: HoveredItemType;
	sourceKind: SourceKind;
	objectKind: ObjectKind;
	series?: Series<SeriesType>;
	objectId?: unknown;
	paneIndex?: number;
}

export interface HoveredEventInfoImpl {
	hoveredSeries?: Series<SeriesType>;
	hoveredObject?: string;
	hoveredInfo?: HoveredInfoImpl;
}

function hoveredTargetSourceKind(
	source: HoveredSource['source'],
	itemType: HoveredItemType
): SourceKind {
	if (source instanceof Pane) {
		return 'pane-primitive';
	}

	if (itemType === 'marker' || itemType === 'primitive') {
		return 'series-primitive';
	}

	return 'series';
}

function hoveredTargetObjectKind(
	itemType: HoveredItemType,
	objectId: unknown
): ObjectKind {
	switch (itemType) {
		case 'custom':
			return objectId !== undefined ? 'custom-object' : 'series';
		case 'price-line':
			return 'custom-price-line';
		case 'marker':
			return 'series-marker';
		case 'primitive':
			return 'primitive';
		case 'series-point':
		case 'series-line':
		case 'series-range':
		default:
			return 'series';
	}
}

export function buildHoveredEventInfo(
	hoveredSource: HoveredSource | null,
	paneIndex?: number
): HoveredEventInfoImpl {
	const hoveredSeries = hoveredSource !== null && hoveredSource.source instanceof Series
		? hoveredSource.source
		: undefined;
	const hoveredObject = hoveredSource?.object?.externalId;
	const normalizedPaneIndex = paneIndex !== undefined && paneIndex !== -1 ? paneIndex : undefined;

	if (hoveredSource === null || hoveredSource.itemType === undefined) {
		return {
			hoveredSeries,
			hoveredObject,
		};
	}

	const hoveredInfo: HoveredInfoImpl = {
		type: hoveredSource.itemType,
		sourceKind: hoveredTargetSourceKind(hoveredSource.source, hoveredSource.itemType),
		objectKind: hoveredTargetObjectKind(hoveredSource.itemType, hoveredObject),
		series: hoveredSeries,
		objectId: hoveredObject,
		paneIndex: normalizedPaneIndex,
	};

	return {
		hoveredSeries,
		hoveredObject,
		hoveredInfo,
	};
}
