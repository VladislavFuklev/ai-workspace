import { z } from "zod";

export const roleSchema = z.enum(["owner", "admin", "member", "viewer"]);

/** Mirrors `OrganizationSummary` and `MemberSummary` on the API (task 4.4). */
export const organizationSchema = z.object({
  id: z.uuid(),
  name: z.string(),
  slug: z.string(),
  role: roleSchema,
  /**
   * What this caller may do here, as the API computed it. The web app does not
   * keep its own copy of the permission table: a copy drifts, and every drift
   * is a button that fails when pressed. This decides what is *offered*; the
   * API still decides what is allowed.
   */
  permissions: z.array(z.string()),
});

export type Organization = z.infer<typeof organizationSchema>;
export type Role = z.infer<typeof roleSchema>;

export const organizationListSchema = z.array(organizationSchema);

export const memberSchema = z.object({
  user_id: z.uuid(),
  email: z.email(),
  display_name: z.string(),
  role: roleSchema,
});

export type Member = z.infer<typeof memberSchema>;

export const memberListSchema = z.array(memberSchema);

/** The permission names this app actually asks about. */
export const PERMISSIONS = {
  update: "organization:update",
  delete: "organization:delete",
  memberRemove: "member:remove",
  memberRoleChange: "member:role_change",
} as const;

export function can(organization: Organization, permission: string): boolean {
  return organization.permissions.includes(permission);
}

/**
 * Authority order, used only to decide which roles a caller may hand out. The
 * API enforces the same ladder; this keeps the select from offering a role the
 * request would be refused for.
 */
export const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, admin: 2, owner: 3 };

/** The API caps a name at 120 characters; saying so here saves a round trip. */
export const MAX_ORGANIZATION_NAME = 120;
