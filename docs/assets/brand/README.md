# OpenBacktesting brand assets

Use the outlined wordmark in the product header, documentation and project READMEs. Use the compact `OB` only for favicons and navigation that cannot accommodate the full name. Keep the original proportions and a clear area of at least half the visible letter height.

## Construction

The master uses Manrope weight 800 with native shaping and kerning, tracking of -0.015em, and optical corrections of +0.012em for `nB`, +0.008em for `kt`, and +0.005em for `st`. The compact mark uses the same weight with -0.035em tracking. The default double-storey `a` and mixed-case spelling are retained. The wordmark aspect ratio is 8.3333:1; the compact mark is 1.7333:1.

The 750 and 800 Manrope specimens and an Inter 750 control were compared at 16, 18 and 20px visible ink heights. Use at least 18px visible height in navigation (150px width), 24px in the desktop documentation header (200px width), and 36px in README artwork (300px width). Prefer the compact mark when the full name will not fit. The favicon uses a dark tile so it remains visible on both browser tab themes.

- `wordmark.svg` and `monogram.svg`: dark ink on light backgrounds.
- `wordmark-white.svg` and `monogram-white.svg`: white ink on dark backgrounds.
- `favicon.svg`: self-contained dark tile with white initials.

These files contain paths, not live text, and require no runtime fonts. Keep an accessible name in the host markup. Decorative duplicate images must have empty alternative text. Do not replace third-party attribution or sponsor artwork with these assets.

## Provenance and regeneration

[Manrope source](manrope-source.json) and [Inter comparison source](inter-source.json) record the exact upstream commit, download URLs and SHA-256 identities. Both fonts use SIL OFL 1.1; the corresponding license texts are retained here. Font binaries are not distributed with the application. Inter is used only for the comparison specimen, not the production artwork. No modified font is distributed under an upstream reserved name.

Download the font URLs recorded in the source manifests into a temporary directory as `manrope.ttf` and `inter.ttf`, then run from the repository root:

```sh
uv run scripts/generate_brand.py --fonts /path/to/fonts --specimen .verification/brand/specimen.html
```

The script verifies font hashes, shapes with HarfBuzz, instantiates the variable axes and exports deterministic path outlines with FontTools. Its isolated tool dependencies are pinned in the script; they are not application dependencies. A normal product build consumes the checked-in SVG files and needs neither the fonts nor the export tools. Review the specimen and all affected surfaces after changing the master.

Studio imports these canonical files at build time and records their source hashes in its build manifest. MkDocs publishes them under `_static/brand/` through its existing file hook. README paths refer directly to this directory. Do not edit derived build output independently.
