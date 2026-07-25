#!/usr/bin/env python3
"""Выгружает полный комплект файлов логотипа myTravel в brand/logo/."""
import pathlib
import re

import logo_system as L

import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent          # brand/tools/logo
BRAND = HERE.parent.parent                          # brand/
PROJECT = BRAND.parent                              # корень проекта



OUT = BRAND / "logo"
ANOR, TUT, KAYMAK = L.ANOR, L.TUT, L.KAYMAK

LAYOUTS = [
    ("primary", "Основной горизонтальный блок"),
    ("stacked", "Компактный: слово над полосой"),
    ("vertical", "Вертикальный: приём над словом"),
    ("plaque", "Блок в гранатовой плите"),
    ("mark", "Только приём — траектория и самолёт"),
    ("wordmark", "Только слово"),
    ("descriptor", "Блок с дескриптором"),
    ("micro", "Для 18–24 px: полоса толще, самолёт крупнее"),
]

# Версия с переменными: цвет задаётся снаружи, фолбэк — фирменный.
VAR_ACCENT = "var(--mt-logo-accent, #a81e2d)"
VAR_INK = "var(--mt-logo-ink, #2a211c)"


def emit(name, text):
    (OUT / name).write_text(text, encoding="utf-8")
    return len(text)


def build(slug, accent, ink):
    fn = getattr(L, "lay_" + slug)
    if slug == "wordmark":
        return fn(ink)
    if slug == "mark":
        return fn(accent)
    if slug == "plaque":
        return fn(ink, accent)          # fg, bg
    return fn(accent, ink)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # анимации живут в той же папке, но генерируются отдельно — не трогаем
    for old in OUT.glob("*.svg"):
        if not old.name.startswith("anim-"):
            old.unlink()

    total = 0
    for slug, note in LAYOUTS:
        variants = [
            ("", ANOR, TUT, "светлый фон"),
            ("-inverse", KAYMAK, KAYMAK, "тёмный фон и фото"),
            ("-mono", "currentColor", "currentColor", "один цвет, печать и штамп"),
            ("-var", VAR_ACCENT, VAR_INK, "цвет из CSS-переменных"),
        ]
        for suffix, accent, ink, what in variants:
            if slug == "plaque" and suffix == "-inverse":
                accent, ink = TUT, KAYMAK        # плита тутовая, логотип каймак
            parts, box = build(slug, accent, ink)
            head = ("<!-- myTravel · %s · %s. Текст в кривых: шрифт не нужен. "
                    "Не менять пропорции и расстояния, правила — docs/usage-rules.md -->"
                    % (note, what))
            svg = L.svg(parts, box, extra=head)
            total += emit("mytravel-%s%s.svg" % (slug, suffix), svg)

    # плитки и иконки
    emit("app-icon.svg", L.tile(size=1024, radius=None, bg=ANOR, fg=KAYMAK))
    emit("tile-anor.svg", L.tile(size=512, radius=112, bg=ANOR, fg=KAYMAK))
    emit("tile-indigo.svg", L.tile(size=512, radius=112, bg="#22285c", fg=KAYMAK))
    emit("tile-ink.svg", L.tile(size=512, radius=112, bg="#1b1512", fg=KAYMAK))
    emit("tile-light.svg", L.tile(size=512, radius=112, bg=KAYMAK, fg=ANOR))
    # favicon: полоса толще и самолёт крупнее — иначе в 16 px остаётся голая линия
    emit("favicon.svg", L.tile(size=32, radius=7, bg=ANOR, fg=KAYMAK, inset=0.74,
                               stroke=34.0, plane_scale=1.45))
    emit("tile-small.svg", L.tile(size=64, radius=14, bg=ANOR, fg=KAYMAK,
                                  inset=0.74, stroke=34.0, plane_scale=1.45))

    files = sorted(OUT.glob("*.svg"))
    print("✓ %d файлов, %d КБ" % (len(files), sum(f.stat().st_size for f in files) // 1024))
    for f in files:
        print("   %-34s %6d B" % (f.name, f.stat().st_size))


if __name__ == "__main__":
    main()
