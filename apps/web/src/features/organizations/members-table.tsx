"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { changeMemberRole, removeMember } from "./api";
import {
  PERMISSIONS,
  ROLE_RANK,
  can,
  roleSchema,
  type Member,
  type Organization,
  type Role,
} from "./schemas";

/**
 * Who is in the organisation, and what the caller may do about it.
 *
 * Every action here is offered from `organization.permissions` — what the API
 * said this caller may do — plus the ladder rule it enforces: you cannot act on
 * someone above you, and never on yourself. Rendering a control the request
 * would refuse teaches people to distrust the interface.
 */
export function MembersTable({
  organization,
  members,
  currentUserId,
}: {
  organization: Organization;
  members: Member[];
  currentUserId: string;
}) {
  const t = useTranslations("organizations");
  const router = useRouter();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mayChangeRoles = can(organization, PERMISSIONS.memberRoleChange);
  const mayRemove = can(organization, PERMISSIONS.memberRemove);
  const myRank = ROLE_RANK[organization.role];
  // The roles this caller may hand out: their own level and below.
  const grantable = roleSchema.options.filter((role) => ROLE_RANK[role] <= myRank);

  async function act(userId: string, action: () => Promise<unknown>) {
    setPendingId(userId);
    setError(null);
    try {
      await action();
      router.refresh();
    } catch {
      setError(t("memberActionFailed"));
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {error ? (
        <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
          <p className="text-sm font-medium text-danger">{error}</p>
        </div>
      ) : null}

      <div className="overflow-x-auto">
        <table className="w-full min-w-md border-collapse text-sm">
          <caption className="sr-only">{t("membersCaption")}</caption>
          <thead>
            <tr className="border-b border-border text-left">
              <th scope="col" className="py-2 pr-3 font-medium text-text-muted">
                {t("memberColumn")}
              </th>
              <th scope="col" className="py-2 pr-3 font-medium text-text-muted">
                {t("roleColumn")}
              </th>
              <th scope="col" className="py-2 text-right font-medium text-text-muted">
                <span className="sr-only">{t("actionsColumn")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => {
              const isSelf = member.user_id === currentUserId;
              const outranksMe = ROLE_RANK[member.role] > myRank;
              const actionable = !isSelf && !outranksMe;
              const busy = pendingId === member.user_id;

              return (
                <tr key={member.user_id} className="border-b border-border last:border-0">
                  <td className="py-3 pr-3">
                    <span className="block font-medium text-text">
                      {member.display_name}
                      {isSelf ? <span className="text-text-muted"> · {t("you")}</span> : null}
                    </span>
                    <span className="block text-xs text-text-muted">{member.email}</span>
                  </td>
                  <td className="py-3 pr-3">
                    {mayChangeRoles && actionable ? (
                      <select
                        value={member.role}
                        disabled={busy}
                        aria-label={t("roleFor", { name: member.display_name })}
                        onChange={(event) =>
                          act(member.user_id, () =>
                            changeMemberRole(
                              organization.slug,
                              member.user_id,
                              event.target.value as Role,
                            ),
                          )
                        }
                        className="rounded-md border border-border bg-surface px-2 py-1 text-sm text-text disabled:opacity-60"
                      >
                        {grantable.map((role) => (
                          <option key={role} value={role}>
                            {t(`roles.${role}`)}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-text-muted">{t(`roles.${member.role}`)}</span>
                    )}
                  </td>
                  <td className="py-3 text-right">
                    {mayRemove && actionable ? (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          act(member.user_id, () => removeMember(organization.slug, member.user_id))
                        }
                        className="rounded-md border border-border px-2.5 py-1 text-sm text-danger transition-colors duration-fast hover:bg-danger-subtle disabled:opacity-60"
                      >
                        {t("removeAction")}
                      </button>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
