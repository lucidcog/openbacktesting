import type { HoveredItemType } from './chart-model';

/**
 * Internal hit-test priority used for hover arbitration.
 *
 * Point hits receive a special override over non-point hits. Otherwise distance
 * decides, and equal-distance non-point ties preserve the existing visual/source
 * order instead of preferring a higher numeric priority.
 */
export const enum HitTestPriority {
	/**
	 * Range-style hit such as a bar, candle, or histogram interval.
	 */
	Range = 0,
	/**
	 * Stroke-style hit such as a line segment.
	 */
	Line = 1,
	/**
	 * Point-style hit such as a marker or explicit point hover.
	 */
	Point = 2,
}

export interface InternalHitTestCandidate {
	distance: number;
	priority: HitTestPriority;
	itemType?: HoveredItemType;
	cursorStyle?: string;
	externalId?: string;
	hitTestData?: unknown;
}

export function isBetterHit(candidate: InternalHitTestCandidate, currentBest: InternalHitTestCandidate | null): boolean {
	if (currentBest === null) {
		return true;
	}

	if (candidate.priority === HitTestPriority.Point && currentBest.priority !== HitTestPriority.Point) {
		return true;
	}

	if (currentBest.priority === HitTestPriority.Point && candidate.priority !== HitTestPriority.Point) {
		return false;
	}

	if (candidate.distance !== currentBest.distance) {
		return candidate.distance < currentBest.distance;
	}

	// Preserve the existing draw/source order for equal-distance non-point ties.
	// This prevents hidden strokes from overtaking visually covering range hits.
	return false;
}
