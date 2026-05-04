# Design System Reference

Source: Figma exports in this folder.
Files: `style-guide.png`, `01-home.png`, `02-chat.png` (results), `03-knowledge.png`, `04-faq.png`, `05-dashboard.png`, `06-chat-progress.png` (intake stepper component).
Logo: `../logo.svg` (four-shape mark + wordmark, native SVG).

This document captures everything I can extract from the screenshots. Where measurements are visual estimates rather than tokens, I've flagged them. Outstanding questions are at the bottom — please answer those before we start changing code.

---

## Brand identity

**Logo wordmark**: "choose my lawyer" set in two-line lockup, lowercase, weighted (light + bold) — paired with a four-petal swirl mark in teal / mint / pink / purple.

**Tone**: friendly, calm, modern. Heavy use of soft gradients (pink → purple → navy), abstract geometric line motifs, rounded shapes (no sharp corners anywhere).

---

## Colour palette

The requirements doc (`docs/requirements.md` §4.1) is canonical. The five swatches on `style-guide.png` are legacy and not in use — ignore them.

| Token | Hex | Usage observed |
|---|---|---|
| `brand.teal` | `#0AE5F6` | Logo accent, "Find a lawyer" pill (gradient start), "New appointments" dashboard card, top-5 results row tint, type-of-help icon tiles, completed-step check icons |
| `brand.navy` | `#080C64` | Body text, headings, footer background, dashboard stat-count badges, hero gradient end |
| `brand.mint` | `#69E4B5` | Logo accent, "New reviews" dashboard card, secondary highlights |
| `brand.purple` | `#9747FF` | Hero gradient, "Find a lawyer" pill (gradient end), "Appearances in results" card, footer accent |

### Surface / neutral colours (visual estimate)

| Token | Hex (est.) | Usage |
|---|---|---|
| `surface.canvas` | `#FFFFFF` | Page background |
| `surface.muted` | `#F4F2FA` | Section backgrounds, FAQ panel left side |
| `surface.alt` | `#EAF8FB` | Light teal-tinted rows in top-5 results |
| `border.subtle` | ≈ `#E5E7EB` | Card and input borders |
| `text.primary` | `#080C64` (navy) | Body and headings |
| `text.muted` | ≈ `#5B6280` | Secondary text |

### Gradients

- **Hero / CTA gradient**: linear, roughly `#9747FF → #0AE5F6` (purple to teal), 135° diagonal. Used on hero background, "Find a lawyer" button, "Proceed" buttons, CTA banners.
- **Footer gradient**: deep navy → purple (`#080C64 → ~#3E2556`) with overlaid faint geometric line pattern.
- **Section divider gradients**: pink → purple → teal sweeps separating page sections (e.g. between hero and "Simplifying access to legal help"). Subtle, with abstract concentric line motifs.

---

## Typography

**Primary typeface**: **Inter** (confirmed in style guide). A second face is listed as "XXX" — placeholder, not yet specified.
**Weights in use**: Light (300), Medium (500), Bold (700).
**Foundries listed**: Adobe Fonts, Google Fonts.

### Scale (visual estimate from style-guide rulers — exact px values not legible)

The style guide shows 11 desktop sizes from H1 down to H11, with a parallel mobile scale. Working approximations:

| Token | Desktop | Mobile | Weight | Usage |
|---|---|---|---|---|
| H1 | ~56–64px | ~36–40px | Bold | Hero headline |
| H2 | ~44–48px | ~30–32px | Bold | Section titles |
| H3 | ~32–36px | ~26–28px | Bold/Medium | Sub-section / card headings |
| H4 | ~24–28px | ~22px | Medium | Mini-headings |
| H5 | ~20–22px | ~18px | Medium | Card titles, table headers |
| Body L | 16px / 24px lh | 16px / 24px lh | Regular | Body copy (1.5× line height per style guide) |
| Body S | 20px? / 30px lh | small | Regular | Note: style-guide text says "small body 20×1.5" — looks reversed; treat as a guide, not a rule |
| Caption | ~12–13px | ~11–12px | Regular | Meta info, footer fine print |

Style-guide note: *body line-height = 1.5×; optimal 50–75 chars per line*. We should bake the 1.5× line-height ratio in.

### Headings

- Tightly tracked (negative letter-spacing approx. -0.02em on H1)
- Sentence case, never all caps
- Colour: navy `#080C64`

---

## Layout & spacing

- **Max content width**: ~1200–1280px centered
- **Section vertical rhythm**: ~80–96px between major page sections on desktop
- **Card padding**: ~24–32px
- **Border radius**:
  - Pills (buttons, chips): full / 999px
  - Cards: ~16–24px
  - Inputs: ~12–16px
  - Hero / large feature cards: ~24–32px
- **Shadows**: very soft and rare; mostly used under elevated cards (e.g. testimonial cards). Estimate: `0 8px 24px rgba(8, 12, 100, 0.08)`.

---

## Components observed

### Buttons

| Variant | Style |
|---|---|
| **Primary** ("Find a lawyer", "Proceed") | Pill, full-radius, **purple→teal gradient**, white text, ~14–16px medium weight, generous horizontal padding (~28–36px) |
| **Secondary** | Outlined pill, navy border, navy text on white background |
| **Tertiary / link** | Plain text, navy or teal, occasionally with chevron |
| **Quick-reply chips** (chat search) | Soft white pill on tinted background, navy text, light border |
| **Pagination** | Numbered circles, current page filled |

The style guide has a "Buttons" heading but no visible samples in the export — confirm intended variants.

### Inputs

- Full-width white field, rounded ~12–16px, subtle 1px border
- Label above input (navy, medium weight, ~13–14px)
- Generous internal padding (~14–16px vertical)
- Helper text below field

### Cards

- **Stat cards** (dashboard): solid colour fill (teal / navy / pink / mint), large number badge in dark navy circle on top-centre, label below ("New appointments"), small "View" link at the bottom. Square-ish, all four cards equal size.
- **Article cards** (knowledge teasers): image top, title, author + date, tag chip
- **Service-type cards** (home): light teal tile, icon top-left, label centred, rounded ~20px
- **Testimonial cards**: white, soft shadow, star row, quote, attribution

### Results table (chat/results page)

- Top section: top-5 firms in **light teal-tinted rows** with bold dark-navy header; each row has rank, firm name, star rating + count, price, distance, "Proceed" button (purple→teal gradient pill).
- Below the top-5: full list in plain white rows with the same columns; sortable (per requirements doc).
- Pagination at bottom centre.

### FAQ accordion

- Rounded pill-shaped rows with chevron-right on the right
- Group headers (Popular questions / Conveyancing / Wills & Probate / Family Law / Personal Injury)
- Left side has a tinted panel with the page hero and category quick-jump chips
- Below the list: a "Didn't find the answer?" contact form (Name / Email / Subject / Description / reCAPTCHA / Submit)

### Intake progress stepper (`06-chat-progress.png`)

A vertical stepper that sits alongside the conversational intake. Five states observed:

1. **Pending** — grey outlined circle, grey label
2. **Completed** — solid teal `#0AE5F6` circle, white check icon, navy label
3. **Active / expanded** — teal check, navy label, panel below shows the entered data as `label → value` pairs (right-aligned values, navy text)
4. **Collapsed** with chevron-down on the right; **expanded** with chevron-up
5. Final two steps in the export are "Get your quote" and "Launch your case" — pending until form completion

Steps and fields visible:

| Step | Fields |
|---|---|
| About your case | Purchase Price, Tenure, Property Postcode, Mortgage, New build, Help to Buy ISA, Shared Ownership |
| Your details | First name, Last name, Your email, Your phone |
| Get your quote | (terminal action) |
| Launch your case | (terminal action) |

Component implementation notes: list of disclosure rows; row heights compact (~40px); the active step's expanded panel pads ~16–20px; values right-aligned with key/value rows.

### Header / nav (consistent across pages)

- White background, ~80px tall
- Logo left, nav links centre-right (How it works · Legal services · Knowledge · FAQs · Firm Register/Login), primary CTA ("Find a lawyer") pill far right
- Sticky?  Not visible from a static export — assume yes.

### Footer (consistent across pages)

- Deep navy → purple gradient background with faint geometric line motif
- Logo + tagline ("We connect consumers with legal experts…") top-left
- Social icons (Instagram / YouTube / LinkedIn) on the right
- Bottom bar: copyright · Website Terms · Privacy Policy · Cookie Policy · Web Design SOZO

### Firm dashboard

- Left rail with firm name (e.g. "Christopher Davidson Solicitors LLP") + sub-nav (Dashboard / Firm Details / Fees & Service Offering / Reviews / Logout)
- Main: 2×2 grid of metric cards (counts over the last 30 days)
- Each card: large number badge (navy circle), card label, "View" link

---

## Page summaries

| File | Page | Key sections |
|---|---|---|
| `01-home.png` | Landing (consumer) | Hero with search input + quick-tag chips → "Simplifying access" 3-up → "Types of legal help" 5-up → "Instant solutions" promo → testimonials → "Your trusted source" image+text → "Making legal choice clearer" → knowledge cards → footer |
| `02-chat.png` | Results | Title "Your conveyancing quotes" → top-5 results table (teal tinted) → full results table → pagination → FAQ accordion teaser → knowledge cards → footer |
| `03-knowledge.png` | Knowledge article | Article hero (title + author + image) → multi-block body with inline images → CTA banner → "You may also be interested in" 3-up → footer |
| `04-faq.png` | FAQs | Hero left panel + category chips → search → grouped accordion → contact form → CTA banner → footer |
| `05-dashboard.png` | Firm dashboard | Left rail nav → 2×2 stat cards (New appointments / Video call requests / Appearances in results / New reviews) → footer |
| `06-chat-progress.png` | Intake stepper component | Five states: pending, completed, active expanded, collapsed, expanded with field summary |

---

## Iconography & illustrations

- **Service icons** on home: line-style, soft, in navy on teal tile background
- **Photography**: warm, muted, real people (older man + carer, parent + child, divorce papers); 85% opacity overlay treatment per the style-guide "Image compositions" page (gradient + photo @ 85% + solid colour bottom layer)
- **Decorative motifs**: abstract concentric line patterns and overlapping geometric shapes used as section dividers and footer texture

---

## Resolved

- ✅ Canonical palette is Teal / Navy / Mint / Purple (requirements doc); style-guide swatches are dropped.
- ✅ Practice area: conveyancing only. Other categories no longer appear in scope.
- ✅ Logo: `docs/logo.svg` available as native SVG.
- ✅ Intake progress component: documented from `06-chat-progress.png`.

## Still open

1. **Type scale** — you couldn't find it in Figma. Three options:
   - **(a) Pull values from Figma directly**: open the file in design mode (not prototype), click any heading on a page (e.g. H1 in the home hero), and the right-hand "Design" panel shows `font-size`, `line-height`, `letter-spacing`. Do this for one of each: H1, H2, H3, body large, body small, caption — and I'll use those exact numbers.
   - **(b) Pick a sane default scale** based on visual proportions (Tailwind's defaults adjusted to match the mocks: H1 60/64, H2 44/52, H3 32/40, H4 24/32, body 16/24). I'd implement this and we iterate.
   - **(c) Switch to Dev Mode in Figma** (`</>` toggle top-right) — this surfaces full CSS for any element. Free tier is limited; paid gets full inspect.
   I'd recommend (a) for H1 + body + a button label as a minimum, then (b) for the rest. Want me to proceed with (b) defaults and we tune later?
2. **Second typeface** — the style guide lists "Typeface 2: XX & XX" as a placeholder. Is Inter the only face, or is there a second?
3. **Mobile** — desktop frames only so far. Are there mobile frames I should pull, or should I adapt responsively from these?
4. **Missing screens** — please export when ready:
   - **Intake / conversational chat flow** (per-question screens — only the home-page entry is here, and the `06-chat-progress` stepper is a side panel)
   - **Firm portal sub-pages**: Firm Details, Fees & Service Offering, Reviews
   - **Firm login / register** flows
   - **Proceed / Request callback modal** (post-results conversion)
   - **Email confirmation** / sent-email confirmation pages
   - **Empty / error / loading states** for results and dashboard
5. **Iconography** — are the service-type and meta icons from a library (Lucide / Phosphor / custom)? If custom, please export the set as SVG.
6. **Photos** — owned/licensed or placeholder? If licensed, drop originals in `docs/design/photos/`.

## Next step

Once (1) and (2) are settled, I'll:

1. Patch `frontend/tailwind.config.ts` with the colour tokens, font family, type scale, radii, and shadow tokens
2. Update `frontend/app/globals.css` button/input/card utilities (`.btn-primary`, `.card`, `.input`) to the new gradient pill / rounded-card aesthetic
3. Re-skin in this order: shared layout (header, footer) → home → results → FAQ → knowledge → firm dashboard
4. Defer chat intake re-skin until you've exported those screens
