#!/usr/bin/env python3
"""Собирает архив логотипа myTravel для пересылки: SVG, PNG, анимации, инструкция."""
import pathlib
import shutil

import raster

import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent          # brand/tools/logo
BRAND = HERE.parent.parent                          # brand/
PROJECT = BRAND.parent                              # корень проекта



BRAND = PROJECT
LOGO = BRAND / "brand" / "logo"
PACK = BRAND / "myTravel-logo"

LAYOUTS = ["primary", "stacked", "vertical", "plaque", "mark", "wordmark",
           "descriptor", "micro"]
PNG_WIDTHS = [2000, 1000]
ICONS = [("app-icon", [1024, 512]), ("tile-anor", [512, 256]),
         ("tile-indigo", [512]), ("tile-ink", [512]), ("tile-light", [512]),
         ("favicon", [64, 32, 16])]


def main():
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "svg").mkdir(parents=True)
    (PACK / "png").mkdir()
    (PACK / "anim").mkdir()

    for f in sorted(LOGO.glob("*.svg")):
        target = "anim" if f.name.startswith("anim-") else "svg"
        shutil.copy(f, PACK / target / f.name)

    made = 0
    for slug in LAYOUTS:
        for suffix in ("", "-inverse"):
            src = LOGO / ("mytravel-%s%s.svg" % (slug, suffix))
            if not src.exists():
                continue
            for w in PNG_WIDTHS:
                out = PACK / "png" / ("mytravel-%s%s-%d.png" % (slug, suffix, w))
                if raster.render(src, out, w):
                    made += 1
    for name, widths in ICONS:
        src = LOGO / ("%s.svg" % name)
        if not src.exists():
            continue
        for w in widths:
            if raster.render(src, PACK / "png" / ("%s-%d.png" % (name, w)), w):
                made += 1

    shutil.copy(BRAND / "_logo.html", PACK / "logo.html")
    # имя латиницей: кириллица в zip превращается в кракозябры на Windows
    (PACK / "README.md").write_text(README, encoding="utf-8")

    svgs = len(list((PACK / "svg").glob("*.svg")))
    anims = len(list((PACK / "anim").glob("*.svg")))
    print("SVG: %d · PNG: %d · анимаций: %d" % (svgs, made, anims))

    # .DS_Store от Finder в архив попадать не должен
    for junk in PACK.rglob(".DS_Store"):
        junk.unlink()
    archive = shutil.make_archive(str(BRAND / "myTravel-logo"), "zip",
                                  root_dir=BRAND, base_dir="myTravel-logo")
    size = pathlib.Path(archive).stat().st_size / 1024 / 1024
    print("✓ %s — %.1f МБ" % (archive, size))


README = """# myTravel — логотип

Комплект файлов утверждённого логотипа. Всё готово к использованию,
устанавливать ничего не нужно.

## С чего начать

Откройте **`logo.html`** двойным кликом — это интерактивное руководство:
все компоновки, 15 цветовых схем, иконки, анимация и правила.
Файл самодостаточный, работает офлайн, интернет не нужен.

## Что в папках

### `svg/` — основные файлы

Векторные, для сайта, приложения, макетов и печати. Текст переведён в кривые,
шрифт для отрисовки не нужен. Открываются в Figma, Illustrator, Canva и браузере.

Восемь компоновок:

| Файл | Когда брать |
|---|---|
| `mytravel-primary` | Основной блок. Везде, где хватает ширины |
| `mytravel-stacked` | Узкая шапка, мобильный экран |
| `mytravel-vertical` | Квадратные форматы, вывеска, мерч |
| `mytravel-plaque` | Пёстрый фон и фото, где выворотка теряется |
| `mytravel-mark` | Только приём: плитка, водяной знак |
| `mytravel-wordmark` | Только слово: соподпись с партнёром |
| `mytravel-descriptor` | С дескриптором: наружная реклама, презентация |
| `mytravel-micro` | Если высота блока 18–24 px |

У каждой — четыре версии:

- без суффикса — основная, для светлого фона;
- `-inverse` — для тёмного фона и фото;
- `-mono` — один цвет через `currentColor`: печать, штамп, тиснение;
- `-var` — цвет задаётся снаружи через CSS-переменные
  `--mt-logo-accent` и `--mt-logo-ink`.

Плюс иконки: `app-icon.svg` (1024, углы прямые — скругление ставит система),
`tile-anor / -indigo / -ink / -light.svg` (512) и `favicon.svg` (32).

### `png/` — растр с прозрачным фоном

Для тех, кто не работает с вектором: презентации, соцсети, документы.
Ширина 2000 и 1000 px, иконки — 1024, 512, 256, 64, 32, 16.
Версии `-inverse` белые: на белом фоне их не видно, они для тёмного.

### `anim/` — анимация

Четыре самодостаточных SVG со стилями внутри:

- `anim-takeoff.svg` — сплэш и первый экран;
- `anim-loader.svg` — зацикленный индикатор для экрана ожидания подтверждения;
- `anim-assemble.svg` — сборка логотипа;
- `anim-micro.svg` — наведение на логотип в шапке.

Вставляются как обычная картинка. При системной настройке «уменьшить движение»
анимация выключается сама и остаётся финальный кадр.

## Правила в двух словах

1. Не менять пропорции, не наклонять, не зеркалить: самолёт летит только вправо-вверх.
2. Не добавлять тень, обводку и объём.
3. Свободное поле вокруг блока — не меньше половины его высоты.
4. Не разбирать блок: самолёт без полосы и полоса без самолёта не используются.
5. На гранатовом фоне — только версия `-inverse`.
6. Ниже 24 px слово не ставится: берите `mytravel-mark` или плитку.

Полные правила — в руководстве `logo.html`, раздел «Так нельзя»,
и на сайте: https://saidamir262008-del.github.io/mytravel-brandbook/

## Цвета

- Гранат `#A81E2D` — приём
- Тут `#2A211C` — слово
- Каймак `#FBF6EE` — фон
- Индиго `#22285C` — второй цвет

Другие цвета можно посмотреть в `logo.html`: там 15 схем, включая изумруд,
бирюзу, терракоту и классический синий. Если выберете другой цвет — скажите,
пересоберу комплект под него.

## Технические детали

Слово набрано Schibsted Grotesk 700 с трекингом −14 (шрифт под SIL Open Font
License, лицензия для коммерческого использования не нужна). Единица системы —
капитальная высота, равная 100: полоса лежит на 48 ниже базовой линии,
толщина 23, отрыв — плюс 182 по горизонтали и минус 100 по вертикали.
"""


if __name__ == "__main__":
    main()
