// The message catalogues must have identical keys.
//
// A key present in one locale and not the other is a page that renders a raw
// key path to some users and nothing to anyone testing in the other language.
// Cheap to check, invisible otherwise.
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dir = resolve(root, "apps/web/messages");

const flatten = (value, prefix = "") =>
  Object.entries(value).flatMap(([key, entry]) =>
    entry && typeof entry === "object"
      ? flatten(entry, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  );

const catalogues = Object.fromEntries(
  readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => [name.replace(/\.json$/, ""), JSON.parse(readFileSync(resolve(dir, name), "utf8"))]),
);

const locales = Object.keys(catalogues);
if (locales.length < 2) {
  console.log(`only ${locales.length} catalogue(s); nothing to compare`);
  process.exit(0);
}

const keysByLocale = Object.fromEntries(
  locales.map((locale) => [locale, new Set(flatten(catalogues[locale]))]),
);
const [reference, ...others] = locales;
let failures = 0;

for (const locale of others) {
  for (const key of keysByLocale[reference]) {
    if (!keysByLocale[locale].has(key)) {
      console.log(`  FAIL ${key} is in ${reference} but missing from ${locale}`);
      failures++;
    }
  }
  for (const key of keysByLocale[locale]) {
    if (!keysByLocale[reference].has(key)) {
      console.log(`  FAIL ${key} is in ${locale} but missing from ${reference}`);
      failures++;
    }
  }
}

// An empty string renders as nothing, which looks like a layout bug rather than
// a missing translation.
for (const locale of locales) {
  const walk = (value, prefix = "") => {
    for (const [key, entry] of Object.entries(value)) {
      if (entry && typeof entry === "object") walk(entry, `${prefix}${key}.`);
      else if (typeof entry !== "string" || entry.trim() === "") {
        console.log(`  FAIL ${locale}: ${prefix}${key} is empty or not a string`);
        failures++;
      }
    }
  };
  walk(catalogues[locale]);
}

console.log(
  failures === 0
    ? `${keysByLocale[reference].size} keys, consistent across ${locales.join(", ")}`
    : `\n${failures} catalogue problem(s)`,
);
process.exit(failures === 0 ? 0 : 1);
