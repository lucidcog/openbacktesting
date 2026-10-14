import { Coordinate } from '../model/coordinate';
import { HitTestPriority, InternalHitTestCandidate } from '../model/internal-hit-test';
import { SeriesItemsIndexesRange } from '../model/time-data';

import { hoveredSeriesHitTestResult, lowerBoundByX, rangePair, TimedCoordinate, upperBoundByX } from './hit-test-common';

function slotStart(
	item: TimedCoordinate,
	previousItem: TimedCoordinate | undefined,
	barSpacing: number
): number {
	if (previousItem === undefined || previousItem.time !== item.time - 1) {
		return item.x - barSpacing / 2;
	}

	return (previousItem.x + item.x) / 2;
}

function slotEnd(
	item: TimedCoordinate,
	nextItem: TimedCoordinate | undefined,
	barSpacing: number
): number {
	if (nextItem === undefined || nextItem.time !== item.time + 1) {
		return item.x + barSpacing / 2;
	}

	return (item.x + nextItem.x) / 2;
}

// eslint-disable-next-line max-params, complexity
export function hitTestSeriesRange<TItem extends TimedCoordinate>(
	items: readonly TItem[],
	visibleRange: SeriesItemsIndexesRange | null,
	x: Coordinate,
	y: Coordinate,
	barSpacing: number,
	hitTestTolerance: number,
	rangeProvider: (item: TItem, out: [Coordinate, Coordinate]) => void
): InternalHitTestCandidate | null {
	if (visibleRange === null || visibleRange.from >= visibleRange.to || items.length === 0) {
		return null;
	}

	const horizontalRadius = barSpacing / 2 + hitTestTolerance;
	const candidateFrom = lowerBoundByX(items, x - horizontalRadius, visibleRange.from, visibleRange.to);
	const candidateTo = upperBoundByX(items, x + horizontalRadius, candidateFrom, visibleRange.to);
	if (candidateFrom >= candidateTo) {
		return null;
	}

	let minDistance = Number.POSITIVE_INFINITY;

	for (let itemIndex = candidateFrom; itemIndex < candidateTo; itemIndex++) {
		const item = items[itemIndex];
		const previousItem = itemIndex > visibleRange.from ? items[itemIndex - 1] : undefined;
		const nextItem = itemIndex < visibleRange.to - 1 ? items[itemIndex + 1] : undefined;
		const leftBoundary = slotStart(item, previousItem, barSpacing) - hitTestTolerance;
		const rightBoundary = slotEnd(item, nextItem, barSpacing) + hitTestTolerance;

		if (x < leftBoundary || x > rightBoundary) {
			continue;
		}

		rangeProvider(item, rangePair);
		const rangeStart = rangePair[0];
		const rangeEnd = rangePair[1];
		const actualTop = Math.min(rangeStart, rangeEnd);
		const actualBottom = Math.max(rangeStart, rangeEnd);
		const top = actualTop - hitTestTolerance;
		const bottom = actualBottom + hitTestTolerance;

		if (y >= actualTop && y <= actualBottom) {
			minDistance = Math.min(minDistance, 0);
			continue;
		}

		if (y >= top && y <= bottom) {
			const distance = Math.min(Math.abs(y - actualTop), Math.abs(actualBottom - y));
			minDistance = Math.min(minDistance, distance);
		}
	}

	return Number.isFinite(minDistance) ? hoveredSeriesHitTestResult(minDistance, HitTestPriority.Range, 'series-range') : null;
}
