# Lightweight Charts provenance

Official repository: https://github.com/tradingview/lightweight-charts

The latest stable release was verified on 2026-10-14 as v5.2.1, resolving to
b2ce010e4ad59f6556c9ed60e2b2b30feccdd2d1. The manifest records all 1,534 files from
that Git tree, not just the source or npm distribution. Each original file was
compared against its Git object before local changes. Git metadata is excluded.

`files` is the immutable upstream baseline. `modifications` records current hashes
and reasons without overwriting original hashes. Run `python studio/scripts/check_vendor.py`
from the repository root to detect missing files or unrecorded changes. New library
features must include their purpose and regression evidence. Upgrade in a separate
change, recheck the official stable release and compare every retained local change.

The debug directory has an upstream `*` ignore rule because its files were already
tracked upstream. Its local ignore file explicitly includes those original files
so the imported tree remains complete in this repository. No upstream tests are removed.

Install development dependencies with `npm ci --ignore-scripts` in the vendor root.
This avoids the upstream Git-hook installer and browser downloads. Build with
`npm run build:release`; run `npm test` and `npm run type-tests` for the non-browser
baseline. These checks passed at import (144 unit tests); browser suites were not run.

Retain LICENSE, NOTICE and TradingView attribution in distribution resources and
the interface. The complete source tree stays in Git; Python runtime packages carry
only compiled assets, version provenance and required notices.

## Local rendering changes

`types.ts`, `series-markers-square.ts` and `renderer.ts` add `triangleUp` and
`triangleDown` as actual triangular geometry with matching hit tests. Studio maps
its exported `triangle_up` / `triangle_down` shapes to these types; it does not
substitute arrowheads. Regression coverage is `studio/web/src/chart/triangle.test.ts`.
The modified tree passed the original 144 unit tests and upstream type tests.

Continuous fill geometry (including crossed and stepped boundaries), per-bar backgrounds
and exact bar-coordinate axes use public local-library primitives. Studio-owned geometry
regressions are in `chart/model.test.ts`; these remain eligible for deeper library edits
when the public primitives cannot preserve a future required semantic.

For upgrades: resolve an official stable tag to a commit; copy every Git-tree file;
record a fresh immutable baseline and tree count; reapply each documented patch; refresh
only the patch digests; run `check_vendor.py`, upstream unit/type checks and Studio
geometry tests; rebuild assets and verify their provenance. Keep the upstream LICENSE
and NOTICE verbatim and the runtime TradingView link visible. The frontend distribution
also includes `third-party-notices.txt` for other bundled runtime dependencies and fonts.

`model/price-scale.ts` bounds extra marker autoscale margins when a pane becomes short
while resizing or docking. It preserves at least two pixels and, when available, 20%
of pane height for prices, distributing the remaining extra margins proportionally.
Without this bound the drawable height can turn negative and reverse the apparent price
direction. Normal pane geometry and explicit `invertScale` remain unchanged. Regression
coverage in `chart/price-scale.test.ts` exercises the real transform at 2–800 px heights,
including round trips and intentional inversion.
