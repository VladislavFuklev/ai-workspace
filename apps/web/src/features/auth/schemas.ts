import { z } from "zod";

/**
 * The auth API's shapes, validated at the boundary.
 *
 * ADR-005: nothing is shared at compile time between the two apps, so a response
 * is checked rather than asserted. If the API changes, this fails loudly here
 * instead of producing `undefined` three components later.
 */
export const userProfileSchema = z.object({
  id: z.uuid(),
  email: z.email(),
  display_name: z.string(),
  is_verified: z.boolean(),
});

export type UserProfile = z.infer<typeof userProfileSchema>;

export const registerResponseSchema = z.object({ message: z.string() });

/** Mirrors the API's policy (task 3.4) so the browser can say no first. */
export const MIN_PASSWORD_LENGTH = 12;
