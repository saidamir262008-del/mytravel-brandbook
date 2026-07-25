# myTravel — брендбук

Направление **ABR** (абрбандӣ, икат): гранат, бухарское индиго, тёплая бумага
и один-единственный «смелый» приём — ступенчатая кромка `abr-edge`.
Всё остальное тихое и дисциплинированное.

**Начните отсюда:** откройте [`brandbook.html`](brandbook.html) двойным кликом.
Один файл, работает офлайн, шрифты и графика внутри. Ничего ставить не нужно.

---

## Что где лежит

```
brand/
├── brandbook.html         главный интерактивный брендбук (самодостаточный)
├── tokens/
│   ├── tokens.css         ИСТОЧНИК ПРАВДЫ: цвет, типографика, отступы, тени
│   └── tokens.json        то же для Figma Tokens Studio и Tailwind
├── logo/                  8 версий логотипа, текст в кривых
├── icons/                 14 иконок категорий + 12 интерфейсных + preview.html
├── components/
│   └── ui-kit.html        живые компоненты: поиск, карточки, оплата, ваучер
├── docs/
│   ├── voice-and-tone.md  тон, словарь, готовые тексты на ru / uz / en
│   ├── usage-rules.md     что можно и чего нельзя с логотипом и цветом
│   └── accessibility.md   контрасты, тап-зоны, фокус, чек-лист приёмки
├── fonts/                 woff2 (OFL) + собранный fonts-inline.css
└── tools/                 скрипты пересборки
```

---

## Разработчику: как подключить

### 1. Токены

```html
<link rel="stylesheet" href="tokens/tokens.css">
```

Дальше в своём CSS — только переменные, никаких сырых хексов:

```css
.button-primary {
  background: var(--mt-accent);
  color: var(--mt-accent-fg);
  min-height: var(--mt-tap-min);
  border-radius: var(--mt-radius-sm);
  font: var(--mt-weight-medium) var(--mt-text-16) / var(--mt-lh-16) var(--mt-font-text);
}
```

### 2. Тёмная тема

Тема переключается атрибутом на `<html>`. Хост-приложение ставит его само —
так у пользователя остаётся ручной выбор, а не только системная настройка:

```js
document.documentElement.dataset.theme =
  localStorage.getItem('theme') ||
  (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
```

### 3. Шрифты

Alegreya (display), IBM Plex Sans (текст), IBM Plex Mono (цифры) — все под OFL,
лицензия для коммерческого использования не требуется.

Подключайте субсеты `latin`, `latin-ext`, `cyrillic` и **обязательно
`cyrillic-ext`** — в нём живут `Қ`, `Ғ`, `Ҳ`. Без него узбекская кириллица
разъедется по разным шрифтам.

Готовые woff2 лежат в `fonts/`. Проверенный факт: `oʻ` и `gʻ` — это
**U+02BB** (modifier letter turned comma), а не апостроф. Шрифты Onest,
Manrope, Rubik, Golos Text, PT Sans и Wix Madefor этот символ **не содержат** —
поэтому они отклонены, не берите их «на замену».

### 4. Цифры

Цены, даты, номера рейсов и паспортов — только моноширинными табличными:

```html
<span class="mt-num">4 850 000 сум</span>
```

Класс `.mt-num` уже есть в `tokens.css`.

### 5. Иконки

Иконки — штриховые, на `currentColor`. Цвет задаётся снаружи, размер — 24 px
(или 16 px, но не мельче 20 px без перерисовки штриха, см. `icons/README.md`).

`currentColor` работает только у **инлайнового** SVG: через `<img src>` цвет
не наследуется. Поэтому вклеивайте иконку в разметку или соберите спрайт —
каждый файл кладётся в `<symbol id="i-имя">` с переносом атрибутов
`fill`/`stroke`/`stroke-width` с корневого `<svg>` (иначе штриховая иконка
станет чёрной заливкой). Ровно это делает `tools/build-brandbook.py` —
функции `inner_svg()` и `root_attrs()` можно взять как образец.

```html
<svg class="icon" width="24" height="24" aria-hidden="true"><use href="#i-cat-flights"/></svg>
```

`icons/preview.html` показывает весь набор в 24 и 16 px сразу — удобно для приёмки.

### 6. Tailwind

Готовый фрагмент для `theme.extend` — в `tokens/tokens.json`, ключ `tailwind`.

---

## Дизайнеру

- Палитра, шкала и отступы — в `tokens/tokens.json`, импортируется в Figma через Tokens Studio.
- Перед сдачей макета пройдите чек-лист в конце [`docs/usage-rules.md`](docs/usage-rules.md).
- Контрасты не подбирайте на глаз: все допустимые пары посчитаны в [`docs/accessibility.md`](docs/accessibility.md).

## Редактору

- Тон, словарь «пиши так / не пиши так» и готовые тексты на трёх языках — в [`docs/voice-and-tone.md`](docs/voice-and-tone.md).
- Узбекский текст на 10–20% длиннее русского. Проверяйте кнопки именно на нём.

---

## Пересборка

Скрипты нужны, только если вы поменяли токены, логотип или иконки.
Обычная работа с брендбуком их не требует.

```bash
# Вклеить в brandbook.html токены, логотипы и иконки. Сеть не нужна.
python3 tools/build-brandbook.py

# Скачать шрифты с Google Fonts и вшить их в brandbook.html и ui-kit.html как base64.
# Нужна сеть. Base64 — потому что Chrome блокирует загрузку шрифтов по file:// (CORS),
# а брендбук должен открываться двойным кликом офлайн.
python3 tools/build-fonts.py
```

Порядок важен: сначала `build-brandbook.py`, потом `build-fonts.py`.

Перерисовка логотипа (нужен `fonttools`, обычно не требуется):

```bash
python3 -m venv venv && ./venv/bin/pip install fonttools brotli
curl -sLo Alegreya.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/alegreya/Alegreya%5Bwght%5D.ttf"
./venv/bin/python tools/build-logo.py Alegreya.ttf
```

---

## Что этот брендбук осознанно не покрывает

Честный список, чтобы не считать его законченным:

- **Фотография.** Правил кадрирования, затемнения и работы с плохими картинками от поставщиков нет, хотя travel-продукт на них держится.
- **Движение.** Есть токены длительности и кривой, но ни один переход не описан.
- **Печать в CMYK.** Гранат не сведён к Pantone, пробы не делались.
- **Тёмная тема** получена механическим осветлением и требует отдельного прохода.
- **Иконки в 16 px.** Шесть из 26 на этом размере читаются слабо — список в `icons/README.md`.

Подробнее — раздел «Самокритика» в конце `brandbook.html`.

---

## Лицензии

- Шрифты Alegreya, IBM Plex Sans, IBM Plex Mono — SIL Open Font License 1.1 (`fonts/OFL.txt`).
- Логотип, иконки, тексты и токены — собственность myTravel.
