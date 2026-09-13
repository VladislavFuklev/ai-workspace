import { getTranslations } from "next-intl/server";

import { getServerUser } from "@/features/auth/server";
import { CreateOrganizationForm } from "@/features/organizations/create-form";
import { getOrganizations } from "@/features/organizations/server";
import { Link } from "@/i18n/navigation";

import { AppHeader } from "../app-header";

/**
 * Pick an organisation, or make the first one.
 *
 * Deliberately outside the app shell: there is no current organisation here, so
 * a sidebar of links into one would have nowhere to point.
 */
export default async function OrganizationsPage() {
  const [t, user, organizations] = await Promise.all([
    getTranslations("organizations"),
    getServerUser(),
    getOrganizations(),
  ]);

  if (!organizations.ok) {
    throw new Error(
      `Could not load your organisations (${organizations.status ?? "no response"}).`,
    );
  }

  return (
    <div className="min-h-dvh bg-bg">
      <header className="sticky top-0 z-header h-header border-b border-border bg-surface">
        <div className="flex h-full items-center gap-3 px-4 sm:px-6">
          <AppHeader userName={user?.display_name ?? ""} />
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-2xl px-4 py-10 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight text-text">{t("title")}</h1>
        <p className="mt-1 text-sm text-text-muted">
          {organizations.data.length > 0 ? t("subtitle") : t("emptyBody")}
        </p>

        {organizations.data.length > 0 ? (
          <ul className="mt-6 flex flex-col gap-2">
            {organizations.data.map((organization) => (
              <li key={organization.id}>
                <Link
                  href={`/${organization.slug}/workspace`}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-surface px-4 py-3 transition-colors duration-fast hover:border-accent hover:bg-surface-muted"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-text">
                      {organization.name}
                    </span>
                    <span className="block truncate text-xs text-text-muted">
                      /{organization.slug}
                    </span>
                  </span>
                  <span className="shrink-0 text-xs text-text-muted">
                    {t(`roles.${organization.role}`)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : null}

        <section className="mt-8 rounded-lg border border-border bg-surface p-4">
          <h2 className="text-sm font-medium text-text">{t("createTitle")}</h2>
          <p className="mt-1 mb-4 text-sm text-text-muted">{t("createBody")}</p>
          <CreateOrganizationForm />
        </section>
      </main>
    </div>
  );
}
