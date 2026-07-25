#!/usr/bin/env python3
"""
Собирает офлайн-шрифты для брендбука myTravel.

Что делает:
  1. Скачивает Google Fonts CSS для Alegreya / IBM Plex Sans / IBM Plex Mono.
  2. Оставляет только нужные субсеты: latin (в нём U+02BB — oʻ, gʻ),
     latin-ext, cyrillic и cyrillic-ext (в нём Қ, Ғ, Ҳ).
  3. Скачивает woff2 в fonts/.
  4. Пишет fonts/fonts-inline.css — те же @font-face, но с base64 data: URI.
  5. Вклеивает результат в brandbook.html и components/ui-kit.html между
     маркерами /* FONTS:START */ и /* FONTS:END */.

Зачем base64: Chrome блокирует загрузку шрифтов по относительным путям
с file:// (CORS), а брендбук должен открываться двойным кликом офлайн.

Запуск:  python3 tools/build-fonts.py
Нужен только python3 + сеть. Повторный запуск идемпотентен.
"""
import base64
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
# cyrillic-ext обязателен: Қ (U+049A), Ғ (U+0492), Ҳ (U+04B2) — буквы узбекской
# кириллицы — лежат именно там, в базовом cyrillic их нет.
KEEP_SUBSETS = ("latin", "latin-ext", "cyrillic", "cyrillic-ext")
TARGETS = (ROOT / "brandbook.html", ROOT / "components" / "ui-kit.html")

CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Alegreya:wght@500..700"
    "&family=IBM+Plex+Mono:wght@400;600"
    "&family=IBM+Plex+Sans:wght@400..700"
    "&display=swap"
)
# UA современного Chrome — иначе Google отдаёт ttf вместо woff2.
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

MARK_START = "/* FONTS:START */"
MARK_END = "/* FONTS:END */"


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8")


def blocks(css: str):
    """Разбирает CSS на (subset, family, weight, url, block-text)."""
    out = []
    pattern = re.compile(r"/\* (?P<subset>[a-z-]+) \*/\s*(?P<block>@font-face \{.*?\})", re.S)
    for m in pattern.finditer(css):
        block = m.group("block")
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        family = re.search(r"font-family: '([^']+)'", block)
        weight = re.search(r"font-weight: ([\d ]+)", block)
        if not (url and family):
            continue
        out.append(
            {
                "subset": m.group("subset"),
                "family": family.group(1),
                "weight": (weight.group(1) if weight else "400").strip(),
                "url": url.group(1),
                "block": block,
            }
        )
    return out


def main() -> int:
    FONTS.mkdir(parents=True, exist_ok=True)
    print("→ Google Fonts CSS…")
    css = fetch(CSS_URL)
    (FONTS / "gf.css").write_text(css, encoding="utf-8")

    faces = [b for b in blocks(css) if b["subset"] in KEEP_SUBSETS]
    if not faces:
        print("!! не нашёл ни одного @font-face — Google изменил формат ответа", file=sys.stderr)
        return 1

    out = [
        "/* Шрифты myTravel — сгенерировано tools/build-fonts.py, не править руками. */",
        "/* Alegreya (display) + IBM Plex Sans (text) + IBM Plex Mono (цифры).   */",
        "/* Лицензия: SIL Open Font License 1.1 — см. fonts/OFL.txt              */",
    ]
    total = 0
    for f in faces:
        slug = "{}-{}-{}.woff2".format(
            f["family"].replace(" ", ""), f["weight"].replace(" ", "-"), f["subset"]
        )
        path = FONTS / slug
        if not path.exists():
            path.write_bytes(fetch(f["url"], binary=True))
        raw = path.read_bytes()
        total += len(raw)
        b64 = base64.b64encode(raw).decode("ascii")
        block = f["block"].replace(
            "url({})".format(f["url"]),
            "url(data:font/woff2;base64,{})".format(b64),
        )
        out.append("/* {} · {} · {} */".format(f["family"], f["weight"], f["subset"]))
        out.append(block)
        print("   {:52s} {:>7,} B".format(slug, len(raw)))

    inline = "\n".join(out) + "\n"
    (FONTS / "fonts-inline.css").write_text(inline, encoding="utf-8")
    print("→ fonts/fonts-inline.css: {} начертаний, {:,} B woff2".format(len(faces), total))

    for target in TARGETS:
        if not target.exists():
            continue
        html = target.read_text(encoding="utf-8")
        if MARK_START not in html or MARK_END not in html:
            print("   ~ {}: нет маркеров FONTS:START/END, пропускаю".format(target.name))
            continue
        head, rest = html.split(MARK_START, 1)
        _, tail = rest.split(MARK_END, 1)
        target.write_text(
            head + MARK_START + "\n" + inline + MARK_END + tail, encoding="utf-8"
        )
        print("   ✓ вклеено в {}".format(target.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
