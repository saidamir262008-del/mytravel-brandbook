#!/usr/bin/env python3
"""
Контрасты палитры myTravel по WCAG 2.1.

На этот скрипт ссылается docs/accessibility.md: все числа в нём посчитаны здесь,
и пересчитать их можно в любой момент — палитра читается прямо из tokens.css,
поэтому разойтись с ней таблицы не могут.

    python3 tools/contrast.py            # ключевые пары обеих тем
    python3 tools/contrast.py --all      # весь текстовый ряд на всех поверхностях
    python3 tools/contrast.py '#a81e2d' '#fbf6ee'   # одна пара
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "tokens" / "tokens.css"

AA_LARGE, AA, AAA = 3.0, 4.5, 7.0


def _linear(channel):
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour):
    h = hex_colour.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def verdict(value, large=False):
    if value >= AAA:
        return "AAA"
    if value >= AA:
        return "AA"
    if value >= AA_LARGE:
        return "AA Large" if large else "AA Large (только крупный текст)"
    return "FAIL"


def palette():
    """Читает токены из tokens.css. Светлая тема — :root, тёмная — переопределения."""
    if not TOKENS.exists():
        raise SystemExit("не нашёл %s" % TOKENS)
    css = TOKENS.read_text(encoding="utf-8")
    blocks = re.split(r"\[data-theme=\"dark\"\]\s*\{", css)
    light_raw = dict(re.findall(r"(--mt-[\w-]+):\s*([^;]+);", blocks[0]))
    dark_raw = dict(light_raw)
    if len(blocks) > 1:
        dark_raw.update(dict(re.findall(r"(--mt-[\w-]+):\s*([^;]+);", blocks[1])))

    def resolve(raw, value, depth=0):
        value = value.strip()
        if depth > 8:
            return None
        ref = re.fullmatch(r"var\((--mt-[\w-]+)\)", value)
        if ref:
            return resolve(raw, raw.get(ref.group(1), ""), depth + 1)
        return value.lower() if re.fullmatch(r"#[0-9a-fA-F]{3,6}", value) else None

    light = {k: resolve(light_raw, v) for k, v in light_raw.items()}
    dark = {k: resolve(dark_raw, v) for k, v in dark_raw.items()}
    return ({k: v for k, v in light.items() if v}, {k: v for k, v in dark.items() if v})


PAIRS = [
    ("основной текст", "--mt-text", "--mt-bg"),
    ("основной текст на поверхности", "--mt-text", "--mt-surface"),
    ("второстепенный текст", "--mt-text-secondary", "--mt-bg"),
    ("приглушённый текст", "--mt-text-muted", "--mt-bg"),
    ("акцент текстом", "--mt-accent", "--mt-bg"),
    ("текст на кнопке", "--mt-accent-fg", "--mt-accent"),
    ("ссылка", "--mt-link", "--mt-bg"),
    ("фокус", "--mt-focus", "--mt-bg"),
    ("ожидание оплаты", "--mt-status-await", "--mt-status-await-bg"),
    ("подтверждено", "--mt-status-ok", "--mt-status-ok-bg"),
    ("отменено", "--mt-status-cancel", "--mt-status-cancel-bg"),
    ("возврат", "--mt-status-refund", "--mt-status-refund-bg"),
    ("ошибка", "--mt-error-fg", "--mt-error-bg"),
    ("успех", "--mt-success-fg", "--mt-success-bg"),
    ("предупреждение", "--mt-warning-fg", "--mt-warning-bg"),
    ("информация", "--mt-info-fg", "--mt-info-bg"),
]

TEXT_TOKENS = ["--mt-n-400", "--mt-n-500", "--mt-n-600", "--mt-n-700",
               "--mt-n-800", "--mt-n-900", "--mt-anor-600", "--mt-indigo-700",
               "--mt-urik-500", "--mt-urik-700", "--mt-gil-500"]
SURFACES = ["--mt-n-50", "--mt-n-100", "#ffffff"]


def show(title, colours, pairs):
    print("\n%s" % title)
    print("-" * 74)
    fails = 0
    for label, fg_key, bg_key in pairs:
        fg = colours.get(fg_key, fg_key if fg_key.startswith("#") else None)
        bg = colours.get(bg_key, bg_key if bg_key.startswith("#") else None)
        if not fg or not bg:
            print("  %-32s — токен не найден" % label)
            continue
        value = ratio(fg, bg)
        mark = verdict(value)
        if mark == "FAIL":
            fails += 1
        print("  %-32s %-8s на %-8s %6.2f:1  %s" % (label, fg, bg, value, mark))
    return fails


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0].startswith("#"):
        value = ratio(args[0], args[1])
        print("%s на %s — %.2f:1 · %s" % (args[0], args[1], value, verdict(value)))
        return 0

    light, dark = palette()
    fails = show("Светлая тема", light, PAIRS)
    fails += show("Тёмная тема", dark, PAIRS)

    if "--all" in args:
        pairs = [("%s на %s" % (t.replace("--mt-", ""), s.replace("--mt-", "")), t, s)
                 for t in TEXT_TOKENS for s in SURFACES]
        show("Весь текстовый ряд на поверхностях (светлая тема)", light, pairs)

    print("\nПорог: AAA ≥ %.0f:1 · AA ≥ %.1f:1 · AA Large ≥ %.0f:1 "
          "(текст ≥24px или ≥18.66px bold)" % (AAA, AA, AA_LARGE))
    if fails:
        print("Пар ниже порога: %d — смотри docs/accessibility.md, раздел "
              "«Что в палитре не проходит»" % fails)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
