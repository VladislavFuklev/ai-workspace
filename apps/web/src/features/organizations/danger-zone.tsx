"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/lib/api";

import { deleteOrganization, leaveOrganization } from "./api";
import { PERMISSIONS, can, type Organization } from "./schemas";

/**
 * Leaving, and ending the organisation.
 *
 * Both are confirmed in place rather than behind `window.confirm`: a native
 * dialog cannot say *which* organisation, and "OK" is not a word anyone reads.
 * Deletion asks for the name, because the cost of a mistaken click here is the
 * whole workspace.
 *
 * 409 is shown specifically. "The last owner cannot leave" is actionable — make
 * someone else an owner — and a generic failure would leave the person guessing.
 */
export function DangerZone({ organization }: { organization: Organization }) {
  const t = useTranslations("organizations");
  const router = useRouter();
  const [confirmName, setConfirmName] = useState("");
  const [pending, setPending] = useState<"leave" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mayDelete = can(organization, PERMISSIONS.delete);

  async function run(action: "leave" | "delete") {
    setPending(action);
    setError(null);
    try {
      if (action === "leave") await leaveOrganization(organization.slug);
      else await deleteOrganization(organization.slug);
      // Everything about the current organisation is gone; /enter picks another
      // one, or offers to create the first.
      router.replace("/enter");
      router.refresh();
    } catch (caught) {
      const conflict = caught instanceof ApiError && caught.status === 409;
      setError(conflict ? t("lastOwner") : t("memberActionFailed"));
      setPending(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {error ? (
        <div role="alert" className="rounded-md border border-danger-subtle bg-danger-subtle p-3">
          <p className="text-sm font-medium text-danger">{error}</p>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-text">{t("leaveTitle")}</p>
          <p className="text-sm text-text-muted">{t("leaveBody")}</p>
        </div>
        <button
          type="button"
          disabled={pending !== null}
          onClick={() => run("leave")}
          className="rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text transition-colors duration-fast hover:bg-surface-muted disabled:opacity-60"
        >
          {pending === "leave" ? t("leavePending") : t("leaveAction")}
        </button>
      </div>

      {mayDelete ? (
        <div className="border-t border-border pt-4">
          <p className="text-sm font-medium text-danger">{t("deleteTitle")}</p>
          <p className="text-sm text-text-muted">{t("deleteBody")}</p>
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-text-muted">
                {t("deleteConfirmLabel", { name: organization.name })}
              </span>
              <input
                value={confirmName}
                onChange={(event) => setConfirmName(event.target.value)}
                className="rounded-md border border-border bg-surface px-2.5 py-1.5 text-sm text-text"
              />
            </label>
            <button
              type="button"
              disabled={pending !== null || confirmName.trim() !== organization.name}
              onClick={() => run("delete")}
              className="rounded-md bg-danger px-3 py-1.5 text-sm font-medium text-danger-fg transition-colors duration-fast disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pending === "delete" ? t("deletePending") : t("deleteAction")}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
