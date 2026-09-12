---
name: ui-review
description: Visual and interaction QA pass for any UI surface in apps/web — responsive behavior at real breakpoints, the four data states, keyboard and focus, contrast, content resilience, and the design bar that separates this product from generated dashboard boilerplate. Use after building or changing any screen, before marking a UI task complete.
---

# UI Review

Run this before calling any UI task done. It is a review pass with a verdict, not a
list of things to bear in mind.

## 1. Responsive — check, do not assume

Three widths, every time: **~375px** (phone), **~768px** (tablet), **≥1280px**
(desktop). Mobile first — if it was built at desktop width and then squeezed, it
will show.

- No horizontal scroll at any width. Test it; a single wide table or long
  unbroken string is the usual cause.
- Tables: either a real responsive treatment or an explicitly scrollable container
  with a visible affordance. Never a table that silently overflows the viewport.
- Navigation collapses to something usable, and the collapsed control is reachable
  by keyboard.
- Touch targets at least ~44px on coarse pointers; controls not stacked so tightly
  that the wrong one gets tapped.
- Modals, drawers and menus are usable at 375px — not cut off, not taller than the
  viewport without scrolling.

## 2. The four states — all of them, on every data surface

| State | The bar |
| --- | --- |
| Loading | Skeleton matching the real layout, so nothing jumps when data arrives. Not a centered spinner on a blank page. |
| Empty | Says what this is, why it is empty, and the one action that fills it. Never a bare "No data". |
| Error | Says what failed in the user's terms, and offers a retry. Never a raw status code or stack. |
| Success | The real thing, with realistic data density — not three demo rows. |

Also: a pending state on every submit (disabled plus visible progress), and
confirmation feedback after a mutation succeeds.

## 3. Keyboard and focus

- Tab through the whole screen. Every interactive element is reachable, in an order
  that matches the visual layout.
- The focus ring is always visible. If the default outline was removed, something
  at least as visible replaced it.
- No keyboard trap — except a modal, which must trap deliberately, close on
  `Escape`, and return focus to the element that opened it.
- Enter and Space activate what looks like a button. If they do not, it is a `div`
  pretending, and that is a defect.
- Skip-to-content link on pages with substantial navigation.

## 4. Screen reader and semantics

- Headings form a real outline: one `h1`, no level skipped for styling.
- Icon-only buttons have accessible names.
- Form fields have associated labels; errors linked with `aria-describedby` and
  announced, not conveyed by red alone.
- Asynchronous updates — streamed answers, toasts, background job status — sit in
  a live region.
- Landmarks (`nav`, `main`, `aside`) present and used once each where appropriate.

## 5. Contrast and color

- Body text ≥ 4.5:1; large text and meaningful UI boundaries ≥ 3:1. Measure, do not
  eyeball — low-contrast grey placeholder text is the most common failure.
- Color is never the only carrier of meaning: status needs a label or icon too.
- Check both themes if a theme system exists (1.5). Dark mode is where contrast
  regressions hide.
- Respect `prefers-reduced-motion`.

## 6. Content resilience

Break it on purpose:

- A 120-character document title, an organization name with no spaces, a user with
  one initial, a 40-item list, a 0-item list, a number with six digits.
- Text that wraps to three lines where the design assumed one.
- A long AI answer, and a one-word one.
- Truncation, where used, is deliberate (`text-overflow`, a tooltip or title with
  the full value) — never an accidental clip.

## 7. The design bar

The brief is explicit that this must not look like generated dashboard
boilerplate. Reject on sight:

- gradient hero headers, glassmorphism, decorative blur
- a grid of three identical oversized rounded cards
- fabricated metrics with nothing behind them, or sparklines of noise
- five font sizes and four greys on one screen
- vast empty space at desktop width with content in a narrow centered column
- emoji as UI iconography

Require instead:

- one restrained palette with a genuine neutral ramp, one accent used sparingly
- a single spacing scale, applied consistently — spacing is the main signal of
  whether a UI was designed or assembled
- typographic hierarchy from weight and size, at most three sizes per screen
- density suited to real work: a document list is a list, not a card gallery
- borders and subtle elevation to separate regions, rather than color blocks
- micro-interactions that communicate state (pending, saved, streaming), not
  decoration

## 8. Verdict

Report findings by severity, each with the surface, the width it appears at, and
the fix:

- **Blocking** — inaccessible to keyboard or screen reader, contrast failure,
  broken layout at 375px, a missing error or empty state.
- **Should fix** — inconsistent spacing or type, weak empty state, missing pending
  feedback, truncation without recourse.
- **Polish** — micro-interaction and refinement.

If nothing is blocking, say so plainly. If something is, the task is not done.
