import { notFound } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { getServerUser } from "@/features/auth/server";
import { OrganizationSwitcher } from "@/features/organizations/switcher";
import { getOrganization, getOrganizations } from "@/features/organizations/server";

import { AppHeader } from "../app-header";

/**
 * Everything inside one organisation.
 *
 * The slug in the path is not trusted: the API answers 404 for a slug the caller
 * does not belong to, exactly as it does for one that does not exist, and that
 * becomes this route's not-found page. So a guessed URL tells the guesser
 * nothing about which organisations exist.
 *
 * Any other failure is rethrown into the error boundary rather than rendered as
 * an empty shell — an outage that looks like an answer is worse than an error.
 */
export default async function OrganizationLayout({
  children,
  params,
}: LayoutProps<"/[locale]/[organization]">) {
  const { organization: slug } = await params;
  const [user, current, all] = await Promise.all([
    getServerUser(),
    getOrganization(slug),
    getOrganizations(),
  ]);

  if (!current.ok) {
    if (current.status === 404 || current.status === 403) notFound();
    throw new Error(`Could not load the organisation (${current.status ?? "no response"}).`);
  }

  return (
    <AppShell
      header={
        <AppHeader userName={user?.display_name ?? ""}>
          <OrganizationSwitcher
            current={current.data}
            organizations={all.ok ? all.data : [current.data]}
          />
        </AppHeader>
      }
    >
      {children}
    </AppShell>
  );
}
