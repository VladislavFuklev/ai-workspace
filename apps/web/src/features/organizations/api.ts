import { api } from "@/lib/api";

import { organizationSchema, type Organization } from "./schemas";

/** Creates an organisation and makes the caller its owner. */
export async function createOrganization(name: string): Promise<Organization> {
  return api("/api/v1/organizations", {
    method: "POST",
    body: { name },
    schema: organizationSchema,
  });
}
