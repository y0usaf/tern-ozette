# Ozette

Ozette's structure, type, shapes, rails and motion as a Tern plugin. It sits over whatever theme is selected and reads only the theme's variables, so colour always comes from the theme.

The UI Menu loads `ozette-answer-bubbles.css` only with Ozette and answer bubbles enabled, and `ozette-bot-you.css` only with Ozette and your message bubbles enabled. Assistant blocks and bot-user card colours live in those optional sheets; turning bubbles off leaves the typography, code, images and lists intact. Classic Tern user cards retain their normal Ozette treatment. YoRHa follows the same rule: `yorha-answer-bubbles.css`, `yorha-bot-answer-bubbles.css` and `yorha-bot-you.css` load only with YoRHa and answer bubbles, bot answer bubbles or your message bubbles enabled.

## Design note: declared backgrounds stay real

Never make a surface's declared background colour transparent where Tern computes contrast from it. The terminal's automatic contrast correction measures every cell against `--tv-bg`; if `--tv-bg` is `transparent`, Tern measures against nothing and leaves pale text unreadable on light glass. Glass is done by layering instead: the element's own `background` goes transparent and the one canvas behind everything carries the tint and dot grid, while `--tv-bg` (and the theme's other surface colours) keep the colour the eye actually sees.

The look canvas is opaque with transparent window off: Ozette keeps its theme-derived dot-grid paper, and YoRHa keeps its light paper or dark ink. The shared transparent window option alone clears the canvas; turning it off restores the look.

Font declarations never use `!important`. Ozette keeps its local serif accents without changing the stock secondary UI family; mono labels read Tern's configured code font. YoRHa's UI defaults are non-important and do not override configured UI or terminal fonts. The shared Glass options control sent-message frost and composer frost independently.

## Grok

`grok.css` is a standalone look over stock Tern: neutral light/dark surfaces, generous sans-serif text, rounded code, a 20px composer and pill controls. It does not load Ozette or YoRHa. Tern's existing hover/focus actions remain keyboard accessible.

The UI Menu loads each `grok-*-bubbles.css` sheet only when Grok and that surface's bubble option are enabled; `grok-bot-you.css` follows the bot's your-message toggle. Frost belongs to the shared frost options, not this look. Switching looks removes all Grok sheets without changing the selected theme.

Optional `grok-avatars.css` contains three original SVG illustrations as inline CSS images: a lavender blob, a golden bean and a mint sprout, each with its own little face. These are our drawings, not xAI assets. There is no extraction, image generator or app dependency. Tern cannot resolve stylesheet-relative image URLs, so the tiny illustrations are self-contained data URLs. CSS adds a gentle bob and disables it for reduced motion; Grok's JavaScript face animation is not reproduced.
