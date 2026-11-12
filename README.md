# tern-ozette

tern-ozette holds the CSS for four Tern looks: Ozette, YoRHa, Grok and Mini.

A look restyles stock Tern through its own selectors and variables; colour always comes from the selected theme. finix copies these sheets into the UI Menu plugin (`~/.config/tern/plugins/ui-menu/snippets/`), and the UI Menu's Looks picker loads them. Nothing here needs building.

## Looks

- **Ozette**: square paper surfaces with offset shadows, serif chat, code cards, label tabs and a dot-grid canvas.
- **YoRHa**: two-tone menus after NieR: Automata's YoRHa screens: light paper or dark ink.
- **Grok**: a standalone look after the Grok Bot app: neutral surfaces, rounded code, a centred 960px composer, and Grok Bot's own menus, dialogs, keycaps, bottom-right notification toasts that say what the bot is doing ("CU-Bot is waiting for you", "CU-Bot finished working"), answered question cards and shimmering working phrase. It hides the composer's model and effort selectors; `/model` still works.
- **Mini**: stock layout with small radii, short transitions, flat borders and no decorative animation. It sets no colours or fonts.

## Sheets

| Sheet | Loaded when |
| --- | --- |
| `rail.css`, `settings.css` | always: right-rail base and native picker sizing |
| `ozette.css`, `motion.css`, `cmus.css` | Ozette is selected |
| `ozette-answer-bubbles.css`, `ozette-bot-you.css` | Ozette plus answer bubbles / your-message bubbles |
| `yorha.css` | YoRHa is selected |
| `yorha-answer-bubbles.css`, `yorha-bot-answer-bubbles.css`, `yorha-bot-you.css` | YoRHa plus the matching bubble option |
| `grok.css` | Grok is selected |
| `grok-*-bubbles.css`, `grok-bot-you.css` | Grok plus the matching bubble option |
| `mini.css` | Mini is selected |

Ozette, YoRHa and Grok still ship their own bubble sheets. Departure, Automata, Botanical, Braun, Folio, Blueprint, Eink and Phosphor do not: their `--omp-user-*` and `--omp-reply-*` variables in the look sheet feed `bubbles.css`, a look layer the UI Menu loads only while one of those eight is selected. It draws the user frame and keeps replies plain; every other look keeps the stock bubble snippets untouched.

`plugin.toml` also makes the repo a plain Ozette plugin (`ozette.css`, `motion.css`, `cmus.css`) for a Tern without the UI Menu.

Bot avatars are not part of any look: omp-bot's Tern plugin draws them under every look. `grok-motion.json` maps the Grok app's animations to Tern surfaces; it is reference only and nothing loads it.

## Light and dark

Light/dark following is Tern's own **Appearance → System** setting (`"theme": "System"` in `settings.json`). Every look follows it. Tern 0.9.11 picks Light when `theme` is missing, so keep that key when editing theme settings.

## Rules for editing

- Use Tern's stock selectors and variables; add look-only variables only for colour transforms Tern has no variable for.
- Every colour comes from the active theme: surfaces from `--tn-page`, `--tbl-head` and `--code-bg`, ink from `--t1` with a look lightness, muted text from `--t2`/`--t3` mixed toward the look's ink, and each look's own hue from an ANSI slot of that hue (`--ansi1` red, `--ansi2` green, `--ansi3` amber, `--ansi4` blue). Bodies carry no colour literals; only achromatic shadow, scrim and glass-highlight alphas stay black or white.
- Never give a reply its own frame: the user message is the framed element, replies are plain text. Set `--omp-user-*` and `--omp-reply-*` instead of drawing boxes.
- Never set `--tv-bg` or another surface colour to `transparent`. Tern measures terminal text contrast against it, so pale text becomes unreadable. For glass, make the element's `background` transparent and tint the canvas behind it instead.
- Never use `!important` on fonts; looks must not override configured UI or terminal fonts.
- Ekko (the rail plugin) owns the rail's layout and data; looks restyle only its visuals, and leave Tern's phone shell to its stock layout.
- Before shipping, run `nix run .` from this checkout (`nix run . -- --update LOOK` accepts a look's new shots): it renders every look × light/dark × transparent window off/on in a private headless Tern against `check/chat.jsonl` and prints a JSON report of text below WCAG AA (on a black desktop, unless stock Tern is as low), pixels changed from `check/ref/`, CSS over `check/budget.json`, and classes stock Tern never styles.
