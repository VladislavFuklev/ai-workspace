import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";

import { loadEnvConfig } from "@next/env";

/**
 * Load the repository-root `.env` into `process.env`.
 *
 * Next.js looks for `.env` in the app directory, but this is a monorepo: one
 * `.env` at the root serves both apps and Docker Compose (ADR-013). Without this,
 * a build run from either directory would not see it.
 *
 * Side-effect module. `next.config.ts` imports it before `./env`, and ES modules
 * evaluate in import order, so the values exist before validation runs.
 *
 * `forceReload` is required: Next.js has already called `loadEnvConfig` for the
 * app directory by the time the config module runs, and without it the second
 * call returns the cached result and this one silently does nothing.
 *
 * Existing `process.env` entries win, so CI and container environments override
 * the file.
 */
function findRepoRoot(from: string): string | null {
  let directory = from;
  for (;;) {
    if (existsSync(resolve(directory, ".git"))) return directory;
    const parent = dirname(directory);
    if (parent === directory) return null;
    directory = parent;
  }
}

const repoRoot = findRepoRoot(process.cwd());
if (repoRoot) {
  loadEnvConfig(
    repoRoot,
    process.env.NODE_ENV !== "production",
    { info: () => {}, error: console.error },
    true,
  );
}
