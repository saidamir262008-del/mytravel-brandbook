#!/usr/bin/env python3
"""
Листинг папки brand/tools/logo — генератора логотипа.

Отдельным скриптом, потому что это не «файлы бренда», а исходный код системы:
его надо объяснить, а не просто перечислить.
"""
import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
LOGO = HERE.parent / "logo"
SITE_TOOLS = HERE

LOGO_FILES = [
    ("logo_system.py", "Сама система",
     "Слово, полоса, самолёт и восемь компоновок. Всё выводится из капитальной "
     "высоты, равной 100: полоса на 48 ниже базовой линии, толщина 23, "
     "отрыв +182 по горизонтали и −100 по вертикали."),
    ("pathbbox.py", "Габариты путей без браузера",
     "Считает фактические границы SVG-путей, включая кривые и дуги. Из них "
     "берётся viewBox — раньше он задавался на глаз, и часть логотипов молча "
     "обрезалась."),
    ("glyphs.py", "Доступ к отдельным глифам",
     "Отдаёт контур каждой буквы с её метриками. Нужен, чтобы резать и подменять "
     "буквы, а не только набирать строку целиком."),
    ("emit.py", "Выгрузка комплекта",
     "Пишет все SVG в brand/logo/: восемь компоновок в четырёх версиях, плитки, "
     "фавикон и иконку приложения. Анимации не трогает."),
    ("guide.py", "Страница-руководство",
     "Собирает _logo.html: компоновки, 15 цветовых схем, иконки, анимации, "
     "правила и минимальные размеры."),
    ("raster.py", "Растр через headless Chrome",
     "Отдельных конвертеров на машине нет, а Chrome даёт ровно ту картинку, "
     "которую увидит получатель. Прозрачность сохраняется."),
    ("pack.py", "Архив для пересылки",
     "Собирает myTravel-logo.zip: SVG, PNG с прозрачным фоном, анимации "
     "и инструкцию."),
    ("SchibstedGrotesk.ttf", "Шрифт словесного знака",
     "Schibsted Grotesk, SIL Open Font License 1.1. Нужен только для пересборки: "
     "в готовых SVG текст уже в кривых."),
    ("IBMPlexSans.ttf", "Шрифт дескриптора",
     "IBM Plex Sans, SIL Open Font License 1.1."),
    ("README.md", "Описание системы",
     "Величины, инструкция запуска, что делать при смене цвета или шрифта "
     "и список граблей, на которые уже наступали."),
]

CSS = """
:root{--paper:#fbf6ee;--surface:#fff;--fg:#2a211c;--muted:#665d53;--line:#e6ded1;
 --accent:#a81e2d}
@media (prefers-color-scheme:dark){:root{--paper:#1b1512;--surface:#241c18;
 --fg:#f3ede3;--muted:#c2b6a6;--line:#3b302a;--accent:#d9525c}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--fg);
 font:400 16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:82ch;margin:0 auto;padding:28px 24px 80px}
nav{font-size:14px;color:var(--muted);margin:0 0 20px}
nav a{color:var(--fg)}
h1{font-size:28px;line-height:1.2;letter-spacing:-.02em;margin:0 0 10px}
.lede{color:var(--muted);margin:0 0 26px;max-width:66ch}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
 margin:34px 0 12px}
.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);
 vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
code{font-family:ui-monospace,"SF Mono",monospace;font-size:13px}
td b{display:block;margin-bottom:2px}
td span{color:var(--muted);font-size:13px}
.size{white-space:nowrap;color:var(--muted);font-family:ui-monospace,monospace;
 font-size:12px}
a{color:var(--accent)}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.note{background:var(--surface);border:1px solid var(--line);border-radius:10px;
 padding:14px 16px;font-size:14px;line-height:1.6;margin:22px 0 0}
pre{background:var(--surface);border:1px solid var(--line);border-radius:8px;
 padding:12px 14px;overflow-x:auto;font-size:13px}
"""


SITE_FILES = [
    ("build-listings.py", "Листинги папок брендбука",
     "Собирает index.html для logo, icons, tokens, fonts, components, docs и tools: "
     "таблицы файлов с предпросмотром SVG и пояснением по каждому."),
    ("build_logo_lab_index.py", "Листинги лаборатории знака",
     "Собирает страницы восьми направлений поиска знака и папки с анимациями, "
     "с превью в трёх размерах и разбором вариантов."),
    ("build-all-map.py", "Карта всех материалов",
     "Собирает all.html: разделы по смыслу, ссылки с пояснениями и фактические "
     "числа, посчитанные обходом дерева."),
    ("mddocs.py", "Документы из markdown в HTML",
     "Браузер не показывает .md, а скачивает его. Конвертер поддерживает ровно то, "
     "что есть в документах: заголовки, таблицы, списки, код, цитаты."),
    ("build-logo-tools-index.py", "Этот листинг",
     "Собирает страницы папок tools/logo и tools/site."),
]


def kb(path):
    size = path.stat().st_size
    return "%.1f КБ" % (size / 1024) if size >= 1024 else "%d Б" % size


def build(folder, files, title, lede, crumb, howto, note, out_name):
    rows = []
    for name, what, why in files:
        path = folder / name
        if not path.exists():
            continue
        rows.append(
            "<tr><td><code>%s</code></td><td><b>%s</b><span>%s</span></td>"
            '<td class="size">%s · <a href="%s" download>скачать</a></td></tr>'
            % (html.escape(name), html.escape(what), html.escape(why), kb(path),
               html.escape(name)))

    page = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>%s — myTravel</title><style>%s</style></head><body><main>"
        '<nav><a href="../../../">Брендбук myTravel</a> · <a href="../../">brand</a> · '
        '<a href="../">tools</a> · %s</nav>'
        "<h1>%s</h1>"
        '<p class="lede">%s</p>'
        "<h2>Файлы</h2>"
        '<div class="tablewrap"><table><thead><tr><th>Файл</th><th>Что делает</th>'
        "<th>Размер</th></tr></thead><tbody>%s</tbody></table></div>"
        "%s"
        '<p class="note">%s</p>'
        "</main></body></html>"
        % (html.escape(title), CSS, html.escape(crumb), html.escape(title), lede,
           "".join(rows), howto, note))
    (folder / "index.html").write_text(page, encoding="utf-8")
    print("  ✓ %s (%d файлов)" % (out_name, len(rows)))


def main():
    build(
        LOGO, LOGO_FILES,
        title="Генератор логотипа",
        crumb="logo",
        lede="Логотип не нарисован в редакторе, а вычисляется: все восемь компоновок "
             "выводятся из одних и тех же величин. Поэтому его можно пересобрать, "
             "поменять пропорции или добавить новое положение, ничего не перерисовывая "
             'руками. Подробности — в <a href="README.md">README</a>.',
        howto="<h2>Как запустить</h2><pre>python3 -m venv venv\n"
              "./venv/bin/pip install fonttools brotli\n\n"
              "./venv/bin/python emit.py    # пересобрать SVG в brand/logo/\n"
              "./venv/bin/python guide.py   # пересобрать страницу-руководство\n"
              "./venv/bin/python pack.py    # собрать архив (для PNG нужен Chrome)</pre>",
        note="<b>Проверка при каждом запуске.</b> Пересборка сверяется с утверждённым "
             "файлом: расхождение должно быть 0.0000. Если появилось — значит поехали "
             "величины системы, и это надо чинить до выгрузки.",
        out_name="brand/tools/logo/index.html")

    build(
        SITE_TOOLS, SITE_FILES,
        title="Сборка сайта",
        crumb="site",
        lede="Скрипты, которые собирают этот сайт: листинги папок, карту материалов "
             "и HTML-версии документов. Запускаются одной командой "
             "<code>./build-site.sh</code> из корня проекта — она же проверяет все "
             "ссылки и не даёт выложить сайт с битыми.",
        howto="<h2>Порядок</h2><pre>1. брендбук и страница логотипа\n"
              "2. документы из markdown, листинги папок\n"
              "3. копирование материалов в _site\n"
              "4. карта материалов\n"
              "5. проверка всех ссылок</pre>",
        note="<b>Почему листинги собираются в исходниках.</b> Копия сайта "
             "пересоздаётся при каждой сборке. Если генерировать страницы прямо в ней, "
             "они будут затёрты — на этом уже спотыкались.",
        out_name="brand/tools/site/index.html")


if __name__ == "__main__":
    main()
