#!/usr/bin/env python3
"""
photo_to_ascii_svg.py

Turns a photo into an ASCII-art portrait rendered as a standalone SVG,
similar to the "ascii.svg" trick used on some GitHub profile READMEs.

Why SVG instead of a plain <pre> block of text?
- GitHub strips <script> and most CSS from README-embedded HTML, but a
  linked/embedded SVG image renders fine and keeps crisp text at any size.
- It becomes a normal file you commit to your repo and reference with an
  <img> tag, so it shows up correctly on your profile page.

Usage:
    python3 photo_to_ascii_svg.py input.jpg output.svg \
        --cols 90 --ramp " .:-=+*#%@" --fg "#39d353" --bg "transparent"

Tweak --cols for resolution (more columns = more detail, bigger file).
Tweak --ramp for a different look (order = dark-to-light or light-to-dark,
see --invert).
"""

import argparse
from PIL import Image


def image_to_ascii_rows(path, cols, ramp, invert):
    img = Image.open(path).convert("L")  # grayscale

    # Monospace characters are taller than they are wide (~0.5-0.6 ratio),
    # so we compress rows to keep the final portrait looking proportional.
    char_aspect = 0.55
    w, h = img.size
    rows = max(1, round((h / w) * cols * char_aspect))
    img = img.resize((cols, rows))

    pixels = list(img.getdata())
    # ramp goes sparse -> dense (e.g. " .:-=+*#%@"). Dark pixels should get
    # dense characters and bright pixels sparse ones, so we map on (255-p).
    ramp_chars = ramp[::-1] if invert else ramp
    n = len(ramp_chars) - 1

    lines = []
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        line = "".join(ramp_chars[int((255 - p) / 255 * n)] for p in row_pixels)
        lines.append(line)
    return lines


def escape_xml(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def rows_to_svg(lines, font_size, fg, bg, line_height_ratio=1.0):
    cols = max(len(l) for l in lines)
    rows = len(lines)

    # Monospace advance width. 0.6em is standard for JetBrains Mono /
    # most coding monospace fonts; adjust if you swap fonts.
    char_w = font_size * 0.6
    line_h = font_size * line_height_ratio

    width = cols * char_w
    height = rows * line_h

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}">'
    )
    if bg and bg != "transparent":
        parts.append(f'<rect width="100%" height="100%" fill="{bg}"/>')
    parts.append(
        f'<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{font_size}" fill="{fg}">'
    )
    for i, line in enumerate(lines):
        y = (i + 1) * line_h - (line_h - font_size) / 2
        # Both xml:space AND the CSS white-space property are needed:
        # different renderers (GitHub's viewer, various browsers) honor
        # one or the other, and without both, runs of spaces representing
        # "blank" background pixels get collapsed to a single space,
        # shearing the whole image sideways row by row.
        parts.append(
            f'<text x="0" y="{y:.1f}" xml:space="preserve" '
            f'style="white-space:pre">{escape_xml(line)}</text>'
        )
    parts.append("</g></svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Path to source photo (jpg/png)")
    ap.add_argument("output", help="Path to write the output .svg")
    ap.add_argument("--cols", type=int, default=90, help="Character columns (detail level)")
    ap.add_argument("--ramp", default=" .:-=+*#%@", help="Characters from darkest-drawn to lightest area, or reverse with --invert")
    ap.add_argument("--invert", action="store_true", help="Flip ramp direction (use if the portrait looks like a photo negative)")
    ap.add_argument("--font-size", type=float, default=8, help="SVG font size in px")
    ap.add_argument("--fg", default="#c9d1d9", help="Text color (e.g. a hex color)")
    ap.add_argument("--bg", default="transparent", help="Background color, or 'transparent'")
    args = ap.parse_args()

    lines = image_to_ascii_rows(args.input, args.cols, args.ramp, args.invert)
    svg = rows_to_svg(lines, args.font_size, args.fg, args.bg)

    with open(args.output, "w") as f:
        f.write(svg)

    print(f"Wrote {args.output}: {len(lines)} rows x {max(len(l) for l in lines)} cols")


if __name__ == "__main__":
    main()
