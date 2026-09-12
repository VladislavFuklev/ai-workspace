// Measure WCAG contrast for every meaningful token pairing, in both themes.
// Reads the values straight out of globals.css so the report cannot drift from
// the stylesheet.
//
//   node scripts/check-contrast.mjs             failures and a summary only
//   node scripts/check-contrast.mjs --verbose   every measured ratio
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, relative as relativePath, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const verbose = process.argv.includes("--verbose");
// The root layout moved under the locale segment in task 1.11; keeping the path
// in one constant means the next move breaks loudly here rather than silently
// exempting nothing.
const LAYOUT = "apps/web/src/app/[locale]/layout.tsx";
// Quiet by default: this runs on every commit, and 40 passing lines are noise.
const report = (ok, line) => {
  if (verbose || !ok) console.log(line);
};
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

// The browser-chrome colour in layout.tsx has to be a literal — metadata cannot
// read CSS — so assert it still matches the token it is duplicating.
let failures = 0;
{
  const layout = readFileSync(resolve(root, LAYOUT), "utf8");
  const declared = [...layout.matchAll(/prefers-color-scheme:\s*(light|dark)\)",\s*color:\s*"(#[0-9a-fA-F]{6})"/g)];
  if (verbose) console.log("\nbrowser theme-color vs the bg token");
  for (const scheme of ["light", "dark"]) {
    const found = declared.find(([, s]) => s === scheme)?.[2]?.toLowerCase();
    const expected = themes[scheme].bg.toLowerCase();
    const ok = found === expected;
    if (!ok) failures++;
    report(ok, `  ${ok ? "ok  " : "FAIL"} theme-color ${scheme}: layout.tsx ${found ?? "missing"} vs --color-bg ${expected}`);
  }
}
for (const [theme, tokens] of Object.entries(themes)) {
  if (verbose) console.log(`\n${theme}`);
  for (const [fg, bg, min, label] of PAIRINGS) {
    if (!tokens[fg] || !tokens[bg]) {
      console.log(`  MISSING  ${theme} ${fg} on ${bg}`);
      failures++;
      continue;
    }
    const r = ratio(tokens[fg], tokens[bg]);
    const ok = r >= min;
    if (!ok) failures++;
    report(
      ok,
      `  ${ok ? "ok  " : "FAIL"} ${theme} ${r.toFixed(2).padStart(5)}:1 (min ${min})  ${fg} on ${bg} — ${label}`,
    );
  }
}

// The system-preference fallback repeats the dark tokens for visitors whose theme
// script has not run. Identical or not at all — a drift here shows up only for
// people with dark mode and slow JS, which is nobody's idea of a test case.
{
  const fallback = tokensFrom(":root:not([data-theme]) {");
  const names = new Set([...Object.keys(themes.dark), ...Object.keys(fallback)]);
  for (const name of names) {
    if (themes.dark[name] !== fallback[name]) {
      console.log(
        `  FAIL --color-${name}: [data-theme="dark"] has ${themes.dark[name] ?? "nothing"}, ` +
          `the prefers-color-scheme fallback has ${fallback[name] ?? "nothing"}`,
      );
      failures++;
    }
  }
}

// Token discipline: a hex literal in a component is a colour that no theme can
// change. Two files are exempt for reasons recorded next to them.
{
  const EXEMPT = new Set([
    // Replaces <html> when the root layout fails, so it cannot load the stylesheet.
    "apps/web/src/app/global-error.tsx",
    // viewport.themeColor must be a literal; asserted against --color-bg above.
    LAYOUT,
  ]);
  const walk = (dir) =>
    readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
      const full = resolve(dir, entry.name);
      if (entry.isDirectory()) return walk(full);
      return /\.(tsx?|css)$/.test(entry.name) ? [full] : [];
    });
  for (const file of walk(resolve(root, "apps/web/src"))) {
    const relative = relativePath(root, file);
    if (relative.endsWith("globals.css") || EXEMPT.has(relative)) continue;
    for (const [, hex] of readFileSync(file, "utf8").matchAll(/(#[0-9a-fA-F]{3,8})\b/g)) {
      console.log(`  FAIL raw colour ${hex} in ${relative} — use a token`);
      failures++;
    }
  }
}

const checked = PAIRINGS.length * Object.keys(themes).length + 2;
console.log(
  failures === 0
    ? `${checked} colour checks pass (WCAG AA, both themes; no raw hex outside globals.css)`
    : `\n${failures} of ${checked} colour checks failed`,
);
process.exit(failures === 0 ? 0 : 1);
