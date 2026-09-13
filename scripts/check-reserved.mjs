#!/usr/bin/env node
/**
 * The reserved-slug list exists twice and must not drift.
 *
 * The API refuses to mint an organisation whose slug matches a static route
 * (`core/slugs.py: RESERVED`); the web middleware uses the same list to tell a
 * slug from a page without a round trip. If they disagree, either an
 * organisation becomes unreachable or a real page starts redirecting into one —
 * and neither shows up until someone happens to create the wrong name.
 *
 * A third check: every static segment that actually exists under `[locale]`
 * must be in the list, so adding a page and forgetting the list fails here.
 */
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function pythonSet(path, name) {
  const source = readFileSync(join(root, path), "utf8");
  const block = source.match(new RegExp(`${name} = frozenset\\(\\s*\\{([^}]*)\\}`));
  if (!block) throw new Error(`${name} not found in ${path}`);
  return new Set([...block[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]));
}

function typescriptList(path, name) {
  const source = readFileSync(join(root, path), "utf8");
  const block = source.match(new RegExp(`${name} = \\[([^\\]]*)\\]`));
  if (!block) throw new Error(`${name} not found in ${path}`);
  return new Set([...block[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]));
}

/** Static (non-dynamic) route segments directly under `[locale]`, groups flattened. */
function staticSegments(dir) {
  const found = new Set();
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    if (entry.name.startsWith("(") && entry.name.endsWith(")")) {
      for (const nested of staticSegments(join(dir, entry.name))) found.add(nested);
      continue;
    }
    if (entry.name.startsWith("[") || entry.name.startsWith("_") || entry.name.startsWith("@")) {
      continue;
    }
    found.add(entry.name);
  }
  return found;
}

const api = pythonSet("apps/api/src/ai_workspace_api/core/slugs.py", "RESERVED");
const web = typescriptList("apps/web/src/features/organizations/reserved.ts", "RESERVED_SEGMENTS");
const routes = staticSegments(join(root, "apps/web/src/app/[locale]"));

const problems = [];
for (const slug of api) if (!web.has(slug)) problems.push(`in the API list, not the web one: ${slug}`);
for (const slug of web) if (!api.has(slug)) problems.push(`in the web list, not the API one: ${slug}`);
for (const segment of routes) {
  if (!api.has(segment)) problems.push(`route /[locale]/${segment} exists but is not reserved`);
}

if (problems.length > 0) {
  console.error("Reserved slugs disagree:");
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}

console.log(`${api.size} reserved slugs, consistent across api, web and the route tree`);
