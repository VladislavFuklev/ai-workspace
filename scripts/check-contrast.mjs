// Measure WCAG contrast for every meaningful token pairing, in both themes.
// Reads the values straight out of globals.css so the report cannot drift from
// the stylesheet. Run: node scripts/check-contrast.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const css = readFileSync(resolve(root, "apps/web/src/app/globals.css"), "utf8");

/** Tokens from a block, e.g. `@theme {` (light) or `[data-theme="dark"] {`. */
function tokensFrom(startPattern) {
  const start = css.indexOf(startPattern);
  if (start === -1) throw new Error(`block not found: ${startPattern}`);
  const body = css.slice(start + startPattern.length, css.indexOf("\n}", start));
  const out = {};
  // Match any value, then validate: a typo like `#182votes` would otherwise be
  // skipped silently by a hex-only pattern and never appear in the report.
  for (const [, name, value] of body.matchAll(/--color-([a-z0-9-]+):\s*([^;]+);/g)) {
    const hex = value.trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(hex)) {
      throw new Error(`--color-${name} is not a 6-digit hex colour: ${hex}`);
    }
    out[name] = hex;
  }
  return out;
}

const srgb = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const luminance = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b);
};
const ratio = (a, b) => {
  const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};

// [foreground, background, minimum, what it is]
const PAIRINGS = [
  ["text", "bg", 4.5, "body text on the page"],
  ["text", "surface", 4.5, "body text on a card"],
  ["text", "surface-muted", 4.5, "body text on a muted panel"],
  ["text-muted", "bg", 4.5, "secondary text"],
  ["text-muted", "surface", 4.5, "secondary text on a card"],
  ["text-subtle", "bg", 4.5, "placeholder / metadata"],
  ["accent", "bg", 4.5, "link text"],
  ["accent-fg", "accent", 4.5, "label on an accent button"],
  ["success", "bg", 4.5, "success text"],
  ["warning", "bg", 4.5, "warning text"],
  ["danger", "bg", 4.5, "danger text"],
  ["danger-fg", "danger", 4.5, "label on a danger button"],
  ["border-strong", "bg", 3, "UI boundary"],
  ["border-strong", "surface", 3, "UI boundary on a card"],
  ["focus", "bg", 3, "focus ring"],
  ["accent", "accent-subtle", 4.5, "accent text on its own tint"],
  ["text", "accent-subtle", 4.5, "body text on an accent tint"],
  ["success", "success-subtle", 4.5, "success text on its own tint"],
  ["warning", "warning-subtle", 4.5, "warning text on its own tint"],
  ["danger", "danger-subtle", 4.5, "danger text on its own tint"],
];

const themes = {
  light: tokensFrom("@theme {"),
  dark: tokensFrom('[data-theme="dark"] {'),
};

let failures = 0;
for (const [theme, tokens] of Object.entries(themes)) {
  console.log(`\n${theme}`);
  for (const [fg, bg, min, label] of PAIRINGS) {
    if (!tokens[fg] || !tokens[bg]) {
      console.log(`  MISSING  ${fg} on ${bg}`);
      failures++;
      continue;
    }
    const r = ratio(tokens[fg], tokens[bg]);
    const ok = r >= min;
    if (!ok) failures++;
    console.log(
      `  ${ok ? "ok  " : "FAIL"} ${r.toFixed(2).padStart(5)}:1 (min ${min})  ${fg} on ${bg} — ${label}`,
    );
  }
}

console.log(
  failures === 0
    ? "\nEvery pairing meets WCAG AA."
    : `\n${failures} pairing(s) below AA.`,
);
process.exit(failures === 0 ? 0 : 1);
