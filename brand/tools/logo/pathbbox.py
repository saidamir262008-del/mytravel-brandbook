#!/usr/bin/env python3
"""
Габариты SVG-пути без браузера.

Нужно, чтобы viewBox считался по факту, а не на глаз: именно из-за неверного
viewBox логотипы в прошлом заходе обрезались. Кривые сэмплируются — для
раскладки этого достаточно, точность порядка сотых.
"""
import math
import re

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])")


def _tokens(d):
    out = []
    for part in CMD.split(d):
        part = part.strip()
        if not part:
            continue
        if CMD.fullmatch(part):
            out.append(part)
        else:
            out.extend(float(n) for n in NUM.findall(part))
    return out


def _bezier(p0, p1, p2, p3, steps=24):
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        yield (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
               u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def _quad(p0, p1, p2, steps=18):
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        yield (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
               u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def _arc(p0, rx, ry, rot, large, sweep, p1, steps=24):
    """Эллиптическая дуга по эндпойнт-параметризации (SVG 1.1, F.6.5)."""
    if p0 == p1 or rx == 0 or ry == 0:
        yield p1
        return
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rot)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0] - p1[0]) / 2.0, (p0[1] - p1[1]) / 2.0
    x1 = cos_p * dx2 + sin_p * dy2
    y1 = -sin_p * dx2 + cos_p * dy2
    lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    coef = math.sqrt(max(num / den, 0)) * (-1 if large == sweep else 1)
    cx1, cy1 = coef * rx * y1 / ry, -coef * ry * x1 / rx
    cx = cos_p * cx1 - sin_p * cy1 + (p0[0] + p1[0]) / 2.0
    cy = sin_p * cx1 + cos_p * cy1 + (p0[1] + p1[1]) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        n = math.hypot(ux, uy) * math.hypot(vx, vy)
        a = math.acos(max(-1.0, min(1.0, dot / n))) if n else 0.0
        return -a if ux * vy - uy * vx < 0 else a

    th1 = angle(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dth = angle((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    for i in range(steps + 1):
        th = th1 + dth * i / steps
        yield (cos_p * rx * math.cos(th) - sin_p * ry * math.sin(th) + cx,
               sin_p * rx * math.cos(th) + cos_p * ry * math.sin(th) + cy)


def points(d):
    """Все опорные и сэмплированные точки пути."""
    t = _tokens(d)
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_c = None
    prev_q = None
    cmd = None
    pts = []
    while i < len(t):
        if isinstance(t[i], str):
            cmd = t[i]
            i += 1
            if cmd in "Zz":
                cur = start
                pts.append(cur)
                continue
        rel = cmd.islower()
        c = cmd.upper()

        def nxt(n):
            nonlocal i
            vals = t[i:i + n]
            i += n
            return vals

        if c == "M":
            x, y = nxt(2)
            cur = (cur[0] + x, cur[1] + y) if rel else (x, y)
            start = cur
            pts.append(cur)
            cmd = "l" if rel else "L"
            prev_c = prev_q = None
        elif c == "L":
            x, y = nxt(2)
            cur = (cur[0] + x, cur[1] + y) if rel else (x, y)
            pts.append(cur)
            prev_c = prev_q = None
        elif c == "H":
            (x,) = nxt(1)
            cur = (cur[0] + x, cur[1]) if rel else (x, cur[1])
            pts.append(cur)
            prev_c = prev_q = None
        elif c == "V":
            (y,) = nxt(1)
            cur = (cur[0], cur[1] + y) if rel else (cur[0], y)
            pts.append(cur)
            prev_c = prev_q = None
        elif c in "CS":
            if c == "C":
                x1, y1, x2, y2, x, y = nxt(6)
                p1 = (cur[0] + x1, cur[1] + y1) if rel else (x1, y1)
            else:
                x2, y2, x, y = nxt(4)
                p1 = (2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]) if prev_c else cur
            p2 = (cur[0] + x2, cur[1] + y2) if rel else (x2, y2)
            p3 = (cur[0] + x, cur[1] + y) if rel else (x, y)
            pts.extend(_bezier(cur, p1, p2, p3))
            prev_c, prev_q, cur = p2, None, p3
        elif c in "QT":
            if c == "Q":
                x1, y1, x, y = nxt(4)
                p1 = (cur[0] + x1, cur[1] + y1) if rel else (x1, y1)
            else:
                x, y = nxt(2)
                p1 = (2 * cur[0] - prev_q[0], 2 * cur[1] - prev_q[1]) if prev_q else cur
            p2 = (cur[0] + x, cur[1] + y) if rel else (x, y)
            pts.extend(_quad(cur, p1, p2))
            prev_q, prev_c, cur = p1, None, p2
        elif c == "A":
            rx, ry, rot, large, sweep, x, y = nxt(7)
            p1 = (cur[0] + x, cur[1] + y) if rel else (x, y)
            pts.extend(_arc(cur, rx, ry, rot, int(large), int(sweep), p1))
            prev_c = prev_q = None
            cur = p1
        else:
            i += 1
    return pts


def bbox(*paths, stroke=0.0):
    """Габарит одного или нескольких путей. stroke — толщина обводки."""
    pts = []
    for d in paths:
        if d:
            pts.extend(points(d))
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    half = stroke / 2.0
    return (min(xs) - half, min(ys) - half, max(xs) + half, max(ys) + half)


def viewbox(*paths, stroke=0.0, pad=0.0):
    x0, y0, x1, y1 = bbox(*paths, stroke=stroke)
    return "%.2f %.2f %.2f %.2f" % (x0 - pad, y0 - pad,
                                    (x1 - x0) + pad * 2, (y1 - y0) + pad * 2)


if __name__ == "__main__":
    import pathlib
    import re as _re
    here = pathlib.Path(__file__).resolve().parent
    src = (here.parent.parent.parent / "logo-lab" / "wordmark-flight"
           / "wordmark-flight-01.svg").read_text()
    ds = _re.findall(r'<path[^>]*?d="([^"]*)"', src)
    names = ["полоса (штрих 23)", "самолёт", "слово"]
    strokes = [23, 0, 0]
    for name, d, st in zip(names, ds, strokes):
        x0, y0, x1, y1 = bbox(d, stroke=st)
        print("%-18s x %8.2f … %8.2f   y %8.2f … %8.2f   (%.1f × %.1f)"
              % (name, x0, x1, y0, y1, x1 - x0, y1 - y0))
    x0, y0, x1, y1 = bbox(*ds, stroke=0)
    print("%-18s %s" % ("общий", viewbox(*ds, stroke=0, pad=0)))
