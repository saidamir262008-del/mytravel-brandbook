#!/usr/bin/env python3
"""
Логотип myTravel — параметрическая система.


Утверждённый вариант (wordmark-flight-01) разобран на три части и пересобран так,
что все компоновки выводятся из одних и тех же величин. Единица измерения —
капитальная высота слова, равная 100.

    слово     Schibsted Grotesk 700, cap 100, базовая линия y = 0
    полоса    прямая на y = 48, обводка 23, затем отрыв: кривая +182 по x, −100 по y
    самолёт   сидит на конце кривой, угол совпадает с касательной

viewBox каждого файла считается по фактическим габаритам (pathbbox), поэтому
ничего не обрезается — в прошлом заходе это была самая частая поломка.
"""
import pathlib
import re

import glyphs as G
import pathbbox as B

import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent          # brand/tools/logo
BRAND = HERE.parent.parent                          # brand/
PROJECT = BRAND.parent                              # корень проекта


FACE = str(HERE / "SchibstedGrotesk.ttf")
WGHT = 700
CAP = 100.0
K = CAP / G.metrics(FACE, WGHT)["cap"]

ANOR = "#a81e2d"
TUT = "#2a211c"
KAYMAK = "#fbf6ee"

SRC = PROJECT / "logo-lab" / "wordmark-flight" / "wordmark-flight-01.svg"
_paths = re.findall(r'<path[^>]*?d="([^"]*)"', SRC.read_text())
PLANE_D = _paths[1]

# --- величины системы -----------------------------------------------------
STROKE = 23.0          # толщина полосы
BASE_Y = 48.0          # полоса ниже базовой линии слова
LIFT_DX, LIFT_DY = 182.0, -100.0      # отрыв: смещение конца кривой
C1 = (72.0, 0.0)                       # контрольные точки кривой отрыва
C2 = (102.0, -34.0)
RUN_X0 = 21.3          # начало полосы (под левым штрихом «m»)
RUN_X1 = 623.81        # конец прямого участка в основном блоке
PLANE_ANCHOR = (805.81, -52.0)         # конец кривой в оригинале


TRACKING = -14.0        # найдено сверкой с утверждённым файлом


def word(cap=CAP, tracking=TRACKING):
    """Путь слова и его габарит. Базовая линия y = 0, левый край ≈ 9.8."""
    gl, adv = G.glyphs(FACE, "myTravel", WGHT, cap / G.metrics(FACE, WGHT)["cap"], tracking)
    d = "".join(g[1] for g in gl)
    return d, adv


def runway(x0=RUN_X0, x1=RUN_X1, y=BASE_Y):
    """Полоса: прямая до x1, затем отрыв. Возвращает путь и конец кривой."""
    end = (x1 + LIFT_DX, y + LIFT_DY)
    d = ("M%.2f,%.2f H%.2f C%.2f,%.2f %.2f,%.2f %.2f,%.2f"
         % (x0, y, x1, x1 + C1[0], y + C1[1], x1 + C2[0], y + C2[1], end[0], end[1]))
    return d, end


def plane(at):
    """Самолёт, посаженный на конец кривой."""
    dx = at[0] - PLANE_ANCHOR[0]
    dy = at[1] - PLANE_ANCHOR[1]
    return PLANE_D, (dx, dy)


def _g(fill, body, transform=None):
    t = ' transform="%s"' % transform if transform else ""
    return '<g fill="%s"%s>%s</g>' % (fill, t, body)


def _stroke(color, d, width=STROKE):
    return ('<path fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" '
            'd="%s"/>' % (color, width, d))


def svg(parts, box, pad=6.0, title="myTravel", extra=""):
    """Собирает файл. Начало viewBox приводится к (0, 0): Chrome неверно
    инстанцирует <symbol> с отрицательным min-y через <use>, и логотип уезжает."""
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) + pad * 2, (y1 - y0) + pad * 2
    height = 120.0
    body = ('<g transform="translate(%.2f %.2f)">%s</g>'
            % (-x0 + pad, -y0 + pad, "".join(parts)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.2f %.2f" width="%.2f" '
            'height="%.2f" role="img" aria-label="%s">%s<title>%s</title>%s</svg>\n'
            % (w, h, height * w / h, height, title, extra, title, body))


# --- компоновки -----------------------------------------------------------
def lay_primary(accent=ANOR, ink=TUT, tracking=TRACKING):
    """Основной горизонтальный блок — утверждённый вариант."""
    wd, _ = word(tracking=tracking)
    rd, end = runway()
    pd, (dx, dy) = plane(end)
    parts = [_stroke(accent, rd),
             _g(accent, '<path d="%s"/>' % pd, "translate(%.2f %.2f)" % (dx, dy)),
             _g(ink, '<path d="%s"/>' % wd)]
    box = B.bbox(rd, stroke=STROKE)
    b2 = B.bbox(pd)
    b3 = B.bbox(wd)
    box = (min(box[0], b2[0] + dx, b3[0]), min(box[1], b2[1] + dy, b3[1]),
           max(box[2], b2[2] + dx, b3[2]), max(box[3], b2[3] + dy, b3[3]))
    return parts, box


def lay_plaque(fg=KAYMAK, bg=ANOR, pad_x=64.0, pad_y=52.0, radius=34.0, uid="plaque"):
    """Блок в гранатовой плите: для аватарок, обложек и вывески.
    Плита — не декор: она держит логотип на пёстром фоне, где выворотка теряется.

    В монохроме (fg == bg) логотип не закрашивается вторым цветом, а вырезается
    из плиты маской — иначе файл печатается сплошным прямоугольником.
    """
    parts, box = lay_primary(fg, fg)
    x0, y0, x1, y1 = box
    rx, ry = x0 - pad_x, y0 - pad_y
    rw, rh = (x1 - x0) + pad_x * 2, (y1 - y0) + pad_y * 2
    if fg == bg:
        mask = ('<mask id="%s-cut" maskUnits="userSpaceOnUse" x="%.2f" y="%.2f" '
                'width="%.2f" height="%.2f">'
                '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="#fff"/>'
                '<g fill="#000" stroke="#000">%s</g></mask>'
                % (uid, rx, ry, rw, rh, rx, ry, rw, rh, radius,
                   "".join(parts).replace(fg, "#000")))
        plate = ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" '
                 'fill="%s" mask="url(#%s-cut)"/>' % (rx, ry, rw, rh, radius, bg, uid))
        return [mask, plate], (rx, ry, x1 + pad_x, y1 + pad_y)
    rect = ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s"/>'
            % (rx, ry, rw, rh, radius, bg))
    return [rect] + parts, (rx, ry, x1 + pad_x, y1 + pad_y)


def lay_stacked(accent=ANOR, ink=TUT):
    """Слово, под ним полоса с поздним отрывом: блок втрое компактнее основного.
    Отрыв уведён правее конца слова, чтобы самолёт не наезжал на буквы."""
    wd, _ = word()
    rd, end = runway(x0=12.0, x1=520.0, y=104.0)
    pd, (dx, dy) = plane(end)
    parts = [_stroke(accent, rd),
             _g(accent, '<path d="%s"/>' % pd, "translate(%.2f %.2f)" % (dx, dy)),
             _g(ink, '<path d="%s"/>' % wd)]
    return parts, _union(rd, STROKE, (pd, dx, dy), wd)


def lay_vertical(accent=ANOR, ink=TUT):
    """Приём сверху, слово под ним по центру. Для квадратных мест и вывески."""
    wd, adv = word()
    wb = B.bbox(wd)
    mark_parts, mb = lay_mark(accent)
    mw, mh = mb[2] - mb[0], mb[3] - mb[1]
    target_w = (wb[2] - wb[0]) * 0.62
    s = target_w / mw
    gap = 46.0
    tx = wb[0] + ((wb[2] - wb[0]) - target_w) / 2 - mb[0] * s
    ty = wb[1] - gap - mb[3] * s
    parts = ['<g transform="translate(%.2f %.2f) scale(%.4f)">%s</g>'
             % (tx, ty, s, "".join(mark_parts)),
             _g(ink, '<path d="%s"/>' % wd)]
    box = (min(wb[0], mb[0] * s + tx), mb[1] * s + ty,
           max(wb[2], mb[2] * s + tx), wb[3])
    return parts, box


def lay_micro(accent=ANOR, ink=TUT, plane_scale=1.24, stroke=30.0):
    """Версия для 18–24 px: полоса толще, самолёт крупнее.
    Самолёт масштабируется вокруг своей опорной точки — конца кривой,
    иначе масштаб уводит его в сторону."""
    wd, _ = word()
    rd, end = runway(x1=548.0, y=52.0)
    parts = [_stroke(accent, rd, width=stroke),
             '<g fill="%s" transform="translate(%.2f %.2f) scale(%.3f) translate(%.2f %.2f)">'
             '<path d="%s"/></g>'
             % (accent, end[0], end[1], plane_scale, -PLANE_ANCHOR[0], -PLANE_ANCHOR[1],
                PLANE_D),
             _g(ink, '<path d="%s"/>' % wd)]
    pb = B.bbox(PLANE_D)
    plane_box = (end[0] + (pb[0] - PLANE_ANCHOR[0]) * plane_scale,
                 end[1] + (pb[1] - PLANE_ANCHOR[1]) * plane_scale,
                 end[0] + (pb[2] - PLANE_ANCHOR[0]) * plane_scale,
                 end[1] + (pb[3] - PLANE_ANCHOR[1]) * plane_scale)
    rb = B.bbox(rd, stroke=stroke)
    wb = B.bbox(wd)
    return parts, (min(rb[0], plane_box[0], wb[0]), min(rb[1], plane_box[1], wb[1]),
                   max(rb[2], plane_box[2], wb[2]), max(rb[3], plane_box[3], wb[3]))


def lay_mark(accent=ANOR, stroke=STROKE, plane_scale=1.0):
    """Только приём: короткая полоса и самолёт. Для плитки и мелких мест.
    В favicon 16–32 px обычная толщина не работает: самолёт схлопывается
    и остаётся голая линия — там берётся жирный вариант."""
    rd, end = runway(x0=0.0, x1=150.0, y=BASE_Y)
    if plane_scale == 1.0:
        pd, (dx, dy) = plane(end)
        plane_g = _g(accent, '<path d="%s"/>' % pd, "translate(%.2f %.2f)" % (dx, dy))
        pb = B.bbox(pd)
        pbox = (pb[0] + dx, pb[1] + dy, pb[2] + dx, pb[3] + dy)
    else:
        plane_g = ('<g fill="%s" transform="translate(%.2f %.2f) scale(%.3f) '
                   'translate(%.2f %.2f)"><path d="%s"/></g>'
                   % (accent, end[0], end[1], plane_scale,
                      -PLANE_ANCHOR[0], -PLANE_ANCHOR[1], PLANE_D))
        pb = B.bbox(PLANE_D)
        pbox = tuple(end[i % 2] + (pb[i] - PLANE_ANCHOR[i % 2]) * plane_scale
                     for i in range(4))
    parts = [_stroke(accent, rd, width=stroke), plane_g]
    rb = B.bbox(rd, stroke=stroke)
    return parts, (min(rb[0], pbox[0]), min(rb[1], pbox[1]),
                   max(rb[2], pbox[2]), max(rb[3], pbox[3]))


def lay_wordmark(ink=TUT):
    wd, _ = word()
    return [_g(ink, '<path d="%s"/>' % wd)], B.bbox(wd)


def lay_descriptor(accent=ANOR, ink=TUT, muted=None):
    """Блок с дескриптором под ним, набранным IBM Plex Sans."""
    parts, box = lay_primary(accent, ink)
    if muted is None:
        # на тёмном фоне приглушённый серый пропадает — светлеем
        muted = "#c2b6a6" if ink == KAYMAK else "#665d53"
    gl, adv = G.glyphs(str(HERE / "IBMPlexSans.ttf"), "Билеты · отели · туры · виза", 500,
                       28.0 / G.metrics(str(HERE / "IBMPlexSans.ttf"), 500)["cap"], 0)
    dd = "".join(g[1] for g in gl)
    y = box[3] + 52
    parts.append(_g(muted, '<path d="%s"/>' % dd, "translate(9.8 %.2f)" % y))
    db = B.bbox(dd)
    box = (min(box[0], db[0] + 9.8), box[1],
           max(box[2], db[2] + 9.8), max(box[3], db[3] + y))
    return parts, box


def _union(stroke_d, stroke_w, *others):
    boxes = [B.bbox(stroke_d, stroke=stroke_w)]
    for o in others:
        if isinstance(o, tuple):
            d, dx, dy = o
            b = B.bbox(d)
            boxes.append((b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy))
        else:
            boxes.append(B.bbox(o))
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def tile(size=512, radius=None, bg=ANOR, fg=KAYMAK, inset=0.62,
         stroke=STROKE, plane_scale=1.0):
    """Плитка приложения: приём по центру гранатового поля."""
    parts, box = lay_mark(fg, stroke=stroke, plane_scale=plane_scale)
    w, h = box[2] - box[0], box[3] - box[1]
    s = size * inset / max(w, h)
    tx = size / 2 - (box[0] + w / 2) * s
    ty = size / 2 - (box[1] + h / 2) * s
    body = ('<rect width="%d" height="%d"%s fill="%s"/>'
            '<g transform="translate(%.2f %.2f) scale(%.4f)">%s</g>'
            % (size, size, ' rx="%d"' % radius if radius else "", bg, tx, ty, s,
               "".join(parts)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
            'height="%d" role="img" aria-label="myTravel"><title>myTravel</title>%s</svg>\n'
            % (size, size, size, size, body))
