# DK Insurance Website — Design System Rules

This is a **plain static HTML/CSS/JS site** (no build step, no framework, no
package manager). This doc exists to keep Figma-to-code work consistent with
what's actually here — it does not describe tooling the project doesn't have.

## 1. Token Definitions

**Location:** `css/style.css`, top of file, inside a single `:root { }` block
(lines 1–42).

**Format:** Native CSS custom properties. No preprocessor (no Sass/Less), no
JSON/YAML token source, no Style Dictionary or similar transform pipeline —
the `:root` block *is* the token source of truth.

```css
:root {
  /* Color */
  --navy: #0f1c33;
  --navy-deep: #0a1424;
  --navy-light: #1c2f4f;
  --gold: #c9a03a;
  --gold-light: #dab863;
  --cream: #f5eddb;
  --cream-dark: #ecdfc0;
  --wood-light: #e7c294;
  --wood-dark: #c88f52;
  --maroon: #7c2f22;
  --ink: #16233a;
  --text-gray: #565f74;

  /* Type */
  --font-display: 'Archivo Black', 'Arial Black', 'Helvetica Neue', sans-serif;
  --font-sans: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  /* Spacing scale (not a strict 4/8pt grid — named steps) */
  --space-1: 0.5rem;  /* 8px */
  --space-2: 1rem;    /* 16px */
  --space-3: 1.5rem;  /* 24px */
  --space-4: 2rem;    /* 32px */
  --space-5: 3rem;    /* 48px */
  --space-6: 4.5rem;  /* 72px */
  --space-7: 6rem;    /* 96px */

  /* Radius */
  --radius: 6px;
  --radius-sm: 4px;

  --container-max: 1200px;
}
```

**Rules for new tokens:**
- Add new colors/spacing/radii to this one `:root` block — never inline a raw
  hex value or pixel size in a component rule if a token already covers it.
- Brand colors (`--navy`, `--gold`, `--blue-logo`) are fixed brand facts —
  don't introduce new brand hues without the client confirming it.
- There is no dark-mode token set. If dark mode is ever requested, it needs a
  second block (`@media (prefers-color-scheme: dark)` + `[data-theme="dark"]`
  override), not ad hoc per-component overrides.

## 2. Component Library

**There is no component library, no framework components, and no Storybook.**
"Components" are CSS class conventions applied directly to HTML markup in
`index.html`. A Figma component maps to **a reusable class name + a markup
pattern**, documented here rather than as an importable unit.

Established patterns (defined in `css/style.css`, used in `index.html`):

| Figma-equivalent | CSS class(es) | Notes |
|---|---|---|
| Button / primary | `.btn .btn-gold` | Rectangular, `--radius-sm`, hard offset shadow (`box-shadow: 5px 5px 0 var(--navy)`) that collapses on hover/press — this interaction is a deliberate brand choice, not a default. |
| Button / secondary | `.btn .btn-navy` | Same shape, shadow color swaps to `--gold`. |
| Button / outline | `.btn .btn-outline` | Transparent fill, navy shadow. |
| Eyebrow label | `.eyebrow` (+ `.center`, `.on-dark` modifiers) | Small-caps label with a short gold rule via `::before`. |
| Section heading block | `.section-head` (+ `.center`) | Eyebrow + `<h2>` + supporting `<p>`. |
| Full-width row (services list) | `.coverage-list` > `.coverage-row` | Numbered chip (`.coverage-index`) + body + CTA, striped via `:nth-child(even)`. |
| Numbered clause (trust section) | `.clause` | `§`-style marker + heading + copy, used in pairs via `.clause-grid`. |
| Full-screen nav overlay | `.nav-overlay` (+ `.is-open`) | Not a dropdown — a fixed, full-viewport takeover. State toggled by JS, not CSS-only. |

**When bringing in a new Figma component:** name its CSS class after the
component's role (`.testimonial-card`, not `.card3`), and add it to this
table.

## 3. Frameworks & Libraries

- **UI framework:** none. Plain HTML5 + vanilla JS (`js/script.js`, ~25 lines,
  handles only the nav-overlay open/close).
- **Styling:** plain CSS, one file (`css/style.css`), no CSS Modules, no
  Tailwind, no CSS-in-JS.
- **Build system / bundler:** none. No `package.json`, no npm scripts, no
  Vite/Webpack. Files are served as-is; `index.html` links `css/style.css`
  and `js/script.js` directly with relative paths.
- **Fonts:** loaded via a Google Fonts `<link>` in `<head>` (Archivo Black +
  Public Sans) — not self-hosted, not bundled.

**Implication for Figma MCP output:** generated code should be plain HTML +
CSS custom properties, not JSX/Vue SFCs/Tailwind classes, unless the project
explicitly adopts a framework (see §7 for how to handle that transition).

## 4. Asset Management

- **Location:** `assets/` at the repo root (`assets/logo.svg`,
  `assets/favicon.svg`). No `public/`, `static/`, or CDN bucket.
- **Format:** SVG only, hand-authored (not exported flat from Figma) —
  `assets/logo.svg` recreates the client's real logo as scalable vector
  markup with a `<title>` for accessibility.
- **Referencing:** direct relative paths, e.g. `<img src="assets/logo.svg" ...>`.
  No import statements, no asset hashing/fingerprinting, no `srcset`/`sizes`
  responsive images yet.
- **Optimization:** none automated (no imagemin/svgo build step) — assets are
  kept small by hand (both current SVGs are well under 1 KB of markup).
- **CDN:** none for site assets. The only external network dependency is the
  Google Fonts stylesheet.

**Rule:** any new raster image (photos, etc.) should be added under `assets/`
with a descriptive filename, and a real `alt` attribute — see §5 in the
accessibility notes baked into `index.html` (skip link, focus-visible states,
`aria-hidden` on decorative SVGs).

## 5. Icon System

- **Location:** icons are **inline `<svg>` markup directly in `index.html`**,
  not separate files, not an icon font, not a component library
  (Heroicons/Lucide/Phosphor are not installed as dependencies here even
  though the visual style is similar).
- **Style:** 24×24 viewBox, `stroke="currentColor"`, `stroke-width` around
  1.8–2.6, `stroke-linecap="round"`, `stroke-linejoin="round"` — this is the
  house style; match it exactly for new icons so stroke weight stays
  consistent.
- **Usage pattern:** icons are colored via `currentColor` and sized by the
  parent's CSS (e.g. `.btn svg { width: 17px; height: 17px; }`,
  `.footer-contact svg { width: 18px; height: 18px; color: var(--gold); }`).
  Don't hardcode `fill`/`stroke` colors inside the SVG itself except for the
  two brand illustrations noted below.
- **Naming convention:** none needed today since icons aren't extracted to
  files — if/when they are, use the pattern `assets/icons/<name>.svg` with
  kebab-case names matching what they depict (`phone.svg`, `mail.svg`).
- **Brand illustrations (exception to the rule above):** the hero umbrella
  illustration and the two `.coverage-index`/wood-tone tiles use fixed brand
  colors (`--gold`, `--maroon`, `--wood-light/dark`) rather than
  `currentColor`, because they're decorative brand moments, not functional
  UI icons.

## 6. Styling Approach

- **Methodology:** hand-written global CSS with descriptive, component-scoped
  class names (loosely BEM-adjacent, e.g. `.hero-copy`, `.hero-panel`,
  `.coverage-row`, `.nav-overlay-list`) — not strict BEM, no CSS Modules
  scoping, so **class name collisions are possible**; keep names specific.
- **Global styles:** `css/style.css` §"Reset" (lines ~44–78) — a lightweight
  reset (box-sizing, margin removal, list style removal, `prefers-reduced-motion`
  handling), plus base `body`/`h1–h4` rules. There is one stylesheet for the
  whole site; there is no per-page or per-component CSS split.
- **Responsive strategy:** mobile-first with `min-width` media queries at
  `640px`, `768px`, `900px`, `960px`, `1024px` (chosen ad hoc per component,
  not a single shared breakpoint list — check nearby rules before adding a
  new breakpoint value). Layout primitives are CSS Grid/Flexbox; no
  container queries in use.
- **Interaction/motion:** transitions are short (`0.12s–0.25s ease`), and the
  file respects `prefers-reduced-motion: reduce` globally (see top of
  `style.css`) by collapsing all animations/transitions. Keep this guard when
  adding new animated components.

## 7. Project Structure

```
test-project/
├── index.html        # entire site — one page, sections in document order
├── css/
│   └── style.css      # all styles, single file, tokens at the top
├── js/
│   └── script.js       # nav-overlay open/close logic only
├── assets/
│   ├── logo.svg         # real client logo, hand-recreated as SVG
│   └── favicon.svg
├── README.md
└── CLAUDE.md          # this file
```

- **Page organization:** `index.html` is a single page with anchor-linked
  sections (`#top`, `#services`, `#about`, `#testimonials`, `#contact`) — there
  is no router and no multi-page structure yet. The real client site (dropdown
  categories like "Business Solutions" / "Personal Benefit Solutions" /
  "Mortgage Free Life") has not been built out as separate pages — if that
  work happens, each new page should reuse `css/style.css` as-is rather than
  forking styles per page.
- **Section order in `index.html`:** header → hero → coverage strip → services
  → how-it-works ("steps") → why-us (clauses) → testimonial ("stories") →
  CTA band → footer. New sections should slot into this flow and follow the
  existing `<section>` + `.container` + `.section-head` scaffolding rather
  than inventing a new outer wrapper pattern.
- **No feature-folder structure** — there's exactly one feature (the
  marketing site), so there's no need for domain/feature subdirectories yet.
  If this grows into a multi-page or app-like project, revisit this doc
  before restructuring.

## Notes for Figma MCP integration specifically

- When pulling a Figma frame into code, **map Figma variables to the existing
  `:root` custom properties above** rather than emitting new literals — check
  this file's token table first.
- Figma text styles should map to `--font-display` (headings, all-caps,
  `font-weight: 400` — the weight lives in the font file, not CSS) or
  `--font-sans` (body/UI text) — there is no third text family.
- Figma auto-layout frames typically translate to a `<section>` +
  `.container` + Flexbox/Grid, matching the patterns in §2 — avoid emitting
  absolute-positioned divs.
- Since there's no component library, treat each Figma component as "a CSS
  class + a markup snippet to copy," and add it to the table in §2 so the
  next person (or the next MCP run) reuses it instead of duplicating.
