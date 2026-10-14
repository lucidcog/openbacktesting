import { Coordinate } from '../../model/coordinate';

import { BitmapShapeItemCoordinates, shapeSize } from './utils';

export function drawSquare(
	ctx: CanvasRenderingContext2D,
	coords: BitmapShapeItemCoordinates,
	size: number
): void {
	const squareSize = shapeSize('square', size);
	const halfSize = ((squareSize - 1) * coords.pixelRatio) / 2;
	const left = coords.x - halfSize;
	const top = coords.y - halfSize;

	ctx.fillRect(left, top, squareSize * coords.pixelRatio, squareSize * coords.pixelRatio);
}

export function hitTestSquare(
	centerX: Coordinate,
	centerY: Coordinate,
	size: number,
	x: Coordinate,
	y: Coordinate
): boolean {
	const squareSize = shapeSize('square', size);
	const halfSize = (squareSize - 1) / 2;
	const left = centerX - halfSize;
	const top = centerY - halfSize;

	return x >= left && x <= left + squareSize &&
		y >= top && y <= top + squareSize;
}

/** Draw an exact triangular marker; unlike an arrow it has no shaft. */
export function drawTriangle(up: boolean, ctx: CanvasRenderingContext2D, coords: BitmapShapeItemCoordinates, size: number): void {
	const half = (shapeSize('triangleUp', size) - 1) * coords.pixelRatio / 2;
	const direction = up ? 1 : -1;
	ctx.beginPath();
	ctx.moveTo(coords.x, coords.y - direction * half);
	ctx.lineTo(coords.x + half, coords.y + direction * half);
	ctx.lineTo(coords.x - half, coords.y + direction * half);
	ctx.closePath();
	ctx.fill();
}

/** Test the triangle itself, preserving the distinct up/down geometry. */
export function hitTestTriangle(up: boolean, centerX: number, centerY: number, size: number, x: number, y: number): boolean {
	const half = (shapeSize('triangleUp', size) - 1) / 2;
	const dy = (y - centerY) * (up ? 1 : -1);
	return half > 0 && dy >= -half && dy <= half && Math.abs(x - centerX) <= (dy + half) / 2;
}
