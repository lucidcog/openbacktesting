# OpenBacktesting wordmark design research

The evidence supports an original, bold, mixed-case geometric wordmark as the strongest starting direction: TradingView's useful precedent is its controlled silhouette and spacing, while OpenBacktesting's longer name and constrained headers require independent proportions.

Research date: 2026-10-15. This is a direction study, not an approved identity or implementation. **Fact** denotes source-supported statements or direct inspection; **inference** denotes design judgment; **proposal** denotes parameters requiring a specimen test. No evidence establishes that a particular typeface will make this product feel more premium to its users.

## Evidence and constraints

### TradingView: what was actually inspected

The [official media-kit page](https://www.tradingview.com/media-kit/) links to the [downloadable asset archive](https://s3.tradingview.com/pub/TradingView-media-kit.zip). Inspection included the live page, the supplied white full-logo PNG, and both full-logo SVG sources. Archive identity: SHA-256 `c56befafbee3ed61b7cce0ccd015165fdda737aeb12cdb30dfc030c60bee2804`. Relevant paths inside it are `Logotypes/SVG/Black/full-logo-black.svg`, `Logotypes/SVG/White/full-logo-white.svg`, and `Logotypes/PNG/White/full-logo-white 1.png`. External assets were inspected temporarily, not added to the repository.

**Observed facts from those assets:**

| Property | Observation |
| --- | --- |
| Letterforms | Upright sans-serif; substantial, broadly even strokes; rounded bowls; single-storey `a` and `g`; circular `i` dots. |
| Case and spacing | `TradingView`, with capitals `T` and `V`, no word space, and close but distinct letter shapes. |
| Weight | Visually heavy; the SVG contains paths, not live text. It does not establish a font family, numeric weight, or CSS tracking value. |
| Proportions | Both full-logo SVG canvases are 755 × 129, approximately 5.85:1. This includes the symbol and canvas space. |
| Symbol relationship | Symbol sits left of the name. In the black SVG, its approximately 72.18-unit height matches the `T`'s 72.14-unit cap height; the horizontal gap to `T` is approximately 25.44 units. |
| Color | Black and white SVG/PNG families are supplied, including full, alternative, square, rounded-square, and tagline versions. |

These measurements describe one supplied lockup, not an official spacing rule. No minimum size, clear-space specification, or original wordmark font was established from the inspected materials. Website body typography cannot establish the logo font.

TradingView itself describes its symbol as a `TV` monogram built from a right angle, shared dot, and rising diagonal. That meaning belongs to its identity. **Inference:** borrow the discipline of solid shapes, monochrome operation, and optical spacing; create independent letterforms and avoid recreating that symbol. [TradingView's explanation](https://www.tradingview.com/blog/en/why-we-changed-our-logo-25638/)

### OpenBacktesting: existing surfaces

**Repository facts:** the name contains 15 characters, compared with TradingView's 11; character count alone does not predict rendered width.

- Studio uses a 48px header, a 20px Activity icon, small semibold text with tight tracking, and a subordinate `Studio` label. The full name is hidden below the `sm` breakpoint. Strategy paths and controls compete for the same row. [Studio header](../../studio/web/src/App.tsx)
- Studio already loads IBM Plex Sans at weights 400, 500, and 600. Its dense theme includes blue `#2962ff`, light background `#ffffff`, and dark background `#131722`. [Studio styles](../../studio/web/src/index.css)
- Documentation uses a separate header with the product name, `Python backtesting` subtitle, and other controls. Its system-font brand text shrinks from `.9rem` to `.7rem`, then `.65rem` on the narrowest screens. [Header template](../theme/partials/header.html), [documentation styles](../core/_static/site.css)
- The current product screenshot shows the brand within a dense working interface and TradingView attribution inside the chart. These are separate identities. [Studio screenshot](../core/_static/studio/backtest-results-light.jpg)

**Inference:** a dedicated outlined wordmark can keep the brand consistent across documentation and Studio while retaining their existing interface fonts. Increasing brand size must be tested against available header width; changing the body font is unnecessary for this task.

## Three directions, in recommendation order

These are alternative design hypotheses, not interchangeable font substitutions. The official Manrope specimen, Inter specimen, and IBM Plex type tester were visually inspected. No candidate is claimed to be TradingView's original typeface.

| Direction | Proposed construction | Reason to choose it | Principal tradeoff |
| --- | --- | --- | --- |
| **1. Geometric wordmark — recommended** | Start with Manrope 750–800; retain `OpenBacktesting` on one baseline in one color. Review the capital `O`/`B`, `nB` transition, and `kt`/`st` spacing individually. | Closest to the requested heavy geometric character, with room for an independent silhouette. | Fifteen heavy letters can become a dark strip at small sizes; reduce weight or loosen spacing for a compact master if testing requires it. |
| **2. Screen-first wordmark** | Start with Inter 700–750; use its text optical size for compact trials and display optical size for larger trials. Keep the default double-storey `a` initially. | A calmer, more neutral direction with an explicit optical-size system. | Less distinctive before custom spacing and restrained letter refinement; apparent compactness must be measured, not assumed. |
| **3. Engineering continuity** | Start with IBM Plex Sans 600 or 700; keep its recognizably different letter construction and refine spacing. Use proportional Sans, not Mono. | Preserves continuity with the current Studio typography and emphasizes a technical-tool character. | Closest to the current UI label; it needs stronger scale and spacing decisions to become an independent brand asset. |

**Font evidence:** Manrope's project describes a geometric, semi-condensed sans-serif with variable weights; Google's specimen visibly uses a double-storey `a`, unlike TradingView's inspected logo. Preserve that difference initially. Inter's official specimen documents weights 100–900, text/display optical sizes, and an optional single-storey `a` (`cv11`); that alternate is available, not mandatory. IBM's specimen distinguishes Sans from Mono and offers Semibold and Bold. [Manrope project](https://github.com/googlefonts/manrope), [Manrope specimen](https://fonts.google.com/specimen/Manrope), [Inter specimen and features](https://rsms.me/inter/), [IBM Plex specimen](https://www.ibm.com/design/language/typography/typeface/)

**Recommendation:** evaluate direction 1 first, with direction 2 as the comparison. Direction 3 is useful if continuity becomes more important than the requested visual departure. Preserve the capital `B` as the word boundary. Avoid adding a space, splitting the name over two lines, or making `Open` pale: those approaches weaken the single-name silhouette in the existing headers. These are design judgments, not measured readability findings.

## Provisional construction and scaling boundaries

All numbers below are **trial parameters**, not validated minima or TradingView specifications.

- **Spacing:** begin at native kerning. Compare overall tracking of `0`, `-0.01em`, and `-0.02em`, then adjust individual gaps. Use the compact version to reject collisions in `nB`, `ack`, `kt`, `test`, and `ing`. Do not solve width problems with horizontal scaling.
- **Header trials:** compare visible ink heights of 16, 18, and 20 CSS pixels inside the existing 48px Studio row. Measure full wordmark widths against provisional 160, 180, and 200px allocations. Keep the `Studio` descriptor separate. Select the smallest acceptable version only after inspecting actual rendering; a 20px SVG canvas does not necessarily contain 20px-tall letters.
- **Large trials:** inspect 32 and 48px ink heights for documentation introductions and README presentation. A correction that looks elegant at 48px must survive at 18px, or belong only to a separate display master.
- **Color:** establish black-on-white and white-on-dark masters first, then test the existing product blue. Do not require gradients, multiple colors, a chart line, or a cut-out detail for recognition. Keep enough counter space for the reversed rendering.
- **Responsive boundary:** below a verified width threshold, use an independently designed compact mark or the established responsive behavior. Do not squeeze the full name into a square favicon or claim an untested abbreviation is recognizable. A compact mark is a later task.
- **Acceptance:** compare every candidate at 1× and 2× pixel density, light/dark backgrounds, 100% and 200% browser zoom, and narrow documentation/Studio headers. Pass only if letters remain distinct, the full name is identifiable, and adjacent controls remain usable. Inspect the outlined export as well as live-font specimens.

## Font rights and remaining uncertainty

**Verified license facts:** Manrope, Inter, and IBM Plex publish SIL Open Font License 1.1 texts. These permit use and modification subject to their terms; redistribution of font software requires its notices and license. Plex explicitly reserves the name `Plex`. Inter's repository additionally identifies `Inter` as a reserved font name. Do not assume modified font binaries may retain upstream names. [Manrope license](https://github.com/google/fonts/blob/main/ofl/manrope/OFL.txt), [Inter license](https://github.com/rsms/inter/blob/master/LICENSE.txt), [Inter project](https://github.com/rsms/inter), [Plex license](https://github.com/IBM/plex/blob/master/LICENSE.txt)

The licenses distinguish font software from documents created using it: the latter do not inherit the OFL requirement. **Practical inference:** a fixed wordmark artwork and a redistributed modified font are different deliverables. Record the precise font release and license before production export; preserve notices if font files ship with the application. These permissions do not establish trademark clearance for a finished identity.

Still unconfirmed: TradingView's exact font and optical adjustments; the best candidate weight, final kerning, header width, minimum size, and user preference. The next decision should follow a small, actual-size comparison of directions 1 and 2, not a final logo chosen from font names alone.
