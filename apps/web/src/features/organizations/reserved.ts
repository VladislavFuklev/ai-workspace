/**
 * Path segments that are pages, not organisations.
 *
 * The organisation slug sits directly under the locale (`/en/acme/documents`),
 * so anything static at that position would shadow an organisation with the same
 * slug. The API refuses to mint these (`core/slugs.py: RESERVED`); this copy is
 * what the middleware uses to tell "a slug" from "a page" without a round trip.
 *
 * `scripts/check-reserved.mjs` fails if the two lists drift apart — an
 * organisation nobody can reach is not a failure anyone would notice quickly.
 */
export const RESERVED_SEGMENTS = [
  "api",
  "assets",
  "components",
  "design",
  "enter",
  "forms",
  "new",
  "organizations",
  "reset-password",
  "sign-in",
  "sign-up",
  "static",
] as const;
