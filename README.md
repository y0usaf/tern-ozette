# Ozette

Ozette's structure, type, shapes, rails and motion as a Tern plugin. It sits over whatever theme is selected and reads only the theme's variables, so colour always comes from the theme.

## Design note: declared backgrounds stay real

Never make a surface's declared background colour transparent where Tern computes contrast from it. The terminal's automatic contrast correction measures every cell against `--tv-bg`; if `--tv-bg` is `transparent`, Tern measures against nothing and leaves pale text unreadable on light glass. Glass is done by layering instead: the element's own `background` goes transparent and the one canvas behind everything carries the tint and dot grid, while `--tv-bg` (and the theme's other surface colours) keep the colour the eye actually sees.
