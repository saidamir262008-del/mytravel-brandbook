#!/usr/bin/env python3
"""
Делает brandbook.html самодостаточным.

Вклеивает между маркерами:
  /* TOKENS:START */ … /* TOKENS:END */   — содержимое tokens/tokens.css
  <!-- LOGOS:START --> … <!-- LOGOS:END --> — все SVG из logo/ как <symbol>
  <!-- ICONS:START --> … <!-- ICONS:END --> — все SVG из icons/ как <symbol> + сетка

Шрифты вклеивает отдельный скрипт tools/build-fonts.py (ему нужна сеть).
Этому скрипту сеть не нужна — только стандартная библиотека python3.

Запуск:  python3 tools/build-brandbook.py
Идемпотентен: гоняй сколько угодно раз после правки токенов, логотипа и иконок.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOK = ROOT / "brandbook.html"

LOGO_ORDER = [
    ("logo-primary", "Основной"),
    ("logo-inverse", "Инверсия"),
    ("logo-mono", "Монохром"),
    ("logo-horizontal", "Компактный"),
    ("logo-vertical", "Вертикальный"),
    ("logo-mark", "Знак"),
    ("logo-favicon", "Favicon"),
    ("app-icon", "Иконка приложения"),
]

CAT_ORDER = [
    "cat-flights", "cat-hotels", "cat-cruises", "cat-tours", "cat-car-rental",
    "cat-apartments", "cat-transfer", "cat-visa", "cat-insurance",
    "cat-attractions", "cat-bus-rail", "cat-cargo", "cat-concerts",
    "cat-concert-tours",
]
UI_ORDER = [
    "ui-search", "ui-calendar", "ui-passenger", "ui-filter", "ui-back",
    "ui-close", "ui-check", "ui-alert", "ui-info", "ui-download",
    "ui-support", "ui-wallet",
]


# Наследуемые свойства обводки живут на корневом <svg>. При переносе
# внутренностей в <symbol> их нужно перенести туда же, иначе штриховая
# иконка превращается в чёрное пятно (fill по умолчанию — чёрный).
INHERITED = ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin")


def root_attrs(text):
    root = re.search(r"<svg([^>]*)>", text)
    if not root:
        return ""
    out = []
    for name in INHERITED:
        m = re.search(r'\b%s="([^"]*)"' % re.escape(name), root.group(1))
        if m:
            out.append('%s="%s"' % (name, m.group(1)))
    return (" " + " ".join(out)) if out else ""


def inner_svg(text):
    """Возвращает (viewBox, внутренности) SVG-файла без корневого тега."""
    vb = re.search(r'viewBox="([^"]+)"', text)
    body = re.sub(r"^.*?<svg[^>]*>", "", text, count=1, flags=re.S)
    body = re.sub(r"</svg>\s*$", "", body, flags=re.S)
    body = re.sub(r"<title>.*?</title>", "", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return (vb.group(1) if vb else "0 0 24 24"), body.strip()


def replace(html, start, end, payload):
    if start not in html or end not in html:
        print("!! нет маркеров %s / %s" % (start, end), file=sys.stderr)
        return html, False
    head, rest = html.split(start, 1)
    _, tail = rest.split(end, 1)
    return head + start + "\n" + payload + "\n" + end + tail, True


def main() -> int:
    if not BOOK.exists():
        print("!! нет brandbook.html", file=sys.stderr)
        return 1
    html = BOOK.read_text(encoding="utf-8")
    ok = True

    # --- токены ---
    tokens = (ROOT / "tokens" / "tokens.css").read_text(encoding="utf-8")
    html, done = replace(html, "/* TOKENS:START */", "/* TOKENS:END */", tokens)
    ok &= done
    print("→ токены: %d символов" % len(tokens))

    # --- логотипы ---
    symbols, ratios, viewboxes = [], [], {}
    for slug, _ in LOGO_ORDER:
        path = ROOT / "logo" / ("%s.svg" % slug)
        if not path.exists():
            print("   ~ нет logo/%s.svg" % slug)
            continue
        raw = path.read_text(encoding="utf-8")
        vb, body = inner_svg(raw)
        symbols.append(
            '<symbol id="%s" viewBox="%s"%s>%s</symbol>'
            % (slug, vb, root_attrs(raw), body)
        )
        _, _, w, h = [float(v) for v in vb.split()]
        ratios.append(".%s{aspect-ratio:%.4f}" % (slug, w / h))
        viewboxes[slug] = vb
    payload = (
        '<svg width="0" height="0" aria-hidden="true" style="position:absolute">'
        + "".join(symbols)
        + "</svg>\n<style>"
        + "".join(ratios)
        + "</style>"
    )
    html, done = replace(html, "<!-- LOGOS:START -->", "<!-- LOGOS:END -->", payload)
    ok &= done
    print("→ логотипы: %d символов-symbol" % len(symbols))

    # Внешнему <svg> нужен собственный viewBox: без него у элемента нет
    # внутренних пропорций, width:auto растягивает его на всю ширину контейнера
    # и ломает раскладку. viewBox берём у соответствующего symbol.
    fixed = 0
    for slug, vb in viewboxes.items():
        pattern = re.compile(r'<svg (?![^>]*viewBox)([^>]*\bclass="[^"]*\b%s\b[^"]*")' % re.escape(slug))
        html, n = pattern.subn(r'<svg viewBox="%s" \1' % vb, html)
        fixed += n
    print("   ✓ viewBox проставлен у %d внешних <svg>" % fixed)

    # --- иконки ---
    icon_dir = ROOT / "icons"
    found = {p.stem: p for p in icon_dir.glob("*.svg")} if icon_dir.exists() else {}
    missing = [s for s in CAT_ORDER + UI_ORDER if s not in found]
    if missing:
        print("   ~ иконки ещё не готовы: %s" % ", ".join(missing))

    def grid(slugs, titles):
        cells, syms = [], []
        for slug in slugs:
            if slug not in found:
                continue
            text = found[slug].read_text(encoding="utf-8")
            vb, body = inner_svg(text)
            title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S)
            label = title.group(1).strip() if title else slug
            syms.append(
                '<symbol id="i-%s" viewBox="%s"%s>%s</symbol>'
                % (slug, vb, root_attrs(text), body)
            )
            cells.append(
                '<li class="icon-cell"><svg class="icon icon-24" aria-hidden="true">'
                '<use href="#i-%s"/></svg>'
                '<svg class="icon icon-16" aria-hidden="true"><use href="#i-%s"/></svg>'
                '<span class="icon-name">%s</span><code>%s</code></li>'
                % (slug, slug, label, slug)
            )
        titles.append((len(cells),))
        return syms, cells

    counters = []
    cat_syms, cat_cells = grid(CAT_ORDER, counters)
    ui_syms, ui_cells = grid(UI_ORDER, counters)
    payload = (
        '<svg width="0" height="0" aria-hidden="true" style="position:absolute">'
        + "".join(cat_syms + ui_syms)
        + "</svg>"
        + '<h3 class="h3">14 категорий</h3><ul class="icon-grid">'
        + "".join(cat_cells)
        + '</ul><h3 class="h3">12 интерфейсных</h3><ul class="icon-grid">'
        + "".join(ui_cells)
        + "</ul>"
    )
    html, done = replace(html, "<!-- ICONS:START -->", "<!-- ICONS:END -->", payload)
    ok &= done
    print("→ иконки: %d категорий + %d интерфейсных" % (len(cat_cells), len(ui_cells)))

    BOOK.write_text(html, encoding="utf-8")
    print("✓ brandbook.html пересобран (%d КБ)" % (len(html) // 1024))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
