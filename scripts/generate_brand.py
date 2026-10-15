# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools==4.60.1", "uharfbuzz==0.52.0"]
# ///
"""Export the reviewed brand outlines from hash-verified source fonts."""

import argparse
import hashlib
import json
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/brand"


def outline(path, text, weight, tracking, family):
    data = path.read_bytes()
    expected = json.loads((ASSETS / f"{family}-source.json").read_text())["files"][0]["sha256"]
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected {family} source font; review provenance before export")
    font = TTFont(path)
    axes = {"wght": weight}
    if family == "inter":
        axes["opsz"] = 14
    static = instantiateVariableFont(font, axes, inplace=False)
    glyphs = static.getGlyphSet()
    shaper = hb.Font(hb.Face(data))
    shaper.set_variations(axes)
    units = font["head"].unitsPerEm
    shaper.scale = (units, units)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaper, buffer, {"kern": True})
    pen = SVGPathPen(
        glyphs, ntos=lambda value: f"{value:.2f}".rstrip("0").rstrip(".") if value else "0"
    )
    bounds = BoundsPen(glyphs)
    x = 0
    # Optical corrections supplement the font's own kerning; units are em fractions.
    pairs = {"nB": 0.012, "kt": 0.008, "st": 0.005} if text == "OpenBacktesting" else {}
    order = static.getGlyphOrder()
    for index, (info, position) in enumerate(zip(buffer.glyph_infos, buffer.glyph_positions)):
        transform = (1, 0, 0, 1, x + position.x_offset, position.y_offset)
        glyphs[order[info.codepoint]].draw(TransformPen(pen, transform))
        glyphs[order[info.codepoint]].draw(TransformPen(bounds, transform))
        pair = text[index : index + 2]
        x += position.x_advance + units * (tracking + pairs.get(pair, 0))
    left, bottom, right, top = bounds.bounds
    return pen.getCommands(), (left, bottom, right, top)


def svg(path, bounds, fill, square=False):
    left, bottom, right, top = bounds
    width, height = right - left, top - bottom
    if square:
        scale = 48 / width
        transform = f"translate({(64 - width * scale) / 2:.3f} {(64 - height * scale) / 2:.3f}) scale({scale:.6f}) translate({-left:.2f} {top:.2f}) scale(1 -1)"
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#131722"/><path fill="#fff" transform="{transform}" d="{path}"/></svg>\n'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}"><path fill="{fill}" transform="translate({-left:.2f} {top:.2f}) scale(1 -1)" d="{path}"/></svg>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fonts", type=Path, required=True, help="Directory containing manrope.ttf and inter.ttf"
    )
    parser.add_argument("--specimen", type=Path, help="Optional HTML comparison sheet")
    args = parser.parse_args()
    for name, text, tracking in [
        ("wordmark", "OpenBacktesting", -0.015),
        ("monogram", "OB", -0.035),
    ]:
        path, bounds = outline(args.fonts / "manrope.ttf", text, 800, tracking, "manrope")
        for suffix, fill in [("", "#131722"), ("-white", "#ffffff")]:
            (ASSETS / f"{name}{suffix}.svg").write_text(svg(path, bounds, fill))
        if name == "monogram":
            (ASSETS / "favicon.svg").write_text(svg(path, bounds, "#fff", square=True))
        print(name, "width/height", round((bounds[2] - bounds[0]) / (bounds[3] - bounds[1]), 4))
    if args.specimen:
        rows = []
        for family, weight in [("manrope", 750), ("manrope", 800), ("inter", 750)]:
            for tracking in [0, -0.01, -0.02, -0.015]:
                path, bounds = outline(
                    args.fonts / f"{family}.ttf", "OpenBacktesting", weight, tracking, family
                )
                small = "".join(
                    f'<span style="height:{size}px">{svg(path, bounds, "#131722")}</span>'
                    for size in [16, 18, 20]
                )
                rows.append(
                    f'<section><label>{family} / {weight} / {tracking}em</label><div class="large">{svg(path, bounds, "#131722")}</div><div class="sizes">{small}</div></section>'
                )
        args.specimen.parent.mkdir(parents=True, exist_ok=True)
        args.specimen.write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8"><title>OpenBacktesting wordmark study</title><style>body{font:14px system-ui;margin:48px;color:#131722;background:#f5f5f3}h1{font-size:24px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}section{padding:24px;background:white}label{display:block;color:#787b86;margin-bottom:24px}.large{height:40px}.large svg,.sizes svg{height:100%;width:auto;display:block}.sizes{margin-top:26px;display:flex;gap:28px;align-items:center;flex-wrap:wrap}</style><h1>OpenBacktesting / wordmark study</h1><p>Visible ink heights: 40px, then 16 / 18 / 20px. Native kerning with optical pair corrections.</p><main>'
            + "".join(rows)
            + "</main></html>"
        )


if __name__ == "__main__":
    main()
