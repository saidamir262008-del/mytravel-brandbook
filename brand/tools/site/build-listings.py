#!/usr/bin/env python3
"""
Генератор index.html для папок брендбука myTravel.

Зачем: у GitHub Pages нет листингов директорий — ссылка на папку отдаёт 404.
Скрипт кладёт статический index.html в brand/ и в каждую подпапку, чтобы
до всех 100+ файлов можно было добраться из браузера, с предпросмотром SVG.

Запуск:  python3 build-listings.py [путь-к-_site]
По умолчанию берётся /Users/said/ammar/mytravel-brand/_site

Идемпотентен: гоняй сколько угодно раз после правки материалов.
Ничего, кроме index.html в перечисленных папках, не трогает.
Нужна только стандартная библиотека python3, сеть не нужна.
"""
import html
import pathlib
import re
import sys
import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent      # brand/tools/site
BRAND_DIR = HERE.parent.parent                  # brand/
PROJECT = BRAND_DIR.parent                      # корень проекта


# Листинги собираются в исходных папках: копия сайта пересоздаётся сборкой
DEFAULT_SITE = BRAND_DIR.parent

# Папки, для которых генерируем листинг. Порядок = порядок карточек в brand/.
SUBDIRS = ("logo", "icons", "tokens", "components", "docs", "fonts", "tools")

PREVIEW_LOGO_PX = 40
PREVIEW_ICON_PX = 24


# ---------------------------------------------------------------------------
# Мелкие утилиты
# ---------------------------------------------------------------------------

def esc(text):
    """Экранирует текст для вставки в HTML."""
    return html.escape(str(text), quote=True)


def kb(num_bytes):
    """Размер в КБ по-русски: 9,4 КБ / 143 КБ."""
    value = num_bytes / 1024
    if value < 100:
        return ("%.1f" % value).replace(".", ",") + " КБ"
    return "%d КБ" % round(value)


def plural(count, one, few, many):
    """Согласование числительного: 1 файл, 2 файла, 44 файла, 28 файлов."""
    tail_100 = count % 100
    tail_10 = count % 10
    if 11 <= tail_100 <= 14:
        return "%d %s" % (count, many)
    if tail_10 == 1:
        return "%d %s" % (count, one)
    if 2 <= tail_10 <= 4:
        return "%d %s" % (count, few)
    return "%d %s" % (count, many)


def read(path):
    return path.read_text(encoding="utf-8")


def viewbox_size(svg_text):
    """Размер холста из viewBox, например '870×176'."""
    match = re.search(r'viewBox="([^"]+)"', svg_text)
    if not match:
        return None
    parts = match.group(1).replace(",", " ").split()
    if len(parts) != 4:
        return None
    return "%g×%g" % (round(float(parts[2])), round(float(parts[3])))


# ---------------------------------------------------------------------------
# Изоляция SVG при инлайне
#
# Часть файлов — анимации со своим <style>. Классы, @keyframes и id глобальны
# для документа, поэтому при вставке сорока четырёх SVG на одну страницу они
# перемешаются: .mtl-plane из anim-loader перекрасит соседа, id="t" у всех
# двадцати шести иконок совпадает, clip-path сошлётся не на тот путь.
# Поэтому каждому файлу выдаём свой префикс и переписываем ВСЕ его
# идентификаторы: id, классы (и в разметке, и в селекторах) и имена кадров.
# ---------------------------------------------------------------------------

def _collect_names(svg_text, css_text):
    """Собирает id, классы и имена @keyframes, которые надо переименовать."""
    ids = set(re.findall(r'\sid="([^"]+)"', svg_text))

    classes = set()
    for attr in re.findall(r'\sclass="([^"]*)"', svg_text):
        classes.update(attr.split())
    # Классы из селекторов: .mtl-host, .is-static и прочие, которых нет в разметке.
    # Шаблон требует букву после точки, поэтому дроби вида .22 в cubic-bezier
    # и единицы вида .5s не попадают.
    classes.update(re.findall(r"\.([A-Za-z_][\w-]*)", css_text))

    keyframes = set(re.findall(r"@keyframes\s+([\w-]+)", css_text))
    return ids, classes, keyframes


def _alternation(names):
    """Регексп-альтернатива, длинные имена первыми: .mta-ltr не должен
    съесться правилом для .mta."""
    return "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))


def _rewrite_css(css_text, prefix, classes, keyframes):
    """Переписывает селекторы классов и имена кадров внутри <style>."""
    if classes:
        pattern = re.compile(r"\.(%s)(?![\w-])" % _alternation(classes))
        css_text = pattern.sub(lambda m: "." + prefix + m.group(1), css_text)
    if keyframes:
        # Классы уже с префиксом, а префикс заканчивается дефисом, поэтому
        # запрет на [\w.#-] слева защищает их от повторного захвата.
        # Он же бережёт кастомные свойства: в --mta-speed слева стоит дефис.
        pattern = re.compile(
            r"(?<![\w.#-])(%s)(?![\w-])" % _alternation(keyframes)
        )
        css_text = pattern.sub(lambda m: prefix + m.group(1), css_text)
    return css_text


def _rewrite_ids(svg_text, prefix, ids):
    """Переписывает id и все ссылки на них: url(#x), href="#x", aria-labelledby."""
    if not ids:
        return svg_text

    def bump(name):
        return prefix + name if name in ids else name

    svg_text = re.sub(
        r'(\sid=")([^"]+)(")',
        lambda m: m.group(1) + bump(m.group(2)) + m.group(3),
        svg_text,
    )
    svg_text = re.sub(
        r"(url\(#)([^)\s]+)(\))",
        lambda m: m.group(1) + bump(m.group(2)) + m.group(3),
        svg_text,
    )
    svg_text = re.sub(
        r'((?:xlink:)?href="#)([^"]+)(")',
        lambda m: m.group(1) + bump(m.group(2)) + m.group(3),
        svg_text,
    )
    svg_text = re.sub(
        r'(aria-labelledby=")([^"]*)(")',
        lambda m: m.group(1) + " ".join(bump(x) for x in m.group(2).split()) + m.group(3),
        svg_text,
    )
    return svg_text


def _rewrite_root(svg_text, height_px):
    """Снимает width/height и подпись с корневого <svg>, задаёт высоту предпросмотра.

    Предпросмотр декоративный: имя и пояснение стоят рядом в разметке,
    поэтому корень прячем от скринридера, чтобы не читал одно и то же дважды.
    """
    match = re.match(r"<svg\b[^>]*>", svg_text)
    tag = match.group(0)
    tag = re.sub(r'\s(?:width|height|role|aria-label|aria-labelledby)="[^"]*"', "", tag)
    style = "display:block;height:%dpx;width:auto;max-width:100%%" % height_px
    tag = tag[:-1].rstrip() + ' aria-hidden="true" focusable="false" style="%s">' % style
    return tag + svg_text[match.end():]


def inline_svg(svg_text, prefix, height_px):
    """Готовит SVG к инлайну: срезает пролог, изолирует имена, задаёт высоту."""
    start = svg_text.index("<svg")
    svg_text = svg_text[start:]

    # Комментарии и <title> в предпросмотре не нужны: пояснение и имя файла
    # уже стоят в карточке. Заодно страница худеет на пару десятков килобайт.
    svg_text = re.sub(r"<!--.*?-->", "", svg_text, flags=re.S)
    svg_text = re.sub(r"<title\b[^>]*>.*?</title>", "", svg_text, flags=re.S)

    css_blocks = re.findall(r"<style[^>]*>(.*?)</style>", svg_text, re.S)
    css_text = re.sub(r"/\*.*?\*/", "", "\n".join(css_blocks), flags=re.S)

    ids, classes, keyframes = _collect_names(svg_text, css_text)

    if classes:
        svg_text = re.sub(
            r'(\sclass=")([^"]*)(")',
            lambda m: m.group(1)
            + " ".join(prefix + c for c in m.group(2).split())
            + m.group(3),
            svg_text,
        )
        svg_text = re.sub(
            r"(<style[^>]*>)(.*?)(</style>)",
            lambda m: m.group(1)
            + _rewrite_css(m.group(2), prefix, classes, keyframes)
            + m.group(3),
            svg_text,
            flags=re.S,
        )
    svg_text = _rewrite_ids(svg_text, prefix, ids)
    return _rewrite_root(svg_text, height_px)


# ---------------------------------------------------------------------------
# Каркас страницы
# ---------------------------------------------------------------------------

CSS = """
:root{
  --bg:#fbf6ee; --ink:#2a211c; --accent:#a81e2d; --muted:#665d53;
  --line:#e6ded1; --card:#fffdf8;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#1b1512; --ink:#f3ede3; --accent:#d9525c; --muted:#a89a8c;
    --line:#3b302a; --card:#221b17;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
}
.wrap{max-width:1040px;margin:0 auto;padding:20px 20px 96px}
a{color:var(--accent);text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
a:focus-visible,summary:focus-visible{
  outline:2px solid var(--accent);outline-offset:3px;border-radius:4px;
}
.mono,code{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:.88em}

.crumbs{
  font-size:14px;color:var(--muted);margin:0 0 22px;
  padding-bottom:14px;border-bottom:1px solid var(--line);
  display:flex;flex-wrap:wrap;gap:6px;align-items:baseline;
}
.crumbs .sep{opacity:.5}
.crumbs strong{font-weight:600;color:var(--ink)}

h1{font-size:26px;line-height:1.25;margin:0 0 10px;font-weight:650;letter-spacing:-.01em}
.lead{margin:0 0 8px;max-width:66ch;color:var(--ink)}
.sub{margin:0 0 30px;color:var(--muted);font-size:14px}
h2{
  font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  font-weight:650;margin:38px 0 14px;padding-top:14px;border-top:1px solid var(--line);
}
h2:first-of-type{border-top:0;padding-top:0}
h3{font-size:15px;margin:0 0 4px;font-weight:600;word-break:break-word}
.note{
  margin:14px 0 0;padding:12px 14px;border-left:3px solid var(--accent);
  background:var(--card);border-radius:0 6px 6px 0;font-size:14px;color:var(--ink);
}

.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 8px}
table{border-collapse:collapse;width:100%;min-width:540px;font-size:15px}
th,td{text-align:left;padding:11px 14px 11px 0;border-bottom:1px solid var(--line);vertical-align:top}
th{
  font-size:12px;letter-spacing:.05em;text-transform:uppercase;
  color:var(--muted);font-weight:650;white-space:nowrap;
}
td .why{color:var(--muted);font-size:13.5px;display:block;margin-top:3px}
td.size{white-space:nowrap;color:var(--muted);font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:13px}
td.name{word-break:break-word}
tr:last-child td{border-bottom:0}

.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(228px,1fr))}
.grid.tight{grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:14px}
.card{
  border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--card);
  display:flex;flex-direction:column;gap:8px;min-width:0;
}
.prev{
  display:flex;align-items:center;justify-content:center;
  min-height:76px;padding:12px;border-radius:7px;overflow:hidden;
  background:#fbf6ee;color:#2a211c;border:1px solid #e6ded1;
  --mt-logo-accent:#a81e2d; --mt-logo-ink:#2a211c;
}
.prev.on-dark{
  background:#1b1512;color:#f3ede3;border-color:#3b302a;
  --mt-logo-accent:#d9525c; --mt-logo-ink:#f3ede3;
}
.prev.icon{min-height:56px}
.card .desc{margin:0;font-size:13.5px;line-height:1.5;color:var(--ink)}
.card .why{margin:0;font-size:13px;line-height:1.5;color:var(--muted)}
.card .meta{
  margin:auto 0 0;padding-top:8px;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;
}
.card .meta .mono{font-size:12px}
.folders{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(290px,1fr))}
.folders .card{gap:6px}
.folders h3{font-size:17px}
.folders h3 a{text-decoration:none}
.folders h3 a:hover{text-decoration:underline}

.swatches{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(128px,1fr));margin:0 0 8px;padding:0;list-style:none}
.swatches li{font-size:12px;line-height:1.45;color:var(--muted);min-width:0}
.swatches .chip{display:block;height:34px;border-radius:6px;border:1px solid var(--line);margin-bottom:5px}
.swatches b{display:block;color:var(--ink);font-weight:600;font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:11.5px;word-break:break-all}

.foot{margin-top:52px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.foot a{color:var(--muted)}

@media (max-width:480px){
  .wrap{padding:16px 14px 72px}
  h1{font-size:22px}
  .grid,.grid.tight,.folders{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}
}
"""


def crumbs(trail):
    """trail — список (подпись, ссылка|None). Последний элемент без ссылки."""
    parts = []
    for label, href in trail:
        if href:
            parts.append('<a href="%s">%s</a>' % (esc(href), esc(label)))
        else:
            parts.append("<strong>%s</strong>" % esc(label))
    joined = '\n    <span class="sep">/</span>\n    '.join(parts)
    return (
        '<nav class="crumbs" aria-label="Вы находитесь здесь">\n    %s\n  </nav>' % joined
    )


def page(title, trail, heading, lead, sub, body, root_href):
    """Собирает самодостаточный HTML: без внешних ссылок, шрифтов и картинок."""
    return """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>%(title)s</title>
<style>%(css)s</style>
</head>
<body>
<main class="wrap">
  %(crumbs)s
  <h1>%(heading)s</h1>
  <p class="lead">%(lead)s</p>
  <p class="sub">%(sub)s</p>
%(body)s
  <p class="foot">Страница собрана скриптом <code>build-listings.py</code>.
  Правьте материалы в папке и запускайте его заново &mdash; список пересоберётся.
  <a href="%(root)s">На главную брендбука</a>.</p>
</main>
</body>
</html>
""" % {
        "title": esc(title),
        "css": CSS,
        "crumbs": crumbs(trail),
        "heading": esc(heading),
        "lead": lead,
        "sub": sub,
        "body": body,
        "root": esc(root_href),
    }


def table(headers, rows):
    """Таблица файлов. rows — список списков уже готовых HTML-ячеек."""
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = "\n".join(
        "      <tr>%s</tr>" % "".join(cells) for cells in rows
    )
    return (
        '  <div class="tw">\n    <table>\n      <thead><tr>%s</tr></thead>\n'
        "      <tbody>\n%s\n      </tbody>\n    </table>\n  </div>\n" % (head, body)
    )


def file_cell(name):
    return '<td class="name"><a href="%s">%s</a></td>' % (esc(name), esc(name))


def why_cell(what, why=None):
    text = esc(what)
    if why:
        text += '<span class="why">%s</span>' % esc(why)
    return "<td>%s</td>" % text


def dl_cell(name, size):
    return (
        '<td class="size">%s<span class="why"><a href="%s" download>скачать</a></span></td>'
        % (esc(kb(size)), esc(name))
    )


# ---------------------------------------------------------------------------
# Тексты: логотип
# ---------------------------------------------------------------------------

LAYOUTS = [
    ("primary", "Основной блок",
     "Знак слева, слово справа, просвет 16 при высоте знака 46. Версия по умолчанию: "
     "шапка сайта, письма, документы, презентации."),
    ("stacked", "Компактный",
     "Слово сидит над полосой, блок ниже и плотнее основного. Для узких шапок "
     "и мест, где по высоте есть запас, а по ширине нет."),
    ("vertical", "Вертикальный",
     "Приём сверху, слово по центру под ним. Для квадратных и вытянутых вверх "
     "мест: аватары, печати, стенды, торцы полиграфии."),
    ("plaque", "В гранатовой плите",
     "Тот же блок внутри скруглённого прямоугольника (радиус 34). Нужен, когда "
     "подложку не контролируешь: пёстрое фото, чужой сайт, партнёрский макет."),
    ("mark", "Только приём",
     "Полоса-траектория и самолёт, без слова. Ставится там, где название уже "
     "прозвучало рядом: фавикон, аватар, тиснение, водяной знак."),
    ("wordmark", "Только слово",
     "Начертание myTravel в кривых, без знака. Для сносок, копирайтов и строк "
     "«партнёр:», где знак был бы лишним шумом."),
    ("descriptor", "С дескриптором",
     "Основной блок плюс вторая строка приглушённым #665d53 — поясняющая "
     "подпись. Для первого контакта: наружная реклама, титульные листы."),
    ("micro", "Микро, 18–24 px",
     "Перерисован под мелкий размер: штрих полосы 30 вместо 23, самолёт крупнее. "
     "Обычный блок на этом размере залипает в пятно, этот — нет."),
]

VERSIONS = [
    ("", "Основная",
     "Гранат #a81e2d на приёме, тут #2a211c на слове. Кладётся на каймак и другие "
     "светлые поверхности."),
    ("-inverse", "Инверсия",
     "Весь блок каймаком #fbf6ee. Для тёмных плоскостей и фотографий; "
     "на светлом фоне исчезнет."),
    ("-mono", "Монохром",
     "Один цвет через currentColor — наследует color родителя. Печать в одну "
     "краску, тиснение, штамп, гравировка, факс-качество."),
    ("-var", "На переменных",
     "Цвет из CSS: var(--mt-logo-accent) и var(--mt-logo-ink) с фолбэком на "
     "гранат и тут. Один файл переключается вместе с темой приложения."),
]

TILES = [
    ("app-icon.svg", "Иконка приложения, 1024×1024",
     "Гранатовый квадрат без скругления: маску рисует сама операционная система. "
     "Исходник для App Store и Google Play."),
    ("favicon.svg", "Фавикон, 32×32",
     "Гранатовая плитка со скруглением 7, знак каймаком, шов расширен до 34 — "
     "иначе на 16 px полоса пропадает. Кладётся в <head> ссылкой icon."),
    ("tile-anor.svg", "Плитка «Анор», 512×512",
     "Основная плитка: гранат #a81e2d, скругление 112, знак каймаком. "
     "Аватар в соцсетях, мессенджерах, каталогах приложений."),
    ("tile-indigo.svg", "Плитка «Индиго», 512×512",
     "Та же плитка на бухарском индиго #22285c. Запасной аватар там, где рядом "
     "уже стоит красный: карточки партнёров, сравнения, витрины."),
    ("tile-ink.svg", "Плитка «Тут», 512×512",
     "Та же плитка на тёмном #1b1512. Для тёмных интерфейсов и подписей "
     "в конце тёмных писем."),
    ("tile-light.svg", "Плитка светлая, 512×512",
     "Инверсия: каймаковое поле #fbf6ee, знак гранатом. Когда плитка ложится "
     "на тёмную подложку и красный квадрат на ней слишком кричит."),
    ("tile-small.svg", "Плитка мелкая, 64×64",
     "Уменьшенная плитка с расширенным швом 34. Берите её, а не масштабированную "
     "tile-anor: у той на 64 px полоса становится волосом."),
]

ANIMS = [
    ("anim-takeoff.svg", "Взлёт — появление логотипа",
     "Полоса прочерчивается слева направо, слово всплывает снизу, летящая копия "
     "самолёта идёт по offset-path и садится на место. Финальный кадр байт в байт "
     "равен статичному логотипу, так что при отключённых анимациях ничего не ломается."),
    ("anim-assemble.svg", "Сборка — 2,14 с",
     "Восемь букв по очереди поднимаются из-под линии полосы (вход через "
     "90/75/65/55/45/35/25 мс — ритм ускоряется), затем рисуется полоса, "
     "затем самолёт сходит с её конца по касательной −39,52°."),
    ("anim-loader.svg", "Ожидание — бесконечный цикл 2 с",
     "Три следа разной длины бегут по траектории, самолёт летит и уходит. "
     "Период штриха равен длине пути (pathLength 1000), поэтому стык кадров не виден. "
     "Покой — обычный логотип: движение включается только при "
     "prefers-reduced-motion: no-preference."),
    ("anim-micro.svg", "Микровзаимодействие в шапке",
     "На hover самолёт делает рывок вперёд на 15,4 px и возвращается за 280 мс, "
     "на :active вдавливается назад. Всё заскоплено на .mtl и .mtl-host, "
     "поэтому файл безопасно вставлять инлайном."),
    ("anim-micro-icon.svg", "То же в иконке 32×32",
     "Один въезд по вектору набора высоты при появлении и короткий рывок на hover. "
     "Класс .is-static выключает въезд — для списков, где иконка повторяется "
     "много раз."),
]

LOGO_LEAD = (
    "Сорок четыре файла логотипа myTravel: восемь компоновок в четырёх цветовых "
    "версиях, набор плиток и фавиконов и пять анимаций. Текст во всех файлах "
    "переведён в кривые, поэтому шрифт для показа логотипа не нужен."
)


def build_logo(folder):
    """logo/ — 8 компоновок × 4 версии + плитки + анимации."""
    parts = []
    counter = [0]

    def card(name, title, desc, extra=None, height=PREVIEW_LOGO_PX):
        path = folder / name
        counter[0] += 1
        svg = inline_svg(read(path), "lg%02d-" % counter[0], height)
        dark = "-inverse" in name
        size = viewbox_size(read(path))
        return (
            '    <article class="card">\n'
            '      <div class="prev%s">%s</div>\n'
            "      <h3><a href=\"%s\">%s</a></h3>\n"
            '      <p class="desc"><b>%s.</b> %s</p>\n'
            "%s"
            '      <p class="meta"><span class="mono">%s%s</span>'
            ' <a href="%s" download>скачать</a></p>\n'
            "    </article>"
            % (
                " on-dark" if dark else "",
                svg,
                esc(name),
                esc(name),
                esc(title),
                esc(desc),
                '      <p class="why">%s</p>\n' % esc(extra) if extra else "",
                esc(kb(path.stat().st_size)),
                " · " + esc(size) if size else "",
                esc(name),
            )
        )

    parts.append("  <h2>Компоновки — восемь штук, каждая в четырёх версиях</h2>")
    parts.append(
        '  <p class="sub">Компоновка отвечает за форму блока, версия — за цвет. '
        "Пропорции и просветы внутри файлов менять нельзя: правила в "
        '<a href="../docs/usage-rules.html">docs/usage-rules.html</a>.</p>'
    )
    for slug, layout_title, layout_desc in LAYOUTS:
        parts.append("  <h2>%s</h2>" % esc(layout_title))
        parts.append('  <p class="sub">%s</p>' % esc(layout_desc))
        parts.append('  <div class="grid">')
        for suffix, ver_title, ver_desc in VERSIONS:
            parts.append(
                card("mytravel-%s%s.svg" % (slug, suffix), ver_title, ver_desc)
            )
        parts.append("  </div>")
        if slug == "plaque":
            parts.append(
                '  <p class="note"><b>Как устроена монохромная плита.</b> '
                "В <code>mytravel-plaque-mono.svg</code> логотип не закрашен вторым "
                "цветом, а вырезан из плиты маской: файл печатается одной краской "
                "и остаётся читаемым. Просто залить и плиту, и знак одним "
                "<code>currentColor</code> нельзя — получится сплошной прямоугольник.</p>"
            )

    parts.append("  <h2>Плитки, фавикон и иконка приложения</h2>")
    parts.append(
        '  <p class="sub">Готовые квадраты со знаком внутри — не собирайте их '
        "заново из компоновок, здесь уже посчитаны поля и толщина шва.</p>"
    )
    parts.append('  <div class="grid">')
    for name, title, desc in TILES:
        parts.append(card(name, title, desc))
    parts.append("  </div>")

    parts.append("  <h2>Анимации</h2>")
    parts.append(
        '  <p class="sub">Живые SVG: наведите курсор на два последних. '
        "Во всех пяти покой равен статичному логотипу, а движение выключается "
        "системной настройкой «уменьшить движение» — поэтому файл можно ставить "
        "вместо обычного логотипа, ничем не рискуя.</p>"
    )
    parts.append('  <div class="grid">')
    for name, title, desc in ANIMS:
        parts.append(card(name, title, desc))
    parts.append("  </div>")

    return page(
        title="Логотип myTravel — файлы папки logo",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("logo", None)],
        heading="brand/logo — 44 файла логотипа",
        lead=esc(LOGO_LEAD),
        sub='Все предпросмотры ниже — настоящие SVG, вставленные в страницу, '
            'а не картинки. Версии <span class="mono">-inverse</span> показаны '
            "на тёмной подложке, иначе их не видно.",
        body="\n".join(parts) + "\n",
        root_href="../../",
    )


# ---------------------------------------------------------------------------
# Тексты: иконки (сведены из icons/README.md)
# ---------------------------------------------------------------------------

ICON_CATEGORIES = [
    ("cat-flights.svg", "Авиабилеты. Самолёт строго сверху, симметричный, без инверсионного следа",
     "Плитка категории на главной, таб поиска рейсов, заголовок ваучера на перелёт"),
    ("cat-hotels.svg", "Отели. Фасад с двумя рядами окон и козырьком над входом",
     "Плитка категории, фильтр «Проживание», карточка брони отеля"),
    ("cat-cruises.svg", "Круизы. Борт судна в профиль, ватерлиния — ступенчатая линия",
     "Плитка категории, карточка круиза, письмо-подтверждение"),
    ("cat-tours.svg", "Туры. Флажок на ступенчатом маршруте с двумя точками-остановками",
     "Плитка категории, карточка турпакета, экран маршрута"),
    ("cat-car-rental.svg", "Аренда авто. Авто в профиль плюс ключ",
     "Плитка категории, фильтр «Транспорт», ваучер аренды"),
    ("cat-apartments.svg", "Аренда квартир. Срез дома с сеткой квартир-ячеек",
     "Плитка категории, выдача посуточного жилья"),
    ("cat-transfer.svg", "Трансфер. Седан спереди с табличкой встречающего над крышей",
     "Плитка категории, блок «Встреча в аэропорту», карточка трансфера"),
    ("cat-visa.svg", "Виза. Развёрнутый паспорт со ступенчатым оттиском",
     "Плитка категории, раздел визовой поддержки, статус заявления"),
    ("cat-insurance.svg", "Страховка. Щит с плоским верхом и крестом внутри",
     "Плитка категории, апсейл в чекауте, полис в «Моих поездках»"),
    ("cat-attractions.svg", "Экскурсионные билеты. Билет с отрывным корешком, кромка — abr-ступенька",
     "Плитка категории, афиша экскурсий, электронный билет"),
    ("cat-bus-rail.svg", "Автобусные и Ж/Д билеты. Вагон спереди и два рельса со ступенькой",
     "Плитка категории, таб наземного транспорта, посадочный талон"),
    ("cat-cargo.svg", "Карго. Коробка с лентой и ступенчатая стрелка отправки",
     "Плитка категории, трекинг отправления, форма расчёта доставки"),
    ("cat-concerts.svg", "Концертные билеты. Микрофон на стойке",
     "Плитка категории, афиша событий, билет на концерт"),
    ("cat-concert-tours.svg", "Концертные туры. Микрофон плюс ступенчатый маршрут — сцепка концерта и поездки",
     "Плитка категории, пакет «концерт + перелёт + отель»"),
]

ICON_UI = [
    ("ui-search.svg", "Поиск", "Строка поиска, пустой экран выдачи, кнопка в шапке"),
    ("ui-calendar.svg", "Календарь, выбор дат", "Поля «Туда»/«Обратно», выбор дат заезда, фильтры"),
    ("ui-passenger.svg", "Пассажир", "Селектор пассажиров, форма данных путешественника, профиль"),
    ("ui-filter.svg", "Фильтр", "Кнопка фильтров в выдаче, шит сортировки"),
    ("ui-back.svg", "Назад", "Навбар, шаг назад в чекауте, закрытие вложенного экрана"),
    ("ui-close.svg", "Закрыть", "Модалки, шиты, снятие чипа фильтра"),
    ("ui-check.svg", "Готово, подтверждено", "Статус «Подтверждено», выбранный пункт списка, экран успеха"),
    ("ui-alert.svg", "Внимание", "Правила тарифа, невозвратные брони, ошибки оплаты"),
    ("ui-info.svg", "Информация", "Подсказки к цене и правилам, тултипы, сноски"),
    ("ui-download.svg", "Скачать", "Скачивание ваучера, посадочного, полиса, счёта"),
    ("ui-support.svg", "Поддержка", "Кнопка связи с консультантом, чат, экран помощи"),
    ("ui-wallet.svg", "Оплата", "Способы оплаты, привязанные карты, экран платежа"),
]

ICONS_LEAD = (
    "Двадцать шесть штриховых иконок: четырнадцать категорий суперприложения "
    "и двенадцать интерфейсных. Нужны верстальщику и дизайнеру: сетка 24×24, "
    "штрих ровно 1,75, цвет только currentColor — ни одного хекса внутри файлов."
)


def build_icons(folder):
    """icons/ — 26 иконок, README и лист приёмки."""
    parts = []
    counter = [0]

    def card(name, meaning, where):
        path = folder / name
        counter[0] += 1
        svg = inline_svg(read(path), "ic%02d-" % counter[0], PREVIEW_ICON_PX)
        title = re.findall(r"<title[^>]*>(.*?)</title>", read(path))
        return (
            '    <article class="card">\n'
            '      <div class="prev icon">%s</div>\n'
            "      <h3><a href=\"%s\">%s</a></h3>\n"
            '      <p class="desc"><b>%s.</b> %s</p>\n'
            '      <p class="why">%s</p>\n'
            '      <p class="meta"><span class="mono">%s · 24×24</span>'
            ' <a href="%s" download>скачать</a></p>\n'
            "    </article>"
            % (
                svg,
                esc(name),
                esc(name),
                esc(title[0] if title else name),
                esc(meaning),
                esc(where),
                esc(kb(path.stat().st_size)),
                esc(name),
            )
        )

    parts.append("  <h2>Категории суперприложения — 14 иконок</h2>")
    parts.append(
        '  <p class="sub">Единая метафора: предмет плоско, спереди или строго '
        "в профиль. Никакой перспективы и никаких «самолётиков по диагонали». "
        "Где нужна идея маршрута, стоит ступенчатая линия — тот же приём, что "
        "в кромке иката <code>abr-edge</code>.</p>"
    )
    parts.append('  <div class="grid tight">')
    for name, meaning, where in ICON_CATEGORIES:
        parts.append(card(name, meaning, where))
    parts.append("  </div>")

    parts.append("  <h2>Интерфейсные — 12 иконок</h2>")
    parts.append('  <div class="grid tight">')
    for name, meaning, where in ICON_UI:
        parts.append(card(name, meaning, where))
    parts.append("  </div>")

    parts.append("  <h2>Документация и приёмка</h2>")
    rows = []
    for name, what, why in (
        ("README.md", "Полное описание набора",
         "Таблицы значений всех 26 иконок, правила сетки и штриха, оптическая "
         "компенсация и почему нельзя масштабировать ниже 20 px и выше 48 px"),
        ("preview.html", "Лист визуальной проверки",
         "Все 26 иконок сразу в 24 px и в 16 px на каймаке. Смотреть надо именно "
         "на колонку 16 px: если форма схлопнулась — иконку перерисовывают, "
         "а не уменьшают"),
    ):
        path = folder / name
        rows.append([file_cell(name), why_cell(what, why), dl_cell(name, path.stat().st_size)])
    parts.append(table(["Файл", "Что это", "Размер"], rows))

    parts.append(
        '  <p class="note"><b>Цвет наследуется только у инлайнового SVG.</b> '
        "Через <code>&lt;img src&gt;</code> <code>currentColor</code> не работает — "
        "иконка станет чёрной. Вклеивайте разметку в страницу или собирайте спрайт "
        "<code>&lt;symbol&gt;</code>, перенося атрибуты <code>stroke</code> и "
        "<code>stroke-width</code> с корневого тега.</p>"
    )

    return page(
        title="Иконки myTravel — файлы папки icons",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("icons", None)],
        heading="brand/icons — 26 иконок",
        lead=esc(ICONS_LEAD),
        sub="Предпросмотр показан в рабочем размере 24 px и берёт цвет текста "
            "страницы — ровно так же иконка поведёт себя в приложении.",
        body="\n".join(parts) + "\n",
        root_href="../../",
    )


# ---------------------------------------------------------------------------
# tokens/
# ---------------------------------------------------------------------------

TOKEN_SWATCH_GROUPS = [
    ("Анор — гранат. Бренд и главное действие", "anor"),
    ("Индиго — бухарская краска. Информация и тёмные плоскости", "indigo"),
    ("Урюк — курага. Ожидание и предупреждение, не больше 10% площади", "urik"),
    ("Гил — сырцовая глина. Декор, иллюстрации, разделители", "gil"),
    ("Нейтральная шкала — от каймака к туту", "n"),
]


def _palette(css_text, group):
    """Достаёт из :root пары --mt-<group>-<step>: #hex, сохраняя порядок файла."""
    root = re.search(r":root\s*\{(.*?)\n\}", css_text, re.S)
    scope = root.group(1) if root else css_text
    pattern = r"(--mt-%s-\d+)\s*:\s*(#[0-9a-fA-F]{3,8})" % re.escape(group)
    return re.findall(pattern, scope)


def build_tokens(folder):
    """tokens/ — источник правды по цвету и типографике."""
    css_text = read(folder / "tokens.css")
    variables = len(set(re.findall(r"(--mt-[\w-]+)\s*:", css_text)))

    parts = []
    rows = [
        [
            file_cell("tokens.css"),
            why_cell(
                "Источник правды. Подключается тегом link, дальше в проекте "
                "только переменные, ни одного сырого хекса",
                "%d переменных --mt-*: палитра, семантика, статусы бронирования, "
                "роли поверхностей, типографика, отступы шагом 4, радиусы, тёплые "
                "тени от тута, тап-зоны и фокус, длительности движения и кромка "
                "abr-edge. Тёмная тема — через [data-theme=\"dark\"] и "
                "prefers-color-scheme. Здесь же класс .mt-num для табличных цифр"
                % variables,
            ),
            dl_cell("tokens.css", (folder / "tokens.css").stat().st_size),
        ],
        [
            file_cell("tokens.json"),
            why_cell(
                "Зеркало tokens.css в формате Design Tokens Community Group",
                "Импортируется в Figma через Tokens Studio. В ключе tailwind лежит "
                "готовый фрагмент для theme.extend. Правится не он, а CSS: "
                "источник правды один",
            ),
            dl_cell("tokens.json", (folder / "tokens.json").stat().st_size),
        ],
    ]
    parts.append("  <h2>Файлы</h2>")
    parts.append(table(["Файл", "Зачем нужен", "Размер"], rows))

    parts.append("  <h2>Палитра из tokens.css</h2>")
    parts.append(
        '  <p class="sub">Значения вытащены из файла при сборке страницы, '
        "поэтому расходиться с ним не могут.</p>"
    )
    for label, group in TOKEN_SWATCH_GROUPS:
        pairs = _palette(css_text, group)
        if not pairs:
            continue
        chips = "".join(
            '      <li><span class="chip" style="background:%s"></span>'
            "<b>%s</b>%s</li>\n" % (esc(value), esc(name), esc(value))
            for name, value in pairs
        )
        parts.append("  <h3>%s</h3>" % esc(label))
        parts.append('  <ul class="swatches">\n%s  </ul>' % chips)

    parts.append(
        '  <p class="note"><b>Правило про красный.</b> Гранат — цвет бренда '
        "и главного действия, поэтому ошибка никогда не обозначается одним "
        "красным: всегда красный плюс иконка плюс текст. Статус «отменено» — "
        "нейтральный, иначе он спорит с кнопкой «Оплатить».</p>"
    )

    return page(
        title="Токены myTravel — файлы папки tokens",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("tokens", None)],
        heading="brand/tokens — цвет, шрифт, отступы",
        lead="Два файла с одним и тем же содержимым в разных форматах: "
             "CSS для разработчика и JSON для дизайнера. Всё, что в продукте "
             "имеет цвет, размер или отступ, берётся отсюда.",
        sub="Источник правды — <span class=\"mono\">tokens.css</span>. "
            "JSON собирается по нему; при расхождении верить CSS.",
        body="\n".join(parts) + "\n",
        root_href="../../",
    )


# ---------------------------------------------------------------------------
# fonts/
# ---------------------------------------------------------------------------

FAMILY_ROLE = {
    "Alegreya": ("дисплейная гарнитура", "заголовки и крупные акценты, вес 500–700"),
    "IBMPlexSans": ("текстовая гарнитура", "весь интерфейсный текст, вес 400–700"),
    "IBMPlexMono": ("моноширинная", "цены, даты, номера рейсов и паспортов — класс .mt-num"),
}

SUBSET_ROLE = {
    "latin": "Базовая латиница. Здесь же U+02BB — та самая запятая-модификатор в oʻ и gʻ",
    "latin-ext": "Расширенная латиница: диакритика европейских языков и узбекской латиницы",
    "cyrillic": "Базовая кириллица: русский текст",
    "cyrillic-ext": "Обязателен: Қ, Ғ, Ҳ узбекской кириллицы живут только здесь",
}


def _font_row(path):
    name = path.name
    match = re.match(r"([A-Za-z]+)-([\d\- ]+)-(.+)\.woff2$", name)
    family, weight, subset = match.group(1), match.group(2), match.group(3)
    role, usage = FAMILY_ROLE[family]
    pretty = {"IBMPlexSans": "IBM Plex Sans", "IBMPlexMono": "IBM Plex Mono"}.get(family, family)
    what = "%s %s — %s, субсет %s" % (pretty, weight.replace("-", "–"), role, subset)
    return [file_cell(name), why_cell(what, SUBSET_ROLE[subset] + ". Применение: " + usage),
            dl_cell(name, path.stat().st_size)]


def build_fonts(folder):
    """fonts/ — woff2, лицензия и собранный inline-CSS."""
    woff = sorted(folder.glob("*.woff2"))
    parts = ["  <h2>Шрифтовые файлы — 16 woff2</h2>"]
    parts.append(
        '  <p class="sub">Четыре субсета на каждое начертание. Подключать надо '
        "все четыре: браузер сам возьмёт нужный по unicode-range, а без "
        "cyrillic-ext узбекская кириллица разъедется по разным шрифтам.</p>"
    )
    parts.append(table(["Файл", "Что это", "Размер"], [_font_row(p) for p in woff]))

    parts.append("  <h2>Служебные файлы</h2>")
    rows = []
    for name, what, why in (
        ("fonts-inline.css", "Собранные @font-face с base64 data: URI",
         "Те же шестнадцать woff2, вшитые прямо в CSS. Так брендбук открывается "
         "двойным кликом офлайн: Chrome блокирует загрузку шрифтов по file:// "
         "из-за CORS. Генерируется tools/build-fonts.py, руками не править"),
        ("gf.css", "Сырой ответ Google Fonts CSS API",
         "Промежуточный файл сборки: из него берутся ссылки на woff2 и "
         "unicode-range. Здесь ещё лежат ненужные субсеты — греческий, "
         "вьетнамский; их отсекает скрипт"),
        ("OFL.txt", "SIL Open Font License 1.1",
         "Лицензия на все три гарнитуры. Коммерческое использование разрешено, "
         "отдельная покупка не нужна. Файл обязан ехать вместе со шрифтами"),
    ):
        path = folder / name
        rows.append([file_cell(name), why_cell(what, why), dl_cell(name, path.stat().st_size)])
    parts.append(table(["Файл", "Что это", "Размер"], rows))

    parts.append(
        '  <p class="note"><b>Замену подбирать нельзя.</b> В узбекской латинице '
        "<code>oʻ</code> и <code>gʻ</code> пишутся через U+02BB — modifier letter "
        "turned comma, а не через апостроф. Onest, Manrope, Rubik, Golos Text, "
        "PT Sans и Wix Madefor этот символ не содержат, поэтому они отклонены.</p>"
    )

    return page(
        title="Шрифты myTravel — файлы папки fonts",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("fonts", None)],
        heading="brand/fonts — три гарнитуры, 16 субсетов",
        lead="Alegreya для заголовков, IBM Plex Sans для текста, IBM Plex Mono "
             "для цифр — все под открытой лицензией OFL. Нужны разработчику, "
             "который подключает шрифты к продукту.",
        sub="Предпросмотра начертаний здесь нет намеренно: страница "
            "самодостаточна и ничего не подгружает. Как шрифты выглядят "
            "в работе — смотрите в <a href=\"../brandbook.html\">брендбуке</a>.",
        body="\n".join(parts) + "\n",
        root_href="../../",
    )


# ---------------------------------------------------------------------------
# components/, tools/, docs/
# ---------------------------------------------------------------------------

UI_KIT_SECTIONS = [
    "Кнопки и чипы", "Поля ввода", "Панель поиска: авиа, отели, авто",
    "Карточки результата", "Форма данных пассажира", "Выбор способа оплаты",
    "Статусы бронирования", "Пустые состояния и ошибки", "Ваучер и билет на печать",
]


def build_components(folder):
    """components/ — живые компоненты интерфейса."""
    path = folder / "ui-kit.html"
    rows = [[
        file_cell("ui-kit.html"),
        why_cell(
            "Живые компоненты интерфейса, собранные на токенах",
            "Не картинка и не макет: разметка работает, поля вводятся, состояния "
            "переключаются. Шрифты вшиты в файл как base64, поэтому он "
            "открывается двойным кликом офлайн. Разделы: " + "; ".join(UI_KIT_SECTIONS),
        ),
        dl_cell("ui-kit.html", path.stat().st_size),
    ]]
    body = "  <h2>Файлы</h2>\n" + table(["Файл", "Что это", "Размер"], rows)
    body += (
        '  <p class="note">Компонент из этого файла можно копировать в проект '
        "целиком, но цвета и размеры в нём заданы переменными из "
        "<a href=\"../tokens/\">tokens/tokens.css</a> — без подключённых токенов "
        "он приедет неокрашенным.</p>\n"
    )
    return page(
        title="Компоненты myTravel — файлы папки components",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("components", None)],
        heading="brand/components — живой UI-kit",
        lead="Один файл, зато большой: собранные из токенов элементы интерфейса "
             "myTravel в рабочем виде. Нужен верстальщику как эталон разметки "
             "и дизайнеру как проверка, что макет собирается из готового.",
        sub="Открывайте <a href=\"ui-kit.html\">ui-kit.html</a> — он "
            "самодостаточный, сеть не нужна.",
        body=body,
        root_href="../../",
    )


TOOLS = [
    ("build-brandbook.py",
     "Делает brandbook.html самодостаточным",
     "Вклеивает между маркерами содержимое tokens/tokens.css, все SVG из logo/ "
     "и icons/ как <symbol>. Сеть не нужна, только стандартная библиотека. "
     "Идемпотентен. Запуск: python3 tools/build-brandbook.py"),
    ("build-fonts.py",
     "Скачивает шрифты и вшивает их в страницы как base64",
     "Берёт CSS у Google Fonts, оставляет четыре нужных субсета, качает woff2 "
     "в fonts/, пишет fonts-inline.css и вклеивает результат в brandbook.html "
     "и components/ui-kit.html. Нужна сеть. Запускать ПОСЛЕ build-brandbook.py"),
    ("contrast.py",
     "Считает контрасты палитры по WCAG 2.1",
     "Читает цвета прямо из tokens.css, поэтому таблицы в docs/accessibility.md "
     "не могут разойтись с токенами. Без аргументов печатает ключевые пары обеих "
     "тем, с --all — весь текстовый ряд на всех поверхностях, с парой хексов — "
     "одну пару. Сеть и зависимости не нужны"),
]


def build_tools(folder):
    """tools/ — скрипты пересборки."""
    rows = []
    for name, what, why in TOOLS:
        path = folder / name
        lines = len(read(path).splitlines())
        rows.append([
            file_cell(name),
            why_cell(what, why),
            '<td class="size">%s<span class="why">%s · <a href="%s" download>скачать</a></span></td>'
            % (esc(kb(path.stat().st_size)),
               esc(plural(lines, "строка", "строки", "строк")), esc(name)),
        ])
    body = "  <h2>Скрипты</h2>\n" + table(["Файл", "Что делает", "Размер"], rows)
    body += (
        '  <p class="note"><b>Порядок важен.</b> Сначала '
        "<code>build-brandbook.py</code>, потом <code>build-fonts.py</code>: "
        "второй ищет маркеры шрифтов в уже пересобранном файле. Оба идемпотентны — "
        "гонять можно сколько угодно раз.</p>\n"
        '  <p class="note"><b>Сборка сайта.</b> Листинги папок, карта материалов '
        "и HTML-версии документов собираются скриптами из "
        '<a href="site/">tools/site/</a>. Всё вместе запускается одной командой '
        "<code>./build-site.sh</code> из корня проекта — она же проверяет ссылки.</p>\n"
        '  <p class="note"><b>Логотип пересобирается отдельно.</b> Он не рисуется '
        "руками, а вычисляется: все компоновки выводятся из капитальной высоты "
        "слова. Генератор и оба шрифта лежат в "
        '<a href="logo/">tools/logo/</a> — там же README с величинами системы, '
        "инструкцией запуска и списком граблей.</p>\n"
    )
    return page(
        title="Скрипты пересборки myTravel — файлы папки tools",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("tools", None)],
        heading="brand/tools — три скрипта пересборки",
        lead="Скрипты нужны, только если вы поменяли токены, логотип, иконки "
             "или шрифты. Обычная работа с брендбуком их не требует: все "
             "результаты уже лежат в репозитории.",
        sub="Запускать из корня папки <span class=\"mono\">brand/</span>, "
            "например <code>python3 tools/build-brandbook.py</code>.",
        body=body,
        root_href="../../",
    )


DOCS = [
    ("usage-rules", "Правила использования",
     "Что можно и чего нельзя делать со знаком, словесным знаком и цветом. "
     "Обязателен для подрядчиков, агентств и партнёров. В конце — чек-лист, "
     "который дизайнер проходит перед сдачей макета"),
    ("voice-and-tone", "Голос и тон",
     "Для всех, кто пишет текст: интерфейс, письма, push, поддержка, промо. "
     "Словарь «пиши так / не пиши так» и готовые формулировки на русском, "
     "узбекском и английском. Помните: узбекский текст на 10–20% длиннее "
     "русского, кнопки проверяйте именно на нём"),
    ("accessibility", "Доступность по WCAG 2.2",
     "Контрасты, тап-зоны, фокус и чек-лист приёмки. Все пары цветов посчитаны "
     "скриптом по формуле WCAG 2.1, а не подобраны на глаз — на глаз не "
     "подбирайте и вы"),
]


def build_docs(folder):
    """docs/ — три документа, каждый в HTML и в Markdown."""
    rows = []
    for slug, title, why in DOCS:
        html_path = folder / (slug + ".html")
        md_path = folder / (slug + ".md")
        rows.append([
            '<td class="name"><a href="%s.html">%s.html</a>'
            '<span class="why">исходник: <a href="%s.md">%s.md</a></span></td>'
            % (esc(slug), esc(slug), esc(slug), esc(slug)),
            why_cell(title, why),
            '<td class="size">%s<span class="why">%s · '
            '<a href="%s.html" download>html</a> · '
            '<a href="%s.md" download>md</a></span></td>'
            % (esc(kb(html_path.stat().st_size)), esc(kb(md_path.stat().st_size)),
               esc(slug), esc(slug)),
        ])
    body = "  <h2>Документы</h2>\n" + table(["Файл", "О чём", "Размер"], rows)
    body += (
        '  <p class="note">HTML и Markdown — один и тот же текст. HTML удобно '
        "читать в браузере, Markdown удобно смотреть в diff и цитировать "
        "в задачах. Правится Markdown, HTML собирается по нему.</p>\n"
    )
    return page(
        title="Документация myTravel — файлы папки docs",
        trail=[("Брендбук myTravel", "../../"), ("brand", "../"), ("docs", None)],
        heading="brand/docs — правила, тон и доступность",
        lead="Три текстовых документа брендбука. Каждый лежит в двух видах: "
             "готовая HTML-страница для чтения и Markdown-исходник для правки.",
        sub="Если сомневаетесь, с чего начать — начните с "
            "<a href=\"usage-rules.html\">правил использования</a>: "
            "они короче остальных и отвечают на большинство вопросов.",
        body=body,
        root_href="../../",
    )


# ---------------------------------------------------------------------------
# brand/ — общая страница
# ---------------------------------------------------------------------------

FOLDER_CARDS = [
    ("logo", "Логотип",
     "Восемь компоновок в четырёх цветовых версиях, плитки, фавикон, иконка "
     "приложения и пять анимаций. Текст в кривых — шрифт для показа не нужен."),
    ("icons", "Иконки",
     "Четырнадцать иконок категорий и двенадцать интерфейсных. Сетка 24×24, "
     "штрих 1,75, цвет только currentColor."),
    ("tokens", "Токены",
     "Источник правды по цвету, типографике, отступам и тени: CSS для кода, "
     "JSON для Figma и Tailwind."),
    ("components", "Компоненты",
     "Живой UI-kit: поиск, карточки результата, оплата, статусы, ваучер. "
     "Не макет — рабочая разметка на токенах."),
    ("docs", "Документация",
     "Правила использования знака и цвета, голос и тон с текстами на трёх "
     "языках, доступность с посчитанными контрастами."),
    ("fonts", "Шрифты",
     "Alegreya, IBM Plex Sans и IBM Plex Mono под лицензией OFL: шестнадцать "
     "субсетов woff2 плюс собранный inline-CSS."),
    ("tools", "Скрипты",
     "Три питон-скрипта пересборки. Нужны, только если вы поменяли исходные "
     "материалы."),
]

BRAND_FILES = [
    ("brandbook.html", "Главный интерактивный брендбук",
     "Начинать надо отсюда. Один самодостаточный файл: токены, логотипы, иконки "
     "и шрифты вшиты внутрь, работает офлайн двойным кликом. В конце — раздел "
     "«Самокритика» с честным списком того, что брендбук не покрывает"),
    ("README.md", "Техническая записка для разработчика и дизайнера",
     "Как подключить токены и тёмную тему, почему субсет cyrillic-ext "
     "обязателен, как собрать спрайт иконок, чем пересобирать материалы"),
]


def build_brand(folder):
    """brand/ — общая страница по всем подпапкам."""
    parts = ["  <h2>Подпапки</h2>", '  <div class="folders">']
    for name, title, desc in FOLDER_CARDS:
        sub = folder / name
        files = [p for p in sub.iterdir() if p.is_file() and p.name != "index.html"]
        total = sum(p.stat().st_size for p in files)
        parts.append(
            '    <article class="card">\n'
            '      <h3><a href="%s/">%s/</a> &mdash; %s</h3>\n'
            '      <p class="desc">%s</p>\n'
            '      <p class="meta"><span class="mono">%s · %s</span></p>\n'
            "    </article>"
            % (esc(name), esc(name), esc(title), esc(desc),
               esc(plural(len(files), "файл", "файла", "файлов")), esc(kb(total)))
        )
    parts.append("  </div>")

    parts.append("  <h2>Файлы в самой папке brand</h2>")
    rows = []
    for name, what, why in BRAND_FILES:
        path = folder / name
        rows.append([file_cell(name), why_cell(what, why), dl_cell(name, path.stat().st_size)])
    parts.append(table(["Файл", "Что это", "Размер"], rows))

    parts.append(
        '  <p class="note"><b>Направление ABR</b> (абрбандӣ, икат): гранат, '
        "бухарское индиго, тёплая бумага и один-единственный смелый приём — "
        "ступенчатая кромка <code>abr-edge</code>. Всё остальное намеренно тихое "
        "и дисциплинированное.</p>"
    )

    return page(
        title="Брендбук myTravel — состав папки brand",
        trail=[("Брендбук myTravel", "../"), ("brand", None)],
        heading="brand — всё содержимое брендбука",
        lead="Семь подпапок и два файла в корне. Если открыли впервые — "
             "идите в <a href=\"brandbook.html\">brandbook.html</a>: там всё "
             "то же самое, но связно и с примерами.",
        sub="Эта страница нужна, когда известно, что именно ищешь: "
            "конкретный SVG, токен или скрипт.",
        body="\n".join(parts) + "\n",
        root_href="../",
    )


# ---------------------------------------------------------------------------

BUILDERS = {
    "logo": build_logo,
    "icons": build_icons,
    "tokens": build_tokens,
    "components": build_components,
    "docs": build_docs,
    "fonts": build_fonts,
    "tools": build_tools,
}


def main():
    site = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_SITE
    brand = site / "brand"
    if not brand.is_dir():
        raise SystemExit("Не нашёл папку brand в %s" % site)

    written = []
    for name in SUBDIRS:
        folder = brand / name
        if not folder.is_dir():
            raise SystemExit("Не нашёл папку %s" % folder)
        target = folder / "index.html"
        target.write_text(BUILDERS[name](folder), encoding="utf-8")
        written.append(target)

    target = brand / "index.html"
    target.write_text(build_brand(brand), encoding="utf-8")
    written.append(target)

    for path in written:
        print("  ✓ %s  %s" % (path.relative_to(site), kb(path.stat().st_size)))
    print("Готово: %d страниц." % len(written))


if __name__ == "__main__":
    main()
