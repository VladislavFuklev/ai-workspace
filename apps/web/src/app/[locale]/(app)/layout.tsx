import { redirect } from "next/navigation";

import { getServerUser } from "@/features/auth/server";
import { QueryProvider } from "@/lib/query";

/**
 * The guard for everything signed-in, organisation or not.
 *
 * Asked on the server, before anything renders: a client-side check would flash
 * the page first and, more to the point, could be skipped entirely. The
 * middleware also redirects when there is no cookie at all, but that is only a
 * fast path — a cookie's presence proves nothing, and this is what verifies it.
 *
 * The frame lives one level down, in `[organization]/layout.tsx`: the pages that
 * pick or create an organisation have no organisation to draw a sidebar for.
 */
export default async function AppLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  const user = await getServerUser();

  if (!user) {
    // Next's own redirect, not the locale-aware one: it is typed as returning
    // `never`, so the compiler knows nothing below runs.
    redirect(`/${locale}/sign-in`);
  }

  return <QueryProvider>{children}</QueryProvider>;
}
