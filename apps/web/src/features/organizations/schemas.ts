import { z } from "zod";

/** Mirrors `OrganizationSummary` and `MemberSummary` on the API (task 4.4). */
export const organizationSchema = z.object({
  id: z.uuid(),
  name: z.string(),
  slug: z.string(),
  role: z.enum(["owner", "admin", "member", "viewer"]),
});

export type Organization = z.infer<typeof organizationSchema>;
export type Role = Organization["role"];

export const organizationListSchema = z.array(organizationSchema);

/** The API caps a name at 120 characters; saying so here saves a round trip. */
export const MAX_ORGANIZATION_NAME = 120;
