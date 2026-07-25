#!/usr/bin/env python3
"""
Собирает /Users/said/ammar/mytravel-brand/_site/all.html — полную карту материалов
бренда myTravel.

Скрипт перезапускаемый: он обходит дерево сайта, считает файлы фактически,
подтягивает содержимое myTravel-logo.zip и в конце проверяет, что каждая
ссылка со страницы ведёт на существующий файл. Если ссылка битая — скрипт
падает с ненулевым кодом и печатает список.

    python3 build-all-map.py
"""

from __future__ import annotations

import html
import re
import sys
import zipfile
from pathlib import Path
import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent      # brand/tools/site
BRAND_DIR = HERE.parent.parent                  # brand/
PROJECT = BRAND_DIR.parent                      # корень проекта


ROOT = _pl.Path("/Users/said/ammar/mytravel-brand/_site")
OUT = ROOT / "all.html"
ZIP = ROOT / "myTravel-logo.zip"

SKIP_DIRS = {".git"}

# --------------------------------------------------------------------------
# Инвентаризация дерева
# --------------------------------------------------------------------------


def walk_site() -> list[Path]:
    """Все файлы сайта, кроме служебных каталогов. Пути относительно ROOT."""
    found: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        found.append(rel)
    # all.html может ещё не существовать на первом прогоне — считаем его тоже,
    # иначе цифры на странице будут расходиться сами с собой.
    out_rel = OUT.relative_to(ROOT)
    if out_rel not in found:
        found.append(out_rel)
    return sorted(found)


FILES = walk_site()
FILE_SET = {str(p) for p in FILES}


def by_suffix(suffix: str, under: str = "") -> list[str]:
    return sorted(
        f for f in FILE_SET if f.endswith(suffix) and f.startswith(under)
    )


def human_size(num_bytes: int) -> str:
    mb = num_bytes / 1024 / 1024
    if mb >= 1:
        return f"{mb:.1f}".replace(".", ",") + " МБ"
    return f"{num_bytes / 1024:.0f} КБ"


def plural(n: int, one: str, few: str, many: str) -> str:
    """Русское согласование: 1 файл, 2 файла, 5 файлов."""
    tail, hundred = n % 10, n % 100
    if tail == 1 and hundred != 11:
        return one
    if 2 <= tail <= 4 and not 12 <= hundred <= 14:
        return few
    return many


def count_phrase(n: int, one: str, few: str, many: str) -> str:
    return f"{n} {plural(n, one, few, many)}"


# --------------------------------------------------------------------------
# Проверка «внешних запросов нет» — не на слово, а чтением страниц
# --------------------------------------------------------------------------

EXTERNAL_RE = re.compile(r'(?:src|href)="(https?://[^"]*)"')
CANONICAL_RE = re.compile(r"<link[^>]*rel=\"canonical\"[^>]*>", re.I)


def audit_external() -> tuple[int, list[str]]:
    """Сколько HTML-страниц прочитано и какие из них тянут сторонний домен.

    Ссылка rel=canonical не считается: она метаданные для поисковика,
    браузер по ней ничего не загружает.
    """
    scanned = 0
    offenders: list[str] = []
    for rel in by_suffix(".html"):
        path = ROOT / rel
        if not path.exists():
            continue
        scanned += 1
        text = CANONICAL_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
        if EXTERNAL_RE.search(text):
            offenders.append(rel)
    return scanned, offenders


# --------------------------------------------------------------------------
# Комплект для пересылки
# --------------------------------------------------------------------------


def read_zip() -> dict:
    with zipfile.ZipFile(ZIP) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
    return {
        "total": len(names),
        "svg": len([n for n in names if n.endswith(".svg") and "/svg/" in n]),
        "anim": len([n for n in names if n.endswith(".svg") and "/anim/" in n]),
        "png": len([n for n in names if n.endswith(".png")]),
        "size": human_size(ZIP.stat().st_size),
    }


PACK = read_zip()

# --------------------------------------------------------------------------
# Словари подписей
# --------------------------------------------------------------------------

LAYOUTS = [
    ("primary", "Основная", "Слово, полоса и отрыв — для шапок, писем и презентаций"),
    ("stacked", "Компактная", "Та же композиция плотнее — для узких мест"),
    ("vertical", "Вертикальная", "Знак над словом — для аватарок и квадратных блоков"),
    ("plaque", "В плашке", "Логотип внутри гранатового прямоугольника"),
    ("mark", "Только приём", "Полоса с отрывом без слова — знак для мелких мест"),
    ("wordmark", "Только слово", "Словесный знак без взлётной полосы"),
    ("descriptor", "С дескриптором", "Логотип плюс строка услуг под ним"),
    ("micro", "Микро", "Пересчитанная версия для высоты блока 18–24 px"),
]

VERSIONS = [
    ("", "основная"),
    ("-inverse", "выворотка"),
    ("-mono", "монохром, currentColor"),
    ("-var", "CSS-переменные"),
]

LOGO_EXTRA = [
    ("app-icon.svg", "Иконка приложения, 1024×1024"),
    ("favicon.svg", "Фавиконка для вкладки браузера"),
    ("tile-anor.svg", "Плитка на гранате"),
    ("tile-indigo.svg", "Плитка на бухарском индиго"),
    ("tile-ink.svg", "Плитка на тёмном тут"),
    ("tile-light.svg", "Плитка на каймаке"),
    ("tile-small.svg", "Плитка для мелких размеров, упрощённая"),
]

LOGO_ANIM = [
    ("anim-assemble.svg", "Сборка логотипа из частей, 1,6 с"),
    ("anim-takeoff.svg", "Отрыв полосы от земли, для сплэша"),
    ("anim-loader.svg", "Зацикленный индикатор загрузки"),
    ("anim-micro.svg", "Микро-версия в движении, для шапки"),
    ("anim-micro-icon.svg", "Анимированная иконка без слова"),
]

ICONS_CAT = [
    ("cat-flights", "Авиабилеты"),
    ("cat-hotels", "Отели"),
    ("cat-cruises", "Круизы"),
    ("cat-tours", "Туры"),
    ("cat-car-rental", "Аренда авто"),
    ("cat-apartments", "Аренда квартир"),
    ("cat-transfer", "Трансфер"),
    ("cat-visa", "Виза"),
    ("cat-insurance", "Страховка"),
    ("cat-attractions", "Экскурсионные билеты"),
    ("cat-bus-rail", "Автобус и Ж/Д"),
    ("cat-cargo", "Карго"),
    ("cat-concerts", "Концертные билеты"),
    ("cat-concert-tours", "Концертные туры"),
]

ICONS_UI = [
    ("ui-search", "Поиск"),
    ("ui-calendar", "Календарь и даты"),
    ("ui-passenger", "Пассажир"),
    ("ui-filter", "Фильтр"),
    ("ui-back", "Назад"),
    ("ui-close", "Закрыть"),
    ("ui-check", "Подтверждено"),
    ("ui-alert", "Внимание"),
    ("ui-info", "Информация"),
    ("ui-download", "Скачать"),
    ("ui-support", "Поддержка"),
    ("ui-wallet", "Оплата"),
]

# Названия направлений поиска знака — те же, что на choose.html
DIRECTIONS = [
    (
        "wordmark-flight",
        "Логотипия с приёмом полёта",
        "Слово ведёт композицию, траектория или самолёт встроены в неё. Отсюда вырос утверждённый знак",
    ),
    (
        "plaque",
        "Плашка и бейдж",
        "Логотип — сам цветной блок: билет, бирка, чемодан",
    ),
    (
        "letter-surgery",
        "Хирургия буквы",
        "Ровно одна буква несёт travel-смысл, остальные не тронуты",
    ),
    (
        "roundel",
        "Авиационная традиция",
        "Язык авиакомпаний: раундель, ливрейная полоса, киль",
    ),
    (
        "document",
        "Документ на руки",
        "Посадочный талон, штамп, отрывной корешок — форма обещания «ваучер на руки»",
    ),
    (
        "route",
        "Маршрут и карта",
        "Поездка целиком, а не только перелёт",
    ),
    (
        "motion",
        "Скорость и движение",
        "Наклон, ускорение, шеврон — «быстро уехал»",
    ),
    (
        "window",
        "Взгляд пассажира",
        "То, что человек видит сам: иллюминатор, горизонт",
    ),
]

LAB_ANIM = [
    ("anim-assemble", "Сборка логотипа"),
    ("anim-takeoff", "Отрыв от земли"),
    ("anim-loader", "Индикатор загрузки"),
    ("anim-micro", "Микро-версия в движении"),
]

FONT_FAMILIES = [
    ("Alegreya", "Alegreya", "Заголовочный, начертания 500 и 700"),
    ("IBMPlexSans", "IBM Plex Sans", "Основной текст, начертания 400 и 700"),
    ("IBMPlexMono", "IBM Plex Mono", "Цифры, цены и номера, начертания 400 и 600"),
]

SUBSETS = [
    ("latin", "латиница"),
    ("latin-ext", "расширенная латиница"),
    ("cyrillic", "кириллица"),
    ("cyrillic-ext", "расширенная кириллица: Қ, Ғ, Ҳ"),
]

CATEGORIES = [
    "Авиабилеты",
    "Отели",
    "Круизы",
    "Туры",
    "Аренда авто",
    "Аренда квартир",
    "Трансфер",
    "Виза",
    "Страховка",
    "Экскурсионные билеты",
    "Автобусные и Ж/Д билеты",
    "Карго",
    "Концертные билеты",
    "Концертные туры",
]

# --------------------------------------------------------------------------
# Сборка разметки
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def exists(href: str) -> bool:
    return href.split("#", 1)[0] in FILE_SET


def link_row(href: str, title: str, note: str) -> str:
    """Строка списка: ссылка и одно предложение о том, что откроется."""
    return (
        f'<li><a class="row" href="{esc(href)}">'
        f'<span class="row-t">{esc(title)}</span>'
        f'<span class="row-n">{esc(note)}</span></a></li>'
    )


def file_row(href: str, label: str) -> str:
    """Компактная плитка файла: имя моноширинным плюс короткая подпись."""
    name = href.rsplit("/", 1)[-1]
    return (
        f'<a class="file" href="{esc(href)}">'
        f'<code>{esc(name)}</code>'
        f'<span>{esc(label)}</span></a>'
    )


def section(anchor: str, title: str, lead: str, body: str) -> str:
    return (
        f'<section id="{anchor}">'
        f"<h2>{esc(title)}</h2>"
        f'<p class="lead">{esc(lead)}</p>'
        f"{body}</section>"
    )


def optional_index(href: str, title: str, note: str) -> str:
    """Ссылка на страницу-указатель каталога, если сосед по пайплайну её собрал."""
    return link_row(href, title, note) if exists(href) else ""


def build_logo_section() -> str:
    rows = [
        link_row(
            "index.html",
            "Руководство по логотипу",
            "Главная страница: восемь компоновок, пятнадцать цветовых схем, иконки, четыре анимации и правила — что можно и чего нельзя.",
        ),
        optional_index(
            "brand/logo/index.html",
            "Все файлы логотипа списком",
            "Указатель каталога brand/logo: каждый SVG открывается в браузере и скачивается правым кликом.",
        ),
    ]

    grids = []
    for slug, name, note in LAYOUTS:
        tiles = []
        for suffix, version in VERSIONS:
            href = f"brand/logo/mytravel-{slug}{suffix}.svg"
            if exists(href):
                tiles.append(file_row(href, version))
        if tiles:
            grids.append(
                f'<h3>{esc(name)}</h3><p class="note">{esc(note)}</p>'
                f'<div class="files">{"".join(tiles)}</div>'
            )

    extra = [
        file_row(f"brand/logo/{n}", lbl)
        for n, lbl in LOGO_EXTRA
        if exists(f"brand/logo/{n}")
    ]
    if extra:
        grids.append(
            '<h3>Иконки и плитки</h3>'
            '<p class="note">Квадратные версии: домашний экран телефона, вкладка браузера, аватар в мессенджере.</p>'
            f'<div class="files">{"".join(extra)}</div>'
        )

    anim = [
        file_row(f"brand/logo/{n}", lbl)
        for n, lbl in LOGO_ANIM
        if exists(f"brand/logo/{n}")
    ]
    if anim:
        grids.append(
            '<h3>Анимации</h3>'
            '<p class="note">SMIL внутри SVG: работают сами по себе, без JavaScript и без библиотек.</p>'
            f'<div class="files">{"".join(anim)}</div>'
        )

    return section(
        "logo",
        "Логотип",
        "Восемь компоновок, у каждой четыре версии: основная, выворотка, "
        "монохром через currentColor и версия с CSS-переменными под любой цвет. "
        "Текст переведён в кривые — файл одинаково отрисуется на машине без шрифтов.",
        f'<ul class="rows">{"".join(r for r in rows if r)}</ul>'
        f'<div class="sub">{"".join(grids)}</div>',
    )


def build_brandbook_section() -> str:
    rows = [
        link_row(
            "brand/brandbook.html",
            "Брендбук целиком",
            "Один самодостаточный файл: цвет, типографика, сетка, иконки, применение, доступность и раздел «Самокритика» в конце.",
        ),
        link_row(
            "brandbook.html",
            "Короткий адрес брендбука",
            "Та же страница по адресу покороче — удобно диктовать по телефону, редирект уводит в brand/.",
        ),
        link_row(
            "brand/docs/usage-rules.html",
            "Правила использования",
            "Что можно и чего нельзя делать со знаком, словесным знаком и цветом. Обязательно для подрядчиков и партнёров.",
        ),
        link_row(
            "brand/docs/voice-and-tone.html",
            "Голос и тон",
            "Как продукт разговаривает: словарь «пиши так / не пиши так» и готовые тексты на русском, узбекском и английском.",
        ),
        link_row(
            "brand/docs/accessibility.html",
            "Доступность",
            "Посчитанные контрасты, размеры тап-зон, поведение фокуса и чек-лист приёмки по WCAG 2.2.",
        ),
        link_row(
            "brand/README.md",
            "Инструкция разработчику",
            "Как подключить токены, тёмную тему, шрифты и иконки, и что этот брендбук осознанно не покрывает.",
        ),
        optional_index(
            "brand/docs/index.html",
            "Каталог документов",
            "Указатель brand/docs: HTML и Markdown-исходники рядом.",
        ),
        optional_index(
            "brand/index.html",
            "Корень папки brand",
            "Точка входа во все подпапки бренда: логотип, иконки, токены, шрифты, документы, компоненты.",
        ),
    ]
    md_sources = [
        ("brand/docs/usage-rules.md", "правила, исходник"),
        ("brand/docs/voice-and-tone.md", "тон, исходник"),
        ("brand/docs/accessibility.md", "доступность, исходник"),
        ("README.md", "описание репозитория"),
    ]
    md = [file_row(h, lbl) for h, lbl in md_sources if exists(h)]
    return section(
        "brandbook",
        "Брендбук и правила",
        "Документы, которые решают спор, а не оставляют его на усмотрение дизайнера. "
        "HTML-версии открываются в браузере, рядом лежат те же тексты в Markdown.",
        f'<ul class="rows">{"".join(rows)}</ul>'
        '<div class="sub"><h3>Те же документы в Markdown</h3>'
        '<p class="note">Исходники для правок и диффов: их читает git, а не браузер.</p>'
        f'<div class="files">{"".join(md)}</div></div>',
    )


def build_ui_section() -> str:
    rows = [
        link_row(
            "brand/components/ui-kit.html",
            "Живые компоненты интерфейса",
            "Собранные из токенов блоки: строка поиска, карточка результата, форма пассажира, экран оплаты и ваучер под печать — всё кликается прямо на странице.",
        ),
        optional_index(
            "brand/components/index.html",
            "Каталог компонентов",
            "Указатель brand/components — на случай, если рядом с ui-kit появятся новые файлы.",
        ),
    ]
    return section(
        "ui",
        "Интерфейс",
        "Как токены выглядят в собранном виде. Страница показывает не палитру, "
        "а готовые экраны, которые можно скопировать в продукт.",
        f'<ul class="rows">{"".join(rows)}</ul>',
    )


def build_icons_section() -> str:
    rows = [
        link_row(
            "brand/icons/preview.html",
            "Лист проверки иконок",
            "Весь набор сразу в 24 и 16 px на фоне «каймак» — смотреть нужно на колонку 16 px, там видно, какая форма схлопывается.",
        ),
        optional_index(
            "brand/icons/index.html",
            "Все иконки списком",
            "Указатель каталога brand/icons со ссылкой на каждый файл.",
        ),
        link_row(
            "brand/icons/README.md",
            "Как устроены иконки",
            "Сетка 24×24, штрих ровно 1,75, правило масштабирования и таблица «где какая иконка применяется».",
        ),
    ]
    cat = [
        file_row(f"brand/icons/{slug}.svg", label)
        for slug, label in ICONS_CAT
        if exists(f"brand/icons/{slug}.svg")
    ]
    ui = [
        file_row(f"brand/icons/{slug}.svg", label)
        for slug, label in ICONS_UI
        if exists(f"brand/icons/{slug}.svg")
    ]
    return section(
        "icons",
        "Иконки",
        f"{count_phrase(len(cat), 'иконка', 'иконки', 'иконок')} категорий "
        f"и {len(ui)} интерфейсных. Все на currentColor: "
        "цвет задаётся снаружи, поэтому светлая и тёмная темы обходятся одним комплектом файлов.",
        f'<ul class="rows">{"".join(r for r in rows if r)}</ul>'
        '<div class="sub"><h3>Категории услуг</h3>'
        '<p class="note">Плитки на главной, табы поиска и заголовки ваучеров.</p>'
        f'<div class="files">{"".join(cat)}</div>'
        '<h3>Интерфейсные</h3>'
        '<p class="note">Навигация, фильтры, статусы и оплата.</p>'
        f'<div class="files">{"".join(ui)}</div></div>',
    )


def build_tokens_section() -> str:
    rows = [
        link_row(
            "brand/tokens/tokens.css",
            "tokens.css — источник правды",
            "Цвет, типографика, отступы, радиусы и тени переменными. Подключается одним link, дальше в продукте только var(), никаких сырых хексов.",
        ),
        link_row(
            "brand/tokens/tokens.json",
            "tokens.json — те же токены для инструментов",
            "Импортируется в Figma через Tokens Studio, а ключ tailwind внутри готов к вставке в theme.extend.",
        ),
        link_row(
            "brand/fonts/OFL.txt",
            "Лицензия шрифтов",
            "SIL Open Font License 1.1 — Alegreya и оба IBM Plex можно использовать коммерчески, платить не нужно.",
        ),
        link_row(
            "brand/fonts/fonts-inline.css",
            "Шрифты, вшитые в base64",
            "Готовый CSS со шрифтами внутри: страница открывается двойным кликом офлайн, потому что Chrome блокирует загрузку шрифтов по file://.",
        ),
        link_row(
            "brand/fonts/gf.css",
            "Карта субсетов Google Fonts",
            "Диапазоны unicode-range, по которым собирались woff2 — нужна, если будете пересобирать набор.",
        ),
        optional_index(
            "brand/tokens/index.html",
            "Каталог токенов",
            "Указатель brand/tokens: CSS и JSON рядом.",
        ),
        optional_index(
            "brand/fonts/index.html",
            "Каталог шрифтов",
            "Указатель brand/fonts: все woff2, лицензия и собранный CSS.",
        ),
        optional_index(
            "brand/tools/index.html",
            "Каталог скриптов",
            "Указатель brand/tools: три скрипта пересборки с описанием, что каждый делает.",
        ),
    ]

    fonts = []
    for prefix, name, note in FONT_FAMILIES:
        tiles = []
        for path in by_suffix(".woff2", "brand/fonts/"):
            fname = path.rsplit("/", 1)[-1]
            if not fname.startswith(prefix):
                continue
            subset = next(
                (lbl for key, lbl in reversed(SUBSETS) if f"-{key}." in fname),
                "субсет",
            )
            tiles.append(file_row(path, subset))
        if tiles:
            fonts.append(
                f'<h3>{esc(name)}</h3><p class="note">{esc(note)}</p>'
                f'<div class="files">{"".join(tiles)}</div>'
            )

    tool_sources = [
        ("brand/tools/build-brandbook.py", "вклеить токены и графику"),
        ("brand/tools/build-fonts.py", "вшить шрифты в base64"),
        ("brand/tools/build-logo.py", "перерисовать логотип в кривые"),
    ]
    tools = [file_row(h, lbl) for h, lbl in tool_sources if exists(h)]

    n_woff2 = count_phrase(
        len(by_suffix(".woff2", "brand/fonts/")), "файл", "файла", "файлов"
    )
    return section(
        "tokens",
        "Токены и шрифты",
        f"Значения, из которых собрано всё остальное, и {n_woff2} woff2 — "
        "по четыре субсета на начертание. Расширенная кириллица обязательна: "
        "без неё Қ, Ғ и Ҳ разъедутся по разным шрифтам.",
        f'<ul class="rows">{"".join(rows)}</ul>'
        f'<div class="sub">{"".join(fonts)}'
        '<h3>Скрипты пересборки</h3>'
        '<p class="note">Нужны, только если поменялись токены, логотип или иконки. Порядок важен: сначала брендбук, потом шрифты.</p>'
        f'<div class="files">{"".join(tools)}</div></div>',
    )


def build_archive_section() -> str:
    rows = [
        link_row(
            "choose.html",
            "Витрина выбора: 24 варианта",
            "Все варианты знака рядом, по восьми направлениям поиска — страница, по которой принималось решение.",
        ),
        optional_index(
            "logo-lab/index.html",
            "Исходники вариантов списком",
            "Указатель каталога logo-lab: каждый SVG и заметки по каждому направлению.",
        ),
    ]

    blocks = []
    for slug, name, note in DIRECTIONS:
        tiles = []
        page = f"logo-lab/{slug}/index.html"
        if exists(page):
            tiles.append(file_row(page, "направление целиком"))
        for path in by_suffix(".svg", f"logo-lab/{slug}/"):
            num = path.rsplit("-", 1)[-1].replace(".svg", "")
            tiles.append(file_row(path, f"вариант {num.lstrip('0') or num}"))
        notes = f"logo-lab/{slug}/notes.md"
        if exists(notes):
            tiles.append(file_row(notes, "разбор направления"))
        if tiles:
            blocks.append(
                f'<h3>{esc(name)}</h3><p class="note">{esc(note)}</p>'
                f'<div class="files">{"".join(tiles)}</div>'
            )

    anim = []
    if exists("logo-lab/anim/index.html"):
        anim.append(file_row("logo-lab/anim/index.html", "мастерская целиком"))
    for slug, label in LAB_ANIM:
        demo = f"logo-lab/anim/{slug}.html"
        if exists(demo):
            anim.append(file_row(demo, f"{label}, демо"))
    for path in by_suffix(".svg", "logo-lab/anim/"):
        name = path.rsplit("/", 1)[-1]
        label = "технический пробник" if name.startswith("_") else "исходник"
        anim.append(file_row(path, label))
    probe = "logo-lab/anim/_probe.html"
    if exists(probe):
        anim.append(file_row(probe, "технический пробник"))

    n_variants = len(
        [
            f
            for f in FILE_SET
            if f.startswith("logo-lab/") and f.endswith(".svg") and "/anim/" not in f
        ]
    )
    variants = count_phrase(n_variants, "вариант", "варианта", "вариантов")
    return section(
        "archive",
        "Архив поиска знака",
        f"{variants} по восьми направлениям — то, из чего выбирали. "
        "Архив держим открытым: он объясняет, почему утверждён именно тот знак, "
        "и избавляет от повторного захода на те же идеи.",
        f'<ul class="rows">{"".join(r for r in rows if r)}</ul>'
        f'<div class="sub">{"".join(blocks)}'
        '<h3>Мастерская анимации</h3>'
        '<p class="note">Страницы-демо крутят анимацию рядом с раскадровкой, SVG — то, что уехало в brand/logo.</p>'
        f'<div class="files">{"".join(anim)}</div></div>',
    )


def build_download_section() -> str:
    body = (
        '<div class="pack">'
        f'<a class="pack-link" href="myTravel-logo.zip">Скачать myTravel-logo.zip '
        f'<span class="pack-size">{esc(PACK["size"])}</span></a>'
        "<ul class=\"pack-list\">"
        f"<li><b>{PACK['svg']} SVG</b> — восемь компоновок в четырёх версиях плюс иконка "
        "приложения, фавиконка и пять плиток. Текст в кривых, шрифты для открытия не нужны.</li>"
        f"<li><b>{PACK['png']} PNG</b> с прозрачным фоном — по 1000 и 2000 px на компоновку, "
        "фавиконка в 16, 32 и 64, иконка приложения в 512 и 1024.</li>"
        f"<li><b>{count_phrase(PACK['anim'], 'анимация', 'анимации', 'анимаций')}</b> "
        "в SVG — сборка, отрыв, загрузчик и две микро-версии. "
        "Работают без JavaScript.</li>"
        "<li><b>logo.html</b> — то же руководство по логотипу, но офлайн: открывается двойным "
        "кликом без интернета.</li>"
        "<li><b>README.md</b> — инструкция: какой файл под какую задачу и чего с логотипом делать нельзя.</li>"
        "</ul>"
        f'<p class="note">Всего в архиве '
        f'{count_phrase(PACK["total"], "файл", "файла", "файлов")}. Это то, что отправляют '
        "подрядчику или типографии одним письмом.</p>"
        "</div>"
    )
    return section(
        "download",
        "Скачать комплект",
        "Один архив со всем логотипом сразу — чтобы не собирать файлы по одному.",
        body,
    )


def build_tech_section(scanned: int, offenders: list[str]) -> str:
    if offenders:
        external_claim = (
            f"Из {count_phrase(scanned, 'прочитанной страницы', 'прочитанных страниц', 'прочитанных страниц')} "
            f"сторонний домен тянут: {', '.join(offenders)}. Остальные обходятся без сети."
        )
    else:
        external_claim = (
            "Ни одного src или href на сторонний домен ни на одной из "
            f"{count_phrase(scanned, 'страницы', 'страниц', 'страниц')}: "
            "ни CDN, ни Google Fonts, ни аналитики. Проверено чтением файлов, "
            "а не обещанием. Ничего не отвалится, когда чей-то сервис переедет."
        )
    body = (
        '<ul class="rows plain">'
        "<li><span class=\"row-t\">Страницы самодостаточные</span>"
        "<span class=\"row-n\">Любой файл можно скачать, положить на флешку и открыть "
        "двойным кликом. Сборка не нужна, сервер не нужен, интернет не нужен.</span></li>"
        "<li><span class=\"row-t\">Шрифты вшиты в base64</span>"
        "<span class=\"row-n\">Alegreya, IBM Plex Sans и IBM Plex Mono лежат внутри HTML "
        "текстом. Так сделано потому, что Chrome блокирует загрузку шрифтов по file:// — "
        "иначе брендбук на чужой машине разъехался бы системным шрифтом.</span></li>"
        "<li><span class=\"row-t\">Текст логотипа в кривых</span>"
        "<span class=\"row-n\">Ни один SVG логотипа не ссылается на шрифт: буквы — это "
        "контуры. Файл отрисуется одинаково у дизайнера, в типографии и на телефоне.</span></li>"
        "<li><span class=\"row-t\">Внешних запросов нет</span>"
        f'<span class="row-n">{esc(external_claim)}</span></li>'
        "<li><span class=\"row-t\">Иконки на currentColor</span>"
        "<span class=\"row-n\">Внутри файлов нет ни одного хекса. Цвет приходит снаружи "
        "из токенов — но только у инлайнового SVG, через img наследования не будет.</span></li>"
        "<li><span class=\"row-t\">Тёмная тема на каждой странице</span>"
        "<span class=\"row-n\">Переключается системной настройкой; в продукте тему "
        "ставит атрибут на html, чтобы у пользователя остался ручной выбор.</span></li>"
        "</ul>"
    )
    return section(
        "tech",
        "Как всё устроено технически",
        "Шесть решений, из-за которых материалы не ломаются со временем.",
        body,
    )


def build_page() -> str:
    counts = {
        "total": len(FILE_SET),
        "svg": len(by_suffix(".svg")),
        "html": len(by_suffix(".html")),
        "md": len(by_suffix(".md")),
        "woff2": len(by_suffix(".woff2")),
    }

    facts = [
        (counts["total"], plural(counts["total"], "файл", "файла", "файлов") + " в проекте"),
        (counts["svg"], plural(counts["svg"], "файл", "файла", "файлов") + " SVG"),
        (counts["html"], plural(counts["html"], "страница", "страницы", "страниц") + " HTML"),
        (counts["woff2"], plural(counts["woff2"], "субсет", "субсета", "субсетов") + " шрифтов"),
    ]
    facts_html = "".join(
        f'<div class="fact"><b>{n}</b><span>{esc(label)}</span></div>'
        for n, label in facts
    )

    cats_html = "".join(f"<li>{esc(c)}</li>" for c in CATEGORIES)

    nav_items = [
        ("logo", "Логотип"),
        ("brandbook", "Брендбук и правила"),
        ("ui", "Интерфейс"),
        ("icons", "Иконки"),
        ("tokens", "Токены и шрифты"),
        ("archive", "Архив поиска знака"),
        ("download", "Скачать комплект"),
        ("tech", "Как всё устроено"),
    ]
    nav_html = "".join(
        f'<a href="#{a}">{esc(t)}</a>' for a, t in nav_items
    )

    sections = "".join(
        [
            build_logo_section(),
            build_brandbook_section(),
            build_ui_section(),
            build_icons_section(),
            build_tokens_section(),
            build_archive_section(),
            build_download_section(),
            build_tech_section(*audit_external()),
        ]
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>myTravel — карта материалов</title>
<meta name="description" content="Полный указатель материалов бренда myTravel: логотип, брендбук, интерфейс, иконки, токены, архив поиска знака и комплект для пересылки.">
<link rel="icon" href="brand/logo/favicon.svg">
<style>
:root{{
  color-scheme: light dark;
  --bg:#fbf6ee; --fg:#2a211c; --accent:#a81e2d; --muted:#665d53;
  --line:#e6ded1; --card:#fffcf6; --hover:#f4ece0;
  /* Гранат для текста поверх карточки. В светлой теме совпадает с брендовым:
     #a81e2d даёт 7,1:1 на карточке. */
  --accent-ink:#a81e2d;
}}
@media (prefers-color-scheme: dark){{
  :root{{
    --bg:#1b1512; --fg:#f3ede3; --accent:#d9525c; --muted:#a2958a;
    --line:#3b302a; --card:#221b17; --hover:#2b2320;
    /* Брендовый #d9525c посчитан под фон страницы и на приподнятой карточке
       даёт только 4,3:1. Для мелкого текста берём тон светлее — 5,1:1. */
    --accent-ink:#e2666f;
  }}
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{
  margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
  padding:0 16px 80px;
}}
.wrap{{max-width:62rem;margin:0 auto}}
code,.mono{{font-family:ui-monospace,"SF Mono",monospace}}
a{{color:var(--accent-ink)}}
a:focus-visible,summary:focus-visible{{
  outline:2px solid var(--accent); outline-offset:3px; border-radius:3px;
}}

header{{padding:56px 0 8px;border-bottom:1px solid var(--line)}}
.kicker{{
  font-family:ui-monospace,"SF Mono",monospace; font-size:12px;
  letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin:0 0 12px;
}}
h1{{font-size:clamp(28px,6vw,44px);line-height:1.15;margin:0 0 16px;letter-spacing:-.02em}}
.intro{{max-width:60ch;margin:0 0 20px;color:var(--fg)}}
.intro + .intro{{color:var(--muted)}}

.cats{{
  list-style:none;padding:0;margin:0 0 28px;display:flex;flex-wrap:wrap;gap:6px;
}}
.cats li{{
  font-size:13px;color:var(--muted);border:1px solid var(--line);
  border-radius:999px;padding:3px 11px;background:var(--card);
}}

.primary{{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 32px}}
.primary a{{
  display:block;flex:1 1 15rem;padding:16px 18px;border:1px solid var(--line);
  border-radius:10px;background:var(--card);text-decoration:none;color:var(--fg);
}}
.primary a:hover{{background:var(--hover);border-color:var(--accent)}}
.primary b{{display:block;color:var(--accent-ink);font-size:17px;margin-bottom:4px}}
.primary span{{display:block;font-size:14px;color:var(--muted);line-height:1.5}}

.facts{{
  display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:10px;overflow:hidden;margin:0 0 36px;
  grid-template-columns:repeat(auto-fit,minmax(min(100%,8.5rem),1fr));
}}
.fact{{background:var(--card);padding:14px 16px}}
.fact b{{
  display:block;font-family:ui-monospace,"SF Mono",monospace;
  font-size:26px;line-height:1.1;color:var(--accent-ink);font-weight:600;
}}
.fact span{{display:block;font-size:13px;color:var(--muted);margin-top:2px}}

nav.toc{{
  display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;padding:0 0 32px;
  border-bottom:1px solid var(--line);
}}
nav.toc a{{
  font-size:14px;text-decoration:none;color:var(--muted);
  border:1px solid var(--line);border-radius:999px;padding:5px 13px;background:var(--card);
}}
nav.toc a:hover{{color:var(--accent-ink);border-color:var(--accent)}}

section{{padding:44px 0 8px;border-bottom:1px solid var(--line)}}
section:last-of-type{{border-bottom:0}}
h2{{font-size:clamp(21px,4vw,27px);margin:0 0 10px;letter-spacing:-.01em}}
h3{{font-size:15px;margin:26px 0 2px;letter-spacing:.01em}}
.lead{{max-width:62ch;color:var(--muted);margin:0 0 22px}}
.note{{font-size:13.5px;color:var(--muted);margin:0 0 10px;max-width:62ch}}

ul.rows{{list-style:none;padding:0;margin:0 0 4px;display:grid;gap:10px}}
.row,ul.rows.plain li{{
  display:block;padding:14px 16px;border:1px solid var(--line);border-radius:10px;
  background:var(--card);text-decoration:none;color:var(--fg);
}}
a.row:hover{{background:var(--hover);border-color:var(--accent)}}
.row-t{{display:block;font-weight:600;font-size:16px;margin-bottom:3px}}
a.row .row-t{{color:var(--accent-ink)}}
.row-n{{display:block;font-size:14px;color:var(--muted);line-height:1.5}}

.sub{{margin-top:10px}}
.files{{
  display:grid;gap:8px;margin:8px 0 4px;
  grid-template-columns:repeat(auto-fill,minmax(min(100%,13.5rem),1fr));
}}
a.file{{
  display:block;padding:9px 11px;border:1px solid var(--line);border-radius:8px;
  background:var(--card);text-decoration:none;color:var(--fg);
}}
a.file:hover{{background:var(--hover);border-color:var(--accent)}}
a.file code{{display:block;font-size:12.5px;color:var(--accent-ink);word-break:break-all}}
a.file span{{display:block;font-size:12.5px;color:var(--muted);margin-top:2px}}

.pack{{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:20px}}
.pack-link{{
  display:inline-block;font-size:17px;font-weight:600;text-decoration:none;
  color:var(--bg);background:var(--accent);padding:12px 18px;border-radius:9px;
}}
.pack-link:hover{{filter:brightness(1.08)}}
.pack-size{{
  font-family:ui-monospace,"SF Mono",monospace;font-size:13px;font-weight:400;
  opacity:.85;margin-left:6px;
}}
.pack-list{{margin:18px 0 10px;padding-left:20px;display:grid;gap:8px}}
.pack-list li{{font-size:14.5px;color:var(--muted);line-height:1.55}}
.pack-list b{{color:var(--fg)}}

footer{{padding:36px 0 0;font-size:13.5px;color:var(--muted);max-width:62ch}}
footer a{{color:var(--accent-ink)}}

@media (max-width:480px){{
  body{{padding:0 14px 60px}}
  header{{padding-top:36px}}
  .facts{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <p class="kicker">myTravel · карта материалов</p>
  <h1>Всё, что сделано по бренду, на одной странице</h1>
  <p class="intro">myTravel — travel-суперприложение для Узбекистана: человек
  покупает поездку целиком в одном месте, а не собирает её из четырёх сайтов.
  Четырнадцать категорий услуг:</p>
  <ul class="cats">{cats_html}</ul>
  <p class="intro">Бренд утверждён: знак выбран из двадцати четырёх вариантов,
  цвет, типографика и правила зафиксированы. Ниже — указатель на каждый файл,
  который для этого сделан, потому что у хостинга нет листингов каталогов и
  ссылка на папку отдаёт пустую страницу.</p>

  <div class="primary">
    <a href="index.html"><b>Руководство по логотипу</b>
      <span>Компоновки, цвета, иконки, анимация и правила. Начните отсюда, если нужен логотип.</span></a>
    <a href="brand/brandbook.html"><b>Брендбук</b>
      <span>Цвет, типографика, иконки, применение и доступность. Начните отсюда, если делаете продукт.</span></a>
  </div>

  <div class="facts">{facts_html}</div>
</header>

<nav class="toc" aria-label="Разделы страницы">{nav_html}</nav>

{sections}

<footer>
  <p>Страница собрана автоматически обходом дерева проекта — цифры и ссылки
  берутся из файлов, а не проставлены руками. Шрифты Alegreya, IBM Plex Sans и
  IBM Plex Mono — под <a href="brand/fonts/OFL.txt">SIL Open Font License 1.1</a>.
  Логотип, иконки, тексты и токены — собственность myTravel. Все имена, номера
  заказов, рейсы и телефоны в примерах вымышленные.</p>
</footer>

</div>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Проверка ссылок
# --------------------------------------------------------------------------


def verify(markup: str) -> tuple[list[str], list[str]]:
    hrefs = re.findall(r'href="([^"]+)"', markup)
    checked: list[str] = []
    broken: list[str] = []
    for href in hrefs:
        if href.startswith(("#", "http://", "https://", "mailto:", "data:")):
            continue
        checked.append(href)
        if not exists(href):
            broken.append(href)
    return checked, broken


def main() -> int:
    markup = build_page()
    checked, broken = verify(markup)
    scanned, offenders = audit_external()

    print(f"Файлов в дереве (без .git): {len(FILE_SET)}")
    print(f"  SVG {len(by_suffix('.svg'))}, HTML {len(by_suffix('.html'))}, "
          f"MD {len(by_suffix('.md'))}, woff2 {len(by_suffix('.woff2'))}")
    print(f"Архив: {PACK['total']} файлов, {PACK['svg']} SVG, "
          f"{PACK['anim']} анимаций, {PACK['png']} PNG, {PACK['size']}")
    print(f"Ссылок на файлы: {len(checked)}, уникальных: {len(set(checked))}")
    print(f"Проверено HTML-страниц на внешние запросы: {scanned}, "
          f"с внешними: {offenders or 'нет'}")

    if broken:
        print("\nБИТЫЕ ССЫЛКИ:")
        for href in sorted(set(broken)):
            print(f"  {href}")
        return 1

    OUT.write_text(markup, encoding="utf-8")
    print(f"\nЗаписано: {OUT} ({len(markup.encode('utf-8')) / 1024:.0f} КБ)")
    print("Все ссылки ведут на существующие файлы.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
