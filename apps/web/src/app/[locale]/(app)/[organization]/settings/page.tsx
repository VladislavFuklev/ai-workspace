import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import { getServerUser } from "@/features/auth/server";
import { DangerZone } from "@/features/organizations/danger-zone";
import { MembersTable } from "@/features/organizations/members-table";
import { RenameOrganizationForm } from "@/features/organizations/rename-form";
import { getMembers, getOrganization } from "@/features/organizations/server";
import { PERMISSIONS, can } from "@/features/organizations/schemas";

export async function generateMetadata() {
  const t = await getTranslations("settings");
  return { title: t("title") };
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border bg-surface p-4 sm:p-6">
      <h2 className="text-sm font-medium text-text">{title}</h2>
      {description ? <p className="mt-1 text-sm text-text-muted">{description}</p> : null}
      <div className="mt-4">{children}</div>
    </section>
  );
}

/**
 * The organisation's own settings: its name, its people, and the two ways out.
 *
 * Each block is rendered only if the caller may use it, and the permissions come
 * from the API rather than from a table copied into this app — see
 * `schemas.ts`. The API checks every request regardless; this only decides what
 * is worth showing.
 */
export default async function SettingsPage({
  params,
}: PageProps<"/[locale]/[organization]/settings">) {
  const { organization: slug } = await params;
  const [t, user, organization, members] = await Promise.all([
    getTranslations("organizations"),
    getServerUser(),
    getOrganization(slug),
    getMembers(slug),
  ]);

  // The layout above already resolved this organisation, so a failure here is
  // the API going away between two requests rather than a permission question.
  if (!organization.ok) {
    if (organization.status === 404) notFound();
    throw new Error(`Could not load the organisation (${organization.status ?? "no response"}).`);
  }

  return (
    <div className="mx-auto flex max-w-content flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">{t("settingsTitle")}</h1>

      {can(organization.data, PERMISSIONS.update) ? (
        <Section title={t("generalTitle")}>
          <RenameOrganizationForm organization={organization.data} />
        </Section>
      ) : (
        <Section title={t("generalTitle")} description={t("addressFixed", { slug })}>
          <p className="text-sm text-text">{organization.data.name}</p>
        </Section>
      )}

      <Section
        title={t("membersTitle")}
        description={t("membersBody", { role: t(`roles.${organization.data.role}`) })}
      >
        {members.ok ? (
          <MembersTable
            organization={organization.data}
            members={members.data}
            currentUserId={user?.id ?? ""}
          />
        ) : (
          <p className="text-sm text-danger">{t("membersUnavailable")}</p>
        )}
      </Section>

      <Section title={t("dangerTitle")}>
        <DangerZone organization={organization.data} />
      </Section>
    </div>
  );
}
