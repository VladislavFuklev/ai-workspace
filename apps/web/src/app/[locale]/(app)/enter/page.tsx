import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ORGANIZATION_COOKIE } from "@/features/organizations/cookie";
import { getOrganizations } from "@/features/organizations/server";

/**
 * Where signing in lands, and the only route that decides *which* organisation
 * someone sees.
 *
 * It renders nothing. Every other page names its organisation in the URL, which
 * is what makes a link shareable and two tabs independent; this exists so that
 * "just take me in" has an address too.
 *
 * The remembered slug is checked against the list rather than trusted: it is a
 * cookie, so it can be stale or forged, and a redirect into an organisation the
 * caller left would render a not-found page.
 */
export default async function EnterPage({ params }: PageProps<"/[locale]/enter">) {
  const { locale } = await params;
  const [organizations, remembered] = await Promise.all([
    getOrganizations(),
    cookies().then((store) => store.get(ORGANIZATION_COOKIE)?.value),
  ]);

  if (!organizations.ok) {
    throw new Error(
      `Could not load your organisations (${organizations.status ?? "no response"}).`,
    );
  }

  const target =
    organizations.data.find((organization) => organization.slug === remembered) ??
    organizations.data[0];

  // No organisations yet: the API creates none at registration, so the picker
  // shows the create form instead of an empty list.
  redirect(target ? `/${locale}/${target.slug}/workspace` : `/${locale}/organizations`);
}
