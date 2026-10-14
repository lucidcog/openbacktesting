import { InternalHitTestCandidate } from '../../model/internal-hit-test';
import { Pane } from '../../model/pane';
import { IPaneRenderer } from '../../renderers/ipane-renderer';

export interface IPaneView {
	renderer(pane: Pane, addAnchors?: boolean): IPaneRenderer | null;
	hitTest?(x: number, y: number, pane?: Pane): InternalHitTestCandidate | null;
}
