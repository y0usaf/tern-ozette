# Ozette

Ozette's structure, type, shapes, rails and motion as a Tern plugin. It sits over whatever theme is selected and reads only the theme's variables, so colour always comes from the theme.

The UI Menu loads `ozette-answer-bubbles.css` only with Ozette and answer bubbles enabled, and `ozette-bot-you.css` only with Ozette and your message bubbles enabled. Assistant blocks and bot-user card colours live in those optional sheets; turning bubbles off leaves the typography, code, images and lists intact. Classic Tern user cards retain their normal Ozette treatment. YoRHa follows the same rule: `yorha-answer-bubbles.css`, `yorha-bot-answer-bubbles.css` and `yorha-bot-you.css` load only with YoRHa and answer bubbles, bot answer bubbles or your message bubbles enabled.

The menu has no separate Pixel variant or legacy “Grok chat” typography preset. Plain omp and bot answer bubbles remain separate shared choices; their small look-specific sheets have hidden dependency gates rather than extra visible controls.

## Design note: declared backgrounds stay real

Never make a surface's declared background colour transparent where Tern computes contrast from it. The terminal's automatic contrast correction measures every cell against `--tv-bg`; if `--tv-bg` is `transparent`, Tern measures against nothing and leaves pale text unreadable on light glass. Glass is done by layering instead: the element's own `background` goes transparent and the one canvas behind everything carries the tint and dot grid, while `--tv-bg` (and the theme's other surface colours) keep the colour the eye actually sees.

The look canvas is opaque with transparent window off: Ozette keeps its theme-derived dot-grid paper, and YoRHa keeps its light paper or dark ink. The shared transparent window option alone clears the canvas; turning it off restores the look.

Font declarations never use `!important`. Ozette keeps its local serif accents without changing the stock secondary UI family; mono labels read Tern's configured code font. YoRHa's UI defaults are non-important and do not override configured UI or terminal fonts. The shared Glass options control sent-message frost and composer frost independently.

Ozette and YoRHa use Tern's stock surface, ink, syntax and font roles directly instead of parallel aliases. Look-only variables remain for genuinely distinct palette transforms, solid window ground and motion timing. Remaining priority flags protect the existing runtime palette, rail-plugin styles and stock image limits; they never force typography.

## Grok

`grok.css` is a standalone look over stock Tern: neutral light/dark surfaces, generous sans-serif text, rounded code, a 20px composer and pill controls. It does not load Ozette or YoRHa. Tern's existing hover/focus actions remain keyboard accessible.

The UI Menu loads each `grok-*-bubbles.css` sheet only when Grok and that surface's bubble option are enabled; `grok-bot-you.css` follows the bot's your-message toggle. Frost belongs to the shared frost options, not this look. Switching looks removes all Grok sheets without changing the selected theme.

Optional `grok-avatars.css` replays faithfully redrawn Grok Bot bodies, cut-out eyes and the four-second Idle_B motion. Six lossless PNG atlases cover Lloyd (cyan cloud), Sol (violet bean), random (orange teardrop), CU-Bot (magenta capsule), baobot (yellow square) and Regal (green clover); helpers/defaults reuse Sol. Each frame is 128px for a maximum 64px display. The 240-sample, 60fps cycle reuses 73–77 pixel-identical frames per bot. The six atlases total 552,489 bytes; the dark palette is shared by both modes, whose source colours differ by only 1–2 RGB values. Reduced motion holds the first frame.

The PNGs were rasterized from our vector reconstructions, not copied from the app's image files. No app code, reference library, drawing generator or reference probe ships. Nix installs the six atlases inside the UI Menu plugin; its CSS loader resolves their plugin-relative URLs. Directly injected CSS needs absolute URLs, while the plugin loader rejects them. CSS probes also found unsupported WebP images, SVG URL masks, `:has()`, separate background-position axes and custom-property/percentage sprite-keyframe positions, so this look uses compact PNG grids and literal pixel coordinates.

## Mini

`mini.css` keeps stock Tern layout, theme colours, configured fonts and terminal text. It normalizes chrome through the existing radius and easing tokens, then overrides hardcoded stock controls, popups and decorative effects. Chrome uses 2/4/6px radii, 12/14/16px type, short 100/150ms transitions and flat one-pixel boundaries rather than depth stacks. Circles, directional bubble corners, focus/error indicators, clipping masks and lifecycle feedback stay functional.

Busy labels, loading placeholders and progress remain visible but static; ornamental shimmers, pulses, orbiting dots, gloss, bloom and welcome flourishes are quiet. Mini supplies no palette, alias variables, font families or `!important` rules. The shared bubble, Glass frost, transparent-window and omp-bot options remain independent; no compatibility layer is needed. Select **Mini** in the Looks picker to load just this sheet.

The reference audit covered all 130 stock sheets from Tern 0.9.11 (`f93bb18`): 86 radius values, 582 shadow values, 62 font sizes, 863 spacing values, 31 opacities, 30 transition times and 298 named keyframes. These are inventory totals, not a claim that Mini rewrites every literal. The four root radius values collapse to three, both root easings become one, and the targeted chrome uses the scales above. Mini targets owners of 66 infinite-animation names and nine finite Mermaid/welcome names; streaming carets, terminal settings, save/bell feedback and lifecycle exits are intentionally retained.

Spine's borderless composer, screen-sized pickers, sidebar overlays, joined button groups and circular app actions keep their stock shape variants; Mini does not apply its rectangular chrome reset to those variants.
