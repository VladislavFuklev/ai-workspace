import { api } from "@/lib/api";

import {
  memberSchema,
  organizationSchema,
  type Member,
  type Organization,
  type Role,
} from "./schemas";

/** Creates an organisation and makes the caller its owner. */
export async function createOrganization(name: string): Promise<Organization> {
  return api("/api/v1/organizations", {
    method: "POST",
    body: { name },
    schema: organizationSchema,
  });
}

/** Renames an organisation. Its address does not change — links keep working. */
export async function renameOrganization(slug: string, name: string): Promise<Organization> {
  return api(`/api/v1/organizations/${encodeURIComponent(slug)}`, {
    method: "PATCH",
    body: { name },
    schema: organizationSchema,
  });
}

export async function deleteOrganization(slug: string): Promise<void> {
  await api(`/api/v1/organizations/${encodeURIComponent(slug)}`, { method: "DELETE" });
}

export async function changeMemberRole(slug: string, userId: string, role: Role): Promise<Member> {
  return api(`/api/v1/organizations/${encodeURIComponent(slug)}/members/${userId}`, {
    method: "PATCH",
    body: { role },
    schema: memberSchema,
  });
}

export async function removeMember(slug: string, userId: string): Promise<void> {
  await api(`/api/v1/organizations/${encodeURIComponent(slug)}/members/${userId}`, {
    method: "DELETE",
  });
}

/** Leaving needs no permission — a viewer may leave — but the last owner may not. */
export async function leaveOrganization(slug: string): Promise<void> {
  await api(`/api/v1/organizations/${encodeURIComponent(slug)}/members/me`, { method: "DELETE" });
}
