import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";

/**
 * Server Component: it composes the shell but holds no state, so nothing here is
 * shipped to the browser beyond what AppShell already needs.
 *
 * LayoutProps<"/"> is correct even though this layout wraps /workspace: route
 * groups create no URL segment, so Next generates LayoutRoutes = "/" only.
 */
export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <AppShell
      header={
        <Link
          href="/"
          className="rounded-sm text-sm font-semibold tracking-tight text-text hover:text-accent"
        >
          AI Workspace
        </Link>
      }
    >
      {children}
    </AppShell>
  );
}
