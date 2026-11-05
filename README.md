# Ozette

Ozette's structure, type, shapes, rails and motion as a Tern plugin. It sits over whatever theme is selected and reads only the theme's variables, so colour always comes from the theme.

The UI Menu loads `ozette-answer-bubbles.css` only with Ozette and answer bubbles enabled, and `ozette-bot-you.css` only with Ozette and your message bubbles enabled. These optional sheets keep message containers out of the base look; turning bubbles off leaves the typography, code, images and lists intact.

## Design note: declared backgrounds stay real

Never make a surface's declared background colour transparent where Tern computes contrast from it. The terminal's automatic contrast correction measures every cell against `--tv-bg`; if `--tv-bg` is `transparent`, Tern measures against nothing and leaves pale text unreadable on light glass. Glass is done by layering instead: the element's own `background` goes transparent and the one canvas behind everything carries the tint and dot grid, while `--tv-bg` (and the theme's other surface colours) keep the colour the eye actually sees.

The canvas takes its colour from `--oz-page`, not `--page` directly. Another plugin may set `--page: transparent` (the Transparent plugin does), and `rgb(from transparent r g b / 92%)` is black. `--oz-page` mixes `--page` with 1% of `--tn-page` in premultiplied sRGB: an opaque `--page` (a file theme's own) wins, a cleared one falls back to the selected theme's page colour.
