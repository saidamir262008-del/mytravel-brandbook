#!/usr/bin/env python3
"""
Превращает docs/*.md в читаемые HTML-страницы для GitHub Pages.

Браузер не показывает .md, а скачивает его — на сайте это выглядит как поломка.
Конвертер намеренно маленький: поддерживает ровно то, что есть в наших документах —
заголовки, абзацы, таблицы, списки, чекбоксы, код, цитаты, разделители,
жирный, курсив, ссылки и inline-код.
"""
import html
import pathlib
import re
import sys

# Документы собираются в исходниках: копия сайта пересоздаётся сборкой
HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent.parent          # brand/
DOCS = SITE / "docs"

CSS = """
:root{--paper:#fbf6ee;--surface:#fff;--fg:#2a211c;--muted:#665d53;--line:#e6ded1;
 --accent:#a81e2d;--link:#22285c}
@media (prefers-color-scheme:dark){
 :root{--paper:#1b1512;--surface:#241c18;--fg:#f3ede3;--muted:#c2b6a6;
       --line:#3b302a;--accent:#d9525c;--link:#a8b0e0}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--fg);
 font:400 16px/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
 -webkit-font-smoothing:antialiased}
main{max-width:82ch;margin:0 auto;padding:32px 24px 96px}
nav.top{border-bottom:1px solid var(--line);background:var(--surface)}
nav.top div{max-width:82ch;margin:0 auto;padding:12px 24px;font-size:14px;
 display:flex;gap:16px;flex-wrap:wrap}
nav.top a{color:var(--fg)}
h1{font-size:32px;line-height:1.2;letter-spacing:-.02em;margin:28px 0 16px}
h2{font-size:24px;line-height:1.25;margin:40px 0 12px;padding-top:14px;
 border-top:1px solid var(--line)}
h3{font-size:18px;margin:28px 0 8px}
h4{font-size:16px;margin:20px 0 6px}
p{margin:0 0 14px}
a{color:var(--link)}
ul,ol{margin:0 0 14px;padding-left:22px}
li{margin:0 0 6px}
code{font-family:ui-monospace,"SF Mono","IBM Plex Mono",monospace;font-size:.9em;
 background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:1px 5px}
pre{background:var(--surface);border:1px solid var(--line);border-radius:8px;
 padding:14px 16px;overflow-x:auto;margin:0 0 16px}
pre code{background:none;border:0;padding:0;font-size:13px;line-height:1.55}
blockquote{margin:0 0 16px;padding:8px 16px;border-left:3px solid var(--accent);
 color:var(--muted)}
hr{border:0;border-top:1px solid var(--line);margin:32px 0}
.tablewrap{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);
 vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:12px;text-transform:uppercase;
 letter-spacing:.04em}
strong{font-weight:600}
"""

INLINE = [
    (re.compile(r"`([^`]+)`"), lambda m: "<code>%s</code>" % html.escape(m.group(1))),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
     lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2)), html.escape(m.group(1)))),
    (re.compile(r"\*\*([^*]+)\*\*"), lambda m: "<strong>%s</strong>" % html.escape(m.group(1))),
    (re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])"),
     lambda m: "<em>%s</em>" % html.escape(m.group(1))),
]


def inline(text):
    """Инлайн-разметка. Экранируем всё, кроме того, что сами превратили в теги."""
    slots = []

    def stash(rendered):
        slots.append(rendered)
        return "\x00%d\x00" % (len(slots) - 1)

    for pattern, render in INLINE:
        text = pattern.sub(lambda m: stash(render(m)), text)
    text = html.escape(text)
    # Плейсхолдеры бывают вложенными (ссылка, подпись которой — код),
    # поэтому раскрываем их в цикле, а не за один проход.
    for _ in range(6):
        new_text = re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], text)
        if new_text == text:
            break
        text = new_text
    return text


def fix_links(text):
    return re.sub(r'href="([^"]+)\.md(#[^"]*)?"', r'href="\1.html\2"', text)


def convert(md):
    out, lines, i = [], md.splitlines(), 0
    list_stack = []

    def close_lists():
        while list_stack:
            out.append("</%s>" % list_stack.pop())

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            close_lists()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue

        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < len(lines) \
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            close_lists()
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join("<th>%s</th>" % inline(c) for c in head)
            tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                         for r in rows)
            out.append('<div class="tablewrap"><table><thead><tr>%s</tr></thead>'
                       "<tbody>%s</tbody></table></div>" % (th, tb))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_lists()
            out.append("<h%d>%s</h%d>" % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
            i += 1
            continue

        if re.match(r"^---+\s*$", line):
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        if line.startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
            continue

        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            tag = "ul" if m.group(2) in "-*" else "ol"
            depth = len(m.group(1)) // 2
            while len(list_stack) > depth + 1:
                out.append("</%s>" % list_stack.pop())
            if len(list_stack) == depth:
                list_stack.append(tag)
                out.append("<%s>" % tag)
            body = m.group(3)
            body = re.sub(r"^\[ \]\s*", "☐ ", body)
            body = re.sub(r"^\[[xX]\]\s*", "☑ ", body)
            out.append("<li>%s</li>" % inline(body))
            i += 1
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        close_lists()
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|```|>|\s*([-*]|\d+\.)\s|---+\s*$|\s*\|)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    close_lists()
    return "\n".join(out)


NAV = ('<nav class="top"><div><a href="../../index.html">← Логотип</a>'
       '<a href="../brandbook.html">Брендбук</a>'
       '<a href="voice-and-tone.html">Тон и слова</a>'
       '<a href="usage-rules.html">Правила использования</a>'
       '<a href="accessibility.html">Доступность</a></div></nav>')


def main():
    if not DOCS.exists():
        raise SystemExit("нет папки %s" % DOCS)
    made = 0
    for md in sorted(DOCS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title = next((l.lstrip("# ").strip() for l in text.splitlines()
                      if l.startswith("# ")), md.stem)
        body = fix_links(convert(text))
        page = ("<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                "<title>%s — myTravel</title><style>%s</style></head><body>%s"
                "<main>%s</main></body></html>"
                % (html.escape(title), CSS, NAV, body))
        (DOCS / (md.stem + ".html")).write_text(page, encoding="utf-8")
        made += 1
        print("   ✓ docs/%s.html" % md.stem)

    # ссылки на .md внутри сайта переводим на .html
    for page in list(SITE.rglob("*.html")):
        if page.parent == DOCS:
            continue
        t = page.read_text(encoding="utf-8")
        n = fix_links(t)
        if n != t:
            page.write_text(n, encoding="utf-8")
            print("   · ссылки поправлены: %s" % page.relative_to(SITE))
    print("готово: %d документов" % made)


if __name__ == "__main__":
    sys.exit(main())
