#!/usr/bin/env python3
"""Доступ к отдельным глифам: нужно, чтобы резать и подменять буквы в логотипе."""
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

_CACHE = {}


def load(path, wght=700):
    key = (path, wght)
    if key not in _CACHE:
        font = TTFont(path)
        if "fvar" in font:
            font = instancer.instantiateVariableFont(font, {"wght": wght})
        _CACHE[key] = font
    return _CACHE[key]


def metrics(path, wght=700):
    f = load(path, wght)
    os2 = f["OS/2"]
    return {
        "upem": f["head"].unitsPerEm,
        "cap": os2.sCapHeight,
        "xh": os2.sxHeight,
        "asc": os2.sTypoAscender,
    }


def stem_width(path, wght=700, ch="l"):
    """Толщина основного штриха — меряем по ширине буквы «l»."""
    f = load(path, wght)
    gs = f.getGlyphSet()
    pen = BoundsPen(gs)
    gs[f.getBestCmap()[ord(ch)]].draw(pen)
    x0, _, x1, _ = pen.bounds
    return x1 - x0


def glyphs(path, text, wght=700, scale=1.0, tracking=0.0):
    """[(символ, path-d в конечных координатах, x_left, advance)] — базовая линия y=0."""
    f = load(path, wght)
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    hmtx = f["hmtx"]
    out = []
    x = 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            raise SystemExit("нет глифа %r" % ch)
        pen = SVGPathPen(gs, ntos=lambda v: format(round(v, 2), "g"))
        gs[name].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, x * scale, 0)))
        out.append((ch, pen.getCommands(), x * scale, hmtx[name][0] * scale))
        x += hmtx[name][0] + tracking
    return out, x * scale


def bounds(path, ch, wght=700, scale=1.0):
    f = load(path, wght)
    gs = f.getGlyphSet()
    pen = BoundsPen(gs)
    gs[f.getBestCmap()[ord(ch)]].draw(pen)
    x0, y0, x1, y1 = pen.bounds
    return x0 * scale, y0 * scale, x1 * scale, y1 * scale
