#!/usr/bin/env python3
"""
Собирает файлы логотипа myTravel в /logo.

Знак («abr-лозенга») задан вручную координатами на сетке 32×32: ромб иката,
разрезанный по вертикали и сдвинутый — как сбой узора в настоящей абрбандӣ.
Словесный знак переведён в кривые из Alegreya 700 (OFL), поэтому SVG не зависит
от установленного шрифта.

Скрипт нужен ТОЛЬКО для перегенерации. Готовые SVG уже лежат в /logo и
самодостаточны. Для запуска нужен fontTools и файл шрифта:

    python3 -m venv venv && ./venv/bin/pip install fonttools brotli
    curl -sLo Alegreya.ttf \
      "https://raw.githubusercontent.com/google/fonts/main/ofl/alegreya/Alegreya%5Bwght%5D.ttf"
    ./venv/bin/python tools/build-logo.py Alegreya.ttf
"""
import pathlib
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

OUT = pathlib.Path(__file__).resolve().parent.parent / "logo"

ANOR = "#a81e2d"
TUT = "#2a211c"
KAYMAK = "#fbf6ee"
ANOR_DARK = "#6b121b"

# --- Знак -----------------------------------------------------------------
# Базовая лозенга: x 5..27, y 2..30, ступень 3×4. Половины разъезжаются на ±1
# по вертикали и на ±1 по горизонтали, шов между ними — 2 единицы.
MARK_L = "M15 3h-3v4h-3v4h-3v4h-2v4h2v4h3v4h3v4h3z"
MARK_R = "M17 1h3v4h3v4h3v4h2v4h-2v4h-3v4h-3v4h-3z"
MARK_BOX = (4, 1, 24, 30)  # x, y, width, height

# Вариант для мелких размеров (≤24px) и для плитки: шов шире вдвое,
# иначе на 16px он затекает и знак читается как цельное пятно.
MARK_L_WIDE = "M14 3h-3v4h-3v4h-3v4h-2v4h2v4h3v4h3v4h3z"
MARK_R_WIDE = "M18 1h3v4h3v4h3v4h2v4h-2v4h-3v4h-3v4h-3z"
MARK_BOX_WIDE = (3, 1, 26, 30)

# Зуб abr-кромки — та же ступень 3×2, что в tokens.css.
ABR_TOOTH = "M0 8V6h3V4h3V2h3V0h3v2h3v2h3v2h3v2z"


def mark_group(fill, scale, tx, ty, wide=False):
    left, right = (MARK_L_WIDE, MARK_R_WIDE) if wide else (MARK_L, MARK_R)
    bx, by, _, _ = MARK_BOX_WIDE if wide else MARK_BOX
    return (
        '<g fill="{f}" transform="translate({tx:.2f} {ty:.2f}) scale({s:.5f}) '
        'translate({mx} {my})"><path d="{a}"/><path d="{b}"/></g>'
    ).format(f=fill, tx=tx, ty=ty, s=scale, mx=-bx, my=-by, a=left, b=right)


def mark_size(scale, wide=False):
    _, _, w, h = MARK_BOX_WIDE if wide else MARK_BOX
    return w * scale, h * scale


# --- Словесный знак -------------------------------------------------------
def wordmark(font_path, text="myTravel", wght=700, cap_target=100.0):
    font = TTFont(font_path)
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": wght})
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    hmtx = font["hmtx"]
    cap = font["OS/2"].sCapHeight
    scale = cap_target / cap
    x = 0.0
    out = []
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise SystemExit("в шрифте нет глифа %r" % ch)
        pen = SVGPathPen(glyphs, ntos=lambda v: format(round(v, 2), "g"))
        glyphs[gname].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, x * scale, 0)))
        if pen.getCommands():
            out.append(pen.getCommands())
        x += hmtx[gname][0]
    return "".join(out), x * scale


HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" '
    'width="{w:.2f}" height="{h:.2f}" role="img" aria-label="{alt}">'
    "<title>{alt}</title>"
    "<!-- myTravel. Знак: abr-лозенга. Текст: Alegreya 700 в кривых (OFL). "
    "Не растягивать, не менять пропорции. Правила: docs/usage-rules.md -->"
)


def write(name, body):
    (OUT / name).write_text(body + "</svg>\n", encoding="utf-8")
    print("   ✓ logo/%s  %6d B" % (name, len(body)))


def lockup_horizontal(wm, adv, cap, mark_h, gap, mk_fill, wm_fill, alt="myTravel"):
    k = cap / 100.0
    wm_w = adv * k
    mk_s = mark_h / MARK_BOX[3]
    mk_w, _ = mark_size(mk_s)
    h = mark_h
    baseline = (h + cap) / 2
    w = mk_w + gap + wm_w
    return (
        HEAD.format(w=w, h=h, alt=alt)
        + mark_group(mk_fill, mk_s, 0, 0)
        + '<g fill="{f}" transform="translate({tx:.2f} {by:.2f}) scale({k:.5f})">'
        '<path d="{d}"/></g>'.format(f=wm_fill, tx=mk_w + gap, by=baseline, k=k, d=wm)
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    wm, adv = wordmark(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    print("→ словесный знак: %d символов пути, ширина %.1f при cap 100" % (len(wm), adv))

    # 1. Основной — знак 46, кегль cap 28, просвет 16.
    write("logo-primary.svg", lockup_horizontal(wm, adv, 28, 46, 16, ANOR, TUT))

    # 2. Инверсия — для тёмного фона и фото.
    write("logo-inverse.svg", lockup_horizontal(wm, adv, 28, 46, 16, KAYMAK, KAYMAK))

    # 3. Монохром — один цвет через currentColor: печать, тиснение, штамп.
    write("logo-mono.svg", lockup_horizontal(wm, adv, 28, 46, 16, "currentColor", "currentColor"))

    # 4. Компактный горизонтальный — для шапок и узких мест.
    write("logo-horizontal.svg", lockup_horizontal(wm, adv, 24, 34, 10, ANOR, TUT))

    # 5. Вертикальный — знак сверху, слово по центру снизу.
    cap, mark_h, gap = 26, 56, 14
    k = cap / 100.0
    wm_w = adv * k
    mk_s = mark_h / MARK_BOX[3]
    mk_w, _ = mark_size(mk_s)
    w = max(mk_w, wm_w)
    desc = 26 * k
    h = mark_h + gap + cap + desc
    body = (
        HEAD.format(w=w, h=h, alt="myTravel")
        + mark_group(ANOR, mk_s, (w - mk_w) / 2, 0)
        + '<g fill="{f}" transform="translate({tx:.2f} {by:.2f}) scale({k:.5f})">'
        '<path d="{d}"/></g>'.format(
            f=TUT, tx=(w - wm_w) / 2, by=mark_h + gap + cap, k=k, d=wm
        )
    )
    write("logo-vertical.svg", body)

    # 6. Только знак, 32×32, широкий шов — работает и как 24px-иконка.
    s = 30 / MARK_BOX_WIDE[3]
    mw, mh = mark_size(s, wide=True)
    body = HEAD.format(w=32, h=32, alt="myTravel") + mark_group(
        ANOR, s, (32 - mw) / 2, (32 - mh) / 2, wide=True
    )
    write("logo-mark.svg", body)

    # 7. Favicon — плитка со скруглением 6, знак 22 по высоте, шов широкий.
    s = 22 / MARK_BOX_WIDE[3]
    mw, mh = mark_size(s, wide=True)
    body = (
        HEAD.format(w=32, h=32, alt="myTravel")
        + '<rect width="32" height="32" rx="6" fill="%s"/>' % ANOR
        + mark_group(KAYMAK, s, (32 - mw) / 2, (32 - mh) / 2, wide=True)
    )
    write("logo-favicon.svg", body)

    # 8. Иконка приложения 1024: без скругления (маску ставит система),
    #    знак в центральной безопасной зоне + abr-кромка по низу.
    size = 1024
    s = 470 / MARK_BOX_WIDE[3]
    mw, mh = mark_size(s, wide=True)
    tooth_s = 8.0  # плитка 24×8 → 192×64
    teeth = "".join(
        '<g transform="translate({x} {y}) scale({s})"><path d="{d}"/></g>'.format(
            x=i * 24 * tooth_s, y=size - 8 * tooth_s, s=tooth_s, d=ABR_TOOTH
        )
        for i in range(int(size / (24 * tooth_s)) + 1)
    )
    body = (
        HEAD.format(w=size, h=size, alt="myTravel")
        + '<rect width="1024" height="1024" fill="%s"/>' % ANOR
        + '<g fill="%s">%s</g>' % (ANOR_DARK, teeth)
        + mark_group(KAYMAK, s, (size - mw) / 2, (size - mh) / 2 - 24, wide=True)
    )
    write("app-icon.svg", body)


if __name__ == "__main__":
    main()
