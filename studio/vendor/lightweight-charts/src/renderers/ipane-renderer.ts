import { CanvasRenderingTarget2D } from 'fancy-canvas';

import { Coordinate } from '../model/coordinate';
import { InternalHitTestCandidate } from '../model/internal-hit-test';

export interface IPaneRenderer {
	draw(target: CanvasRenderingTarget2D, isHovered: boolean, hitTestData?: unknown): void;
	drawBackground?(target: CanvasRenderingTarget2D, isHovered: boolean, hitTestData?: unknown): void;
	hitTest?(x: Coordinate, y: Coordinate): InternalHitTestCandidate | null;
}
