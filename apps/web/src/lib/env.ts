import { z } from "zod";

/**
 * Public runtime configuration, validated once.
 *
 * Only `NEXT_PUBLIC_*` variables belong here. Next.js inlines those into the
 * browser bundle, so **anything in this file is world-readable** — a secret added
 * here is a published secret.
 *
 * Server-only configuration will live in a sibling `env.server.ts` guarded by
 * `import "server-only"`, added when the first server secret exists (phase 3).
 *
 * Validation runs at module load. `next.config.ts` imports this file so a missing
 * or malformed value fails the build rather than a request in production.
 */
const publicEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: z
    .url("NEXT_PUBLIC_API_URL must be an absolute URL, e.g. http://localhost:8000")
    .describe("Base URL of the AI Workspace API"),
});

/**
 * Read explicitly rather than by spreading `process.env`: Next.js replaces
 * `process.env.NEXT_PUBLIC_*` textually at build time, so a dynamic lookup finds
 * nothing in the browser.
 */
const parsed = publicEnvSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
});

if (!parsed.success) {
  const problems = parsed.error.issues
    .map((issue) => `  ${issue.path.join(".")}: ${issue.message}`)
    .join("\n");
  throw new Error(`Invalid public environment configuration:\n${problems}`);
}

export const env = parsed.data;
export type PublicEnv = typeof env;
