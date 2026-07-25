#!/usr/bin/env python3
"""
Растр из SVG через headless Chrome.

Специальных конвертеров (rsvg, inkscape, cairosvg) на машине нет, а Chrome есть
и рендерит SVG ровно так же, как его увидит получатель. Каждый файл открывается
на прозрачном фоне в окне точного размера, скриншот делается с deviceScaleFactor.
"""
import base64
import pathlib
import re
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def ratio(svg_text):
    m = re.search(r'viewBox="([^"]+)"', svg_text)
    if not m:
        return 1.0
    _, _, w, h = [float(v) for v in m.group(1).replace(",", " ").split()]
    return w / h if h else 1.0


def render(svg_path, out_png, width, background=None):
    svg = pathlib.Path(svg_path).read_text(encoding="utf-8")
    height = max(1, round(width / ratio(svg)))
    b64 = base64.b64encode(svg.encode()).decode()
    bg = background or "transparent"
    html = (
        "<!doctype html><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:0;background:%s}"
        "img{display:block;width:%dpx;height:%dpx}</style>"
        '<img src="data:image/svg+xml;base64,%s">' % (bg, width, height, b64)
    )
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        page = f.name
    cmd = [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--force-device-scale-factor=1",
           "--default-background-color=00000000",
           "--window-size=%d,%d" % (width, height),
           "--screenshot=%s" % out_png, "file://" + page]
    r = subprocess.run(cmd, capture_output=True)
    pathlib.Path(page).unlink(missing_ok=True)
    ok = pathlib.Path(out_png).exists()
    if not ok:
        print(r.stderr.decode()[-400:], file=sys.stderr)
    return ok


if __name__ == "__main__":
    src, dst, w = sys.argv[1], sys.argv[2], int(sys.argv[3])
    print("ок" if render(src, dst, w) else "не вышло")
