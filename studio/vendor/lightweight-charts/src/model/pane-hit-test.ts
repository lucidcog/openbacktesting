import { IPaneView } from '../views/pane/ipane-view';

import { HoveredItemType, HoveredObject } from './chart-model';
import { Coordinate } from './coordinate';
import { IDataSource, IPrimitiveHitTestSource } from './idata-source';
import { HitTestPriority, InternalHitTestCandidate, isBetterHit } from './internal-hit-test';
import { PrimitiveHoveredItem, PrimitivePaneViewZOrder } from './ipane-primitive';
import { Pane } from './pane';

export interface HitTestResult {
	source: IPrimitiveHitTestSource;
	object?: HoveredObject;
	view?: IPaneView;
	cursorStyle?: string;
	itemType?: HoveredItemType;
}

export interface HitTestPaneViewResult {
	view: IPaneView;
	candidate: InternalHitTestCandidate;
}

interface BestPrimitiveHit {
	hit: PrimitiveHoveredItem;
	candidate: InternalHitTestCandidate;
	source: IPrimitiveHitTestSource;
}

function hoveredObjectFromCandidate(candidate: InternalHitTestCandidate): HoveredObject {
	return {
		externalId: candidate.externalId,
		hitTestData: candidate.hitTestData,
	};
}

// returns true if item is above reference
function comparePrimitiveZOrder(
	item: PrimitivePaneViewZOrder,
	reference?: PrimitivePaneViewZOrder
): boolean {
	return (
		!reference ||
		(item === 'top' && reference !== 'top') ||
		(item === 'normal' && reference === 'bottom')
	);
}

function primitiveHitCandidate(hitResult: PrimitiveHoveredItem): InternalHitTestCandidate {
	return {
		distance: hitResult.distance ?? 0,
		priority: hitResult.hitTestPriority ?? (hitResult.itemType === 'marker' ? HitTestPriority.Point : HitTestPriority.Range),
		itemType: hitResult.itemType ?? 'primitive',
		cursorStyle: hitResult.cursorStyle,
		externalId: hitResult.externalId,
	};
}

function findBestPrimitiveHitTest(
	sources: readonly IPrimitiveHitTestSource[],
	x: Coordinate,
	y: Coordinate
): BestPrimitiveHit | null {
	let bestPrimitiveHit: PrimitiveHoveredItem | undefined;
	let bestPrimitiveCandidate: InternalHitTestCandidate | undefined;
	let bestHitSource: IPrimitiveHitTestSource | undefined;
	for (const source of sources) {
		const primitiveHitResults = source.primitiveHitTest?.(x, y) ?? [];
		for (const hitResult of primitiveHitResults) {
			const candidate = primitiveHitCandidate(hitResult);
			if (
				comparePrimitiveZOrder(hitResult.zOrder, bestPrimitiveHit?.zOrder) ||
				(hitResult.zOrder === bestPrimitiveHit?.zOrder && bestPrimitiveCandidate !== undefined && isBetterHit(candidate, bestPrimitiveCandidate)) ||
				(hitResult.zOrder === bestPrimitiveHit?.zOrder && bestPrimitiveCandidate === undefined)
			) {
				bestPrimitiveHit = hitResult;
				bestPrimitiveCandidate = candidate;
				bestHitSource = source;
			}
		}
	}
	if (!bestPrimitiveHit || !bestHitSource || !bestPrimitiveCandidate) {
		return null;
	}
	return {
		candidate: bestPrimitiveCandidate,
		hit: bestPrimitiveHit,
		source: bestHitSource,
	};
}

function convertPrimitiveHitResult(
	primitiveHit: BestPrimitiveHit
): HitTestResult {
	return {
		source: primitiveHit.source,
		object: hoveredObjectFromCandidate(primitiveHit.candidate),
		cursorStyle: primitiveHit.candidate.cursorStyle,
		itemType: primitiveHit.candidate.itemType ?? 'primitive',
	};
}

/**
 * Performs a hit test on a collection of pane views to determine which view and object
 * is located at a given coordinate (x, y) and returns the matching pane view and
 * hit-tested result object, or null if no match is found.
 */
function hitTestPaneView(
	paneViews: readonly IPaneView[],
	x: Coordinate,
	y: Coordinate,
	pane: Pane
): HitTestPaneViewResult | null {
	let bestResult: HitTestPaneViewResult | null = null;

	for (const paneView of paneViews) {
		// Pane-view hit tests are an internal contract, so we can trust the typed
		// InternalHitTestCandidate directly instead of probing build-mangled fields.
		let candidate = paneView.hitTest?.(x, y, pane) ?? null;

		if (candidate === null) {
			const renderer = paneView.renderer(pane);
			candidate = renderer !== null && renderer.hitTest ? renderer.hitTest(x, y) : null;
		}

		if (candidate !== null) {
			const candidateResult: HitTestPaneViewResult = {
				view: paneView,
				candidate,
			};
			if (bestResult === null || isBetterHit(candidateResult.candidate, bestResult.candidate)) {
				bestResult = candidateResult;
			}
		}
	}

	return bestResult;
}

function isDataSource(source: IPrimitiveHitTestSource): source is IDataSource {
	return (source as IDataSource).paneViews !== undefined;
}

// eslint-disable-next-line complexity
export function hitTestPane(
	pane: Pane,
	x: Coordinate,
	y: Coordinate
): HitTestResult | null {
	// Hover arbitration should use the pane's stable source order, not the temporary
	// "hovered series on top" render order, otherwise the current hovered source can
	// become sticky and keep winning equal-distance overlaps.
	const sources: IPrimitiveHitTestSource[] = [pane, ...pane.orderedSources()].reverse();
	const bestPrimitiveHit = findBestPrimitiveHitTest(sources, x, y);
	if (bestPrimitiveHit?.hit.zOrder === 'top') {
		// a primitive hit on the 'top' layer will always beat the built-in hit tests
		// (on normal layer) so we can return early here.
		return convertPrimitiveHitResult(bestPrimitiveHit);
	}

	let bestSourceHit: HitTestResult | null = null;
	let bestSourceCandidate: InternalHitTestCandidate | null = null;

	for (const source of sources) {
		if (bestPrimitiveHit && bestPrimitiveHit.source === source && bestPrimitiveHit.hit.zOrder !== 'bottom' && !bestPrimitiveHit.hit.isBackground) {
			// A foreground primitive sits above its source's built-in views and blocks all lower sources,
			// but hits from higher sources should still keep precedence.
			return bestSourceHit ?? convertPrimitiveHitResult(bestPrimitiveHit);
		}
		if (isDataSource(source)) {
			const sourceResult = hitTestPaneView(source.paneViews(pane), x, y, pane);
			if (sourceResult !== null) {
				const candidateHit: HitTestResult = {
					source,
					view: sourceResult.view,
					object: hoveredObjectFromCandidate(sourceResult.candidate),
					cursorStyle: sourceResult.candidate.cursorStyle,
					itemType: sourceResult.candidate.itemType ?? 'primitive',
				};
				if (bestSourceHit === null || isBetterHit(sourceResult.candidate, bestSourceCandidate)) {
					bestSourceHit = candidateHit;
					bestSourceCandidate = sourceResult.candidate;
				}
			}
		}
		if (bestPrimitiveHit && bestPrimitiveHit.source === source && bestPrimitiveHit.hit.zOrder !== 'bottom' && bestPrimitiveHit.hit.isBackground) {
			return bestSourceHit ?? convertPrimitiveHitResult(bestPrimitiveHit);
		}
	}
	if (bestSourceHit !== null) {
		return bestSourceHit;
	}
	if (bestPrimitiveHit?.hit) {
		// return primitive hits for the 'bottom' layer
		return convertPrimitiveHitResult(bestPrimitiveHit);
	}

	return null;
}
