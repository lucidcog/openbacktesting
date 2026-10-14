import { lowerBound, upperBound } from '../helpers/algorithms';

import { Coordinate } from '../model/coordinate';
import { HitTestPriority, InternalHitTestCandidate } from '../model/internal-hit-test';
import { TimedValue } from '../model/time-data';

export interface TimedCoordinate extends TimedValue {
	x: Coordinate;
}

interface XCoordinate {
	x: Coordinate;
}

function lowerBoundByCoordinate(item: XCoordinate, value: number): boolean {
	return item.x < value;
}

function upperBoundByCoordinate(item: XCoordinate, value: number): boolean {
	return value < item.x;
}

export function lowerBoundByX<T extends XCoordinate>(items: readonly T[], value: number, from: number, to: number): number {
	return lowerBound(items, value, lowerBoundByCoordinate, from, to);
}

export function upperBoundByX<T extends XCoordinate>(items: readonly T[], value: number, from: number, to: number): number {
	return upperBound(items, value, upperBoundByCoordinate, from, to);
}

export function hoveredSeriesHitTestResult(
	distance: number,
	priority: HitTestPriority,
	itemType: InternalHitTestCandidate['itemType']
): InternalHitTestCandidate {
	return { distance, priority, itemType };
}

export function isWithinHorizontalSweep(x: number, left: number, right: number, radius: number): boolean {
	return x >= left - radius && x <= right + radius;
}

export function distanceToSegment(
	x: number,
	y: number,
	x1: number,
	y1: number,
	x2: number,
	y2: number
): number {
	const deltaX = x2 - x1;
	const deltaY = y2 - y1;

	if (deltaX === 0 && deltaY === 0) {
		return Math.hypot(x - x1, y - y1);
	}

	const projection = ((x - x1) * deltaX + (y - y1) * deltaY) / (deltaX * deltaX + deltaY * deltaY);
	const clampedProjection = Math.max(0, Math.min(1, projection));
	const closestX = x1 + deltaX * clampedProjection;
	const closestY = y1 + deltaY * clampedProjection;

	return Math.hypot(x - closestX, y - closestY);
}

export const rangePair: [Coordinate, Coordinate] = [0 as Coordinate, 0 as Coordinate];
