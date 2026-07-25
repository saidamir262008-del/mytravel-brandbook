#!/usr/bin/env python3
"""
Страница-руководство по утверждённому логотипу myTravel.


Все компоновки рисуются прямо из logo_system с цветами-переменными, поэтому
одна кнопка наверху перекрашивает страницу целиком: цвет и форма проверяются
отдельно друг от друга, как и положено при приёмке.
"""
import base64
import html
import pathlib
import re

import logo_system as L

import pathlib as _pl

HERE = _pl.Path(__file__).resolve().parent          # brand/tools/logo
BRAND = HERE.parent.parent                          # brand/
PROJECT = BRAND.parent                              # корень проекта


OUT = PROJECT / "_logo.html"
FONTS = BRAND / "fonts"
ANIM = PROJECT / "logo-lab" / "anim"

ACC = "var(--c-accent)"
INK = "var(--c-ink)"
PAPER = "var(--c-paper)"

SCHEMES = [
    ("Гранат", "#a81e2d", "#2a211c", "#fbf6ee"),
    ("Гранат на белом", "#a81e2d", "#2a211c", "#ffffff"),
    ("Гранат целиком", "#a81e2d", "#a81e2d", "#fbf6ee"),
    ("Индиго", "#22285c", "#22285c", "#fbf6ee"),
    ("Чёрно-белый", "#2a211c", "#2a211c", "#ffffff"),
    ("Выворотка на гранате", "#fbf6ee", "#fbf6ee", "#a81e2d"),
    ("Выворотка на индиго", "#fbf6ee", "#fbf6ee", "#22285c"),
    ("Выворотка на тёмном", "#fbf6ee", "#fbf6ee", "#1b1512"),
    ("Изумруд", "#12684f", "#2a211c", "#fbf6ee"),
    ("Бирюза", "#0e6a78", "#2a211c", "#fbf6ee"),
    ("Терракота", "#bd5620", "#2a211c", "#fbf6ee"),
    ("Слива", "#6b2a5b", "#2a211c", "#fbf6ee"),
    ("Классический синий", "#1b4fa0", "#2a211c", "#fbf6ee"),
    ("Хвоя", "#2f5d3a", "#2a211c", "#fbf6ee"),
    ("Охра", "#9a6b12", "#2a211c", "#fbf6ee"),
]

LAYOUTS = [
    ("primary", "Основной", "Утверждённый блок. Везде, где хватает ширины: сайт, презентация, документы.", "5.2 : 1"),
    ("stacked", "Компактный", "Полоса уходит под слово и отрывается позже. Для узкой шапки и мобильного экрана.", "3.5 : 1"),
    ("vertical", "Вертикальный", "Приём над словом. Квадратные форматы, вывеска, мерч.", "1.9 : 1"),
    ("plaque", "В плашке", "Плита держит логотип на пёстром фоне и на фото, где выворотка теряется.", "3.7 : 1"),
    ("mark", "Только приём", "Траектория без слова: плитка приложения, водяной знак, паттерн.", "2.5 : 1"),
    ("wordmark", "Только слово", "Для соподписи с партнёром, где приём мешает.", "5.0 : 1"),
    ("descriptor", "С дескриптором", "Первое знакомство: наружная реклама, презентация для партнёров.", "3.8 : 1"),
    ("micro", "Микро", "Для 18–24 px: полоса толще, самолёт крупнее. Иначе линия исчезает раньше слова.", "4.5 : 1"),
]


def layout_svg(slug, accent=ACC, ink=INK, height=None, fit=None, cls=""):
    fn = getattr(L, "lay_" + slug)
    if slug == "wordmark":
        parts, box = fn(ink)
    elif slug == "mark":
        parts, box = fn(accent)
    elif slug == "plaque":
        parts, box = fn(ink, accent)
    else:
        parts, box = fn(accent, ink)
    x0, y0, x1, y1 = box
    pad = 6.0
    w, h = (x1 - x0) + pad * 2, (y1 - y0) + pad * 2
    ratio = w / h
    if fit:
        style = "width:min(100%%,%dpx);height:auto" % round(fit * ratio)
    else:
        style = "height:%dpx;width:%dpx;max-width:100%%" % (height, round(height * ratio))
    return ('<svg class="lg %s" viewBox="%.2f %.2f %.2f %.2f" style="%s" role="img" '
            'aria-label="myTravel">%s</svg>'
            % (cls, x0 - pad, y0 - pad, w, h, style, "".join(parts)))


def tile_svg(bg, fg, size=512, radius=112, px=96, bold=False):
    raw = (L.tile(size=size, radius=radius, bg=bg, fg=fg, inset=0.74,
                  stroke=34.0, plane_scale=1.45) if bold
           else L.tile(size=size, radius=radius, bg=bg, fg=fg))
    inner = re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S).group(1)
    inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
    return ('<svg viewBox="0 0 %d %d" style="width:%dpx;height:%dpx" role="img" '
            'aria-label="Иконка myTravel">%s</svg>' % (size, size, px, px, inner))


def font_css():
    out = []
    for family, weight, name, urange in (
        ("IBM Plex Sans", "400 700", "IBMPlexSans-400-700-latin.woff2",
         "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+2000-206F,U+2122,U+2212"),
        ("IBM Plex Sans", "400 700", "IBMPlexSans-400-700-cyrillic.woff2",
         "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"),
        ("IBM Plex Mono", "400", "IBMPlexMono-400-latin.woff2",
         "U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+2122,U+2212"),
    ):
        p = FONTS / name
        if p.exists():
            out.append("@font-face{font-family:'%s';font-weight:%s;font-style:normal;"
                       "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');"
                       "unicode-range:%s}"
                       % (family, weight, base64.b64encode(p.read_bytes()).decode(), urange))
    return "".join(out)


def animations():
    """Инлайним анимации, снимая с них внешние обёртки."""
    cards = []
    meta = {
        "takeoff": ("Взлёт", "Для сплэша и первого экрана: полоса прочерчивается, "
                             "самолёт идёт по ней и отрывается, слово проявляется."),
        "loader": ("Ожидание", "Зацикленный индикатор для экрана «держим место»: "
                               "логотип статичен, живёт только приём."),
        "assemble": ("Сборка", "Слово собирается, полоса подчёркивает его последней."),
        "micro": ("Микро", "Наведение на логотип в шапке: короткий рывок вперёд."),
    }
    for slug, (title, note) in meta.items():
        f = ANIM / ("anim-%s.svg" % slug)
        if not f.exists():
            continue
        raw = f.read_text(encoding="utf-8")
        m = re.search(r"<svg([^>]*)>(.*)</svg>", raw, re.S)
        if not m:
            continue
        vb = re.search(r'viewBox="([^"]+)"', m.group(1))
        body = re.sub(r"<title>.*?</title>", "", m.group(2), flags=re.S)
        # цвета анимаций переводим в те же роли, что и у статики,
        # иначе переключатель цвета их не берёт
        for hexv, role in (("#a81e2d", "var(--c-accent)"), ("#2a211c", "var(--c-ink)"),
                           ("#fbf6ee", "var(--c-paper)"), ("#ffffff", "var(--c-paper)")):
            body = re.sub(hexv, role, body, flags=re.I)
        # у каждой анимации свои id и классы — изолируем, чтобы стили не смешались
        body = re.sub(r'\b(id|class)="([^"]*)"',
                      lambda mm: '%s="%s"' % (mm.group(1), " ".join(
                          slug + "-" + c for c in mm.group(2).split())), body)
        body = re.sub(r"url\(#([\w-]+)\)", lambda mm: "url(#%s-%s)" % (slug, mm.group(1)), body)
        body = re.sub(r"\.([A-Za-z][\w-]*)", lambda mm: ".%s-%s" % (slug, mm.group(1)), body) \
            if "<style" in body else body
        cards.append(
            '<article class="card anim" data-anim="%s">'
            '<div class="stage big" style="background:#fbf6ee">'
            '<svg viewBox="%s" style="width:min(100%%,420px);height:auto">%s</svg></div>'
            '<div class="idrow"><b>%s</b>'
            '<button type="button" class="replay">Проиграть заново</button></div>'
            '<p class="note">%s</p><code>logo/anim-%s.svg</code></article>'
            % (slug, vb.group(1) if vb else "0 0 100 100", body, title, note, slug))
    return cards


DONTS = [
    ("d-stretch", "Растягивать и сжимать", "transform:scaleX(1.4)"),
    ("d-rotate", "Наклонять и вращать", "transform:rotate(-8deg)"),
    ("d-shadow", "Добавлять тень и объём", "filter:drop-shadow(4px 5px 3px rgba(0,0,0,.5))"),
    ("d-recolor", "Перекрашивать по настроению", "filter:hue-rotate(150deg) saturate(2)"),
    ("d-swap", "Менять местами слово и приём", "transform:scaleX(-1)"),
    ("d-outline", "Обводить и запирать в рамку", "outline:3px solid #22285c;outline-offset:8px"),
]


def main():
    layouts = []
    for slug, title, note, ratio in LAYOUTS:
        layouts.append(
            '<article class="card"><div class="stage big">{big}</div>'
            '<div class="sizes"><div class="stage">{s34}</div><div class="stage">{s20}</div></div>'
            '<div class="bars">'
            '<div class="bar light">{b1}<span>Билеты · Отели · Туры · Виза</span></div>'
            '<div class="bar dark">{b2}<span>Билеты · Отели · Туры · Виза</span></div></div>'
            '<div class="idrow"><b>{t}</b><code>{r}</code></div><p class="note">{n}</p>'
            '<code class="files">mytravel-{s}.svg · -inverse · -mono · -var</code>'
            "</article>".format(
                big=layout_svg(slug, fit=88), s34=layout_svg(slug, height=34),
                s20=layout_svg(slug, height=20), b1=layout_svg(slug, height=26),
                b2=layout_svg(slug, height=26, accent="#e2707a", ink="#f3ede3"),
                t=title, r=ratio, n=note, s=slug))

    tiles = "".join(
        '<div class="tilecard"><div class="stage" style="background:%s">%s</div>'
        "<b>%s</b><code>%s</code></div>" % (bgpage, tile_svg(bg, fg), lbl, f)
        for bg, fg, lbl, f, bgpage in (
            ("#a81e2d", "#fbf6ee", "Иконка приложения", "app-icon.svg", "#f4f3f1"),
            ("#a81e2d", "#fbf6ee", "Плитка гранат", "tile-anor.svg", "#f4f3f1"),
            ("#22285c", "#fbf6ee", "Плитка индиго", "tile-indigo.svg", "#f4f3f1"),
            ("#1b1512", "#fbf6ee", "Плитка тёмная", "tile-ink.svg", "#f4f3f1"),
            ("#fbf6ee", "#a81e2d", "Плитка светлая", "tile-light.svg", "#f4f3f1"),
        ))
    favicons = "".join(
        '<div class="favcell">%s<i>%d px</i></div>'
        % (tile_svg("#a81e2d", "#fbf6ee", size=32, radius=7, px=px, bold=True), px)
        for px in (16, 24, 32, 48))

    donts = "".join(
        '<div class="dontcard"><div class="stage dont"><span style="%s">%s</span></div>'
        "<p class=\"note\">%d. %s</p></div>" % (style, layout_svg("primary", height=30), i, label, )
        for i, (cls, label, style) in enumerate(DONTS, 1))

    chips = "".join(
        '<button type="button" class="chip" style="--sw:%s">%s</button>' % (s[1], s[0])
        for s in SCHEMES)
    schemes_js = ",".join('["%s","%s","%s"]' % (s[1], s[2], s[3]) for s in SCHEMES)

    page = PAGE
    for key, val in (("__FONTS__", font_css()), ("__CHIPS__", chips),
                     ("__SCHEMES__", schemes_js), ("__LAYOUTS__", "".join(layouts)),
                     ("__TILES__", tiles), ("__FAVICONS__", favicons),
                     ("__DONTS__", donts), ("__ANIMS__", "".join(animations())),
                     ("__CLEAR__", layout_svg("primary", fit=70))):
        page = page.replace(key, val)
    OUT.write_text(page, encoding="utf-8")
    print("✓ %s — %d КБ, компоновок %d, анимаций %d"
          % (OUT, OUT.stat().st_size // 1024, len(LAYOUTS), len(animations())))


PAGE = """<title>myTravel — логотип</title>
<style>
__FONTS__
:root{--paper:#f4f3f1;--surface:#fff;--fg:#1b1a18;--muted:#6f6b65;--line:#e3e0dc;
 --line-strong:#cdc8c1;--c-accent:#a81e2d;--c-ink:#2a211c;--c-paper:#fbf6ee}
@media (prefers-color-scheme:dark){:root{--paper:#131211;--surface:#1c1a18;--fg:#f2efea;
 --muted:#a8a29b;--line:#302c29;--line-strong:#48433f}}
:root[data-theme="dark"]{--paper:#131211;--surface:#1c1a18;--fg:#f2efea;--muted:#a8a29b;
 --line:#302c29;--line-strong:#48433f}
:root[data-theme="light"]{--paper:#f4f3f1;--surface:#fff;--fg:#1b1a18;--muted:#6f6b65;
 --line:#e3e0dc;--line-strong:#cdc8c1}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--fg);
 font:400 16px/1.55 "IBM Plex Sans",system-ui,-apple-system,sans-serif;
 -webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px 96px}
header{padding:44px 0 8px;max-width:70ch}
h1{font-size:clamp(28px,4vw,40px);line-height:1.1;letter-spacing:-.02em;margin:0 0 12px;
 font-weight:600;text-wrap:balance}
.lede{color:var(--muted);margin:0 0 8px}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
 font-weight:600;margin:0 0 6px}
.snote{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:70ch}
section{margin-top:52px}
.hero{background:var(--c-paper);border-radius:14px;padding:44px 32px;display:flex;
 justify-content:center;margin:24px 0 8px;border:1px solid var(--line)}
.hero svg{width:min(100%,620px);height:auto}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;
 padding:18px;display:flex;flex-direction:column;gap:10px}
.stage{display:flex;align-items:center;justify-content:center;min-width:0;overflow:hidden;
 background:var(--c-paper);border-radius:8px;padding:16px;
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.06)}
.stage.big{min-height:132px;padding:20px}
.sizes{display:flex;gap:10px}
.sizes .stage{flex:1;min-height:62px;padding:12px}
.lg{display:block;min-width:0;flex:0 1 auto}
.bars{display:flex;flex-direction:column;gap:6px}
.bar{display:flex;align-items:center;gap:14px;padding:9px 14px;border-radius:8px;
 overflow:hidden;min-width:0}
.bar span{font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar.light{background:#fff;box-shadow:inset 0 0 0 1px var(--line)}
.bar.light span{color:#8b857c}
.bar.dark{background:#161311}.bar.dark span{color:#8b8177}
.idrow{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;padding-top:6px;
 border-top:1px solid var(--line)}
.idrow b{font-size:15px}
.note{font-size:13px;color:var(--muted);margin:0}
code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--muted)}
code.files{font-size:11px}
.tilecard,.dontcard{background:var(--surface);border:1px solid var(--line);
 border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:10px;
 align-items:center;text-align:center}
.tilecard .stage{width:100%;min-height:130px}
.tilecard b{font-size:14px}
.favrow{display:flex;gap:22px;align-items:flex-end;background:var(--surface);
 border:1px solid var(--line);border-radius:12px;padding:20px;flex-wrap:wrap}
.favcell{display:flex;flex-direction:column;align-items:center;gap:8px}
.favcell i{font:400 11px/1 "IBM Plex Mono",monospace;color:var(--muted);font-style:normal}
.dont{position:relative;width:100%;min-height:104px}
.dont::after{content:"";position:absolute;inset:10px;
 background:linear-gradient(to top right,transparent calc(50% - 1px),#a81e2d calc(50% - 1px),
 #a81e2d calc(50% + 1px),transparent calc(50% + 1px))}
.clear{position:relative;display:inline-block;padding:44px}
.clear::before{content:"";position:absolute;inset:0;border:1px dashed var(--c-accent)}
.clear::after{content:"½X";position:absolute;top:6px;left:8px;
 font:500 11px/1 "IBM Plex Mono",monospace;color:var(--c-accent)}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:8px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line)}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
 font-weight:600}
.bar-top{position:sticky;top:0;z-index:5;background:var(--paper);
 border-bottom:1px solid var(--line);padding:10px 0}
.bar-top .inner{max-width:1240px;margin:0 auto;padding:0 24px;display:flex;gap:8px;
 align-items:center;flex-wrap:wrap}
.bar-top .t{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
button{font:inherit;font-size:13px;color:var(--fg);background:transparent;
 border:1px solid var(--line-strong);border-radius:6px;padding:6px 12px;cursor:pointer;
 min-height:34px}
button:hover{border-color:var(--fg)}
button:focus-visible{outline:2px solid var(--fg);outline-offset:2px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:4px 11px}
.chip::before{content:"";width:11px;height:11px;border-radius:50%;background:var(--sw);
 box-shadow:inset 0 0 0 1px rgba(0,0,0,.18)}
.chip[aria-pressed="true"]{border-color:var(--fg);background:var(--surface);font-weight:600}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;
 color:var(--muted)}
footer a{color:var(--fg)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="bar-top"><div class="inner">
 <span class="t">Цвет</span>__CHIPS__
 <span class="t" style="margin-left:10px">Страница</span>
 <button type="button" id="theme">Светлая / тёмная</button>
</div></div>

<div class="wrap">
<header>
 <h1>myTravel — логотип</h1>
 <p class="lede">Утверждённый знак: слово ведёт композицию, под ним взлётная полоса,
 которая за последней буквой отрывается от земли. Ниже — все компоновки, цвета,
 иконки, анимация и правила.</p>
</header>

<div class="hero">__CLEAR__</div>
<p class="note" style="text-align:center">Охранное поле — половина высоты блока
со всех сторон. В него не заходят текст, другие логотипы и край макета.</p>

<section>
 <h2>Компоновки</h2>
 <p class="snote">Восемь положений. У каждого — крупный вид, проверка в 34 и 20 пикселях
 и вид в шапке приложения на светлом и тёмном. Файлы идут в четырёх версиях:
 основная, выворотка, монохром через <code>currentColor</code> и версия с
 CSS-переменными для любого цвета.</p>
 <div class="grid">__LAYOUTS__</div>
</section>

<section>
 <h2>Иконки и плитки</h2>
 <p class="snote">В плитке живёт только приём: слово в квадрате мельче 96 px
 нечитаемо. Скругление иконки приложения ставит система — в файле углы прямые.</p>
 <div class="grid">__TILES__</div>
 <div class="favrow" style="margin-top:16px">__FAVICONS__</div>
</section>

<section>
 <h2>Анимация</h2>
 <p class="snote">Каждая — самодостаточный SVG: стили внутри файла, внешних
 зависимостей нет. При включённом «уменьшить движение» анимация выключается,
 логотип остаётся в финальном кадре.</p>
 <div class="grid">__ANIMS__</div>
</section>

<section>
 <h2>Так нельзя</h2>
 <p class="snote">Шесть запретов, которые ломают логотип чаще всего.
 Полный список — в правилах использования.</p>
 <div class="grid">__DONTS__</div>
</section>

<section>
 <h2>Минимальные размеры</h2>
 <table>
  <thead><tr><th>Компоновка</th><th>Экран</th><th>Печать</th><th>Когда</th></tr></thead>
  <tbody>
   <tr><td>Основной</td><td>120 px по ширине</td><td>32 мм</td><td>Везде, где хватает места</td></tr>
   <tr><td>Компактный</td><td>96 px</td><td>26 мм</td><td>Узкая шапка, мобильный экран</td></tr>
   <tr><td>Вертикальный</td><td>72 px</td><td>20 мм</td><td>Квадратные форматы, вывеска</td></tr>
   <tr><td>Микро</td><td>64 px</td><td>—</td><td>Высота блока 18–24 px</td></tr>
   <tr><td>Только приём</td><td>24 px</td><td>8 мм</td><td>Плитка, водяной знак</td></tr>
   <tr><td>Плитка / favicon</td><td>16 px</td><td>—</td><td>Вкладка, аватарка</td></tr>
  </tbody>
 </table>
</section>

<footer>
 <p><a href="all.html">Все материалы</a> ·
 <a href="brand/brandbook.html">Брендбук</a> ·
 <a href="brand/logo/">Файлы логотипа</a> ·
 <a href="brand/docs/usage-rules.html">Правила использования</a> ·
 <a href="choose.html">Архив: 24 варианта, из которых выбирали</a></p>
 <p>Контуры букв вырезаны из Schibsted Grotesk 700 и переведены в кривые: шрифт
 для отрисовки не нужен. Единица системы — капитальная высота, равная 100;
 полоса лежит на 48 ниже базовой линии, толщина 23, отрыв — плюс 182 по горизонтали
 и минус 100 по вертикали.</p>
</footer>
</div>

<script>
(function(){
 var S=[__SCHEMES__],root=document.documentElement;
 var chips=[].slice.call(document.querySelectorAll('.chip'));
 function apply(n){var s=S[n];if(!s)return;
  root.style.setProperty('--c-accent',s[0]);root.style.setProperty('--c-ink',s[1]);
  root.style.setProperty('--c-paper',s[2]);
  chips.forEach(function(c,i){c.setAttribute('aria-pressed',String(i===n))});}
 chips.forEach(function(c,i){c.addEventListener('click',function(){apply(i)})});
 apply(0);
 document.getElementById('theme').addEventListener('click',function(){
  var d=root.getAttribute('data-theme')==='dark'||(!root.hasAttribute('data-theme')&&
   matchMedia('(prefers-color-scheme:dark)').matches);
  root.setAttribute('data-theme',d?'light':'dark');});
 document.addEventListener('click',function(e){
  var b=e.target.closest('.replay');if(!b)return;
  var card=b.closest('.anim'),svg=card.querySelector('.stage svg');
  var clone=svg.cloneNode(true);svg.parentNode.replaceChild(clone,svg);});
})();
</script>
"""


if __name__ == "__main__":
    main()
