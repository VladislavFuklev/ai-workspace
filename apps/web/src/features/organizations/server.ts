import { serverGet, type ServerResult } from "@/lib/api/server";

import { organizationListSchema, organizationSchema, type Organization } from "./schemas";

/** Every organisation the caller belongs to, for the switcher and the picker. */
export async function getOrganizations(): Promise<ServerResult<Organization[]>> {
  return serverGet("/api/v1/organizations", organizationListSchema);
}

/**
 * One organisation, by the slug in the URL.
 *
 * A slug the caller does not belong to answers 404 — the same as one that does
 * not exist (task 4.4), so this cannot be used to discover other tenants. The
 * caller turns that into a not-found page.
 */
export async function getOrganization(slug: string): Promise<ServerResult<Organization>> {
  return serverGet(`/api/v1/organizations/${encodeURIComponent(slug)}`, organizationSchema);
}
