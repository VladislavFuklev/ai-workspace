import Link from "next/link";

/**
 * Frame for the authenticated product.
 *
 * Structure only: a header region and the main landmark. The responsive sidebar,
 * breakpoints and navigation are tasks 1.2 and 1.4 — this establishes where they
 * go and the accessibility contract they inherit.
 *
 * LayoutProps<"/"> is correct even though this layout wraps /workspace: route
 * groups create no URL segment, so Next generates LayoutRoutes = "/" only.
 */
export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      {/* First focusable element on the page. Visible only once focused. */}
      <a
        href="#main"
        className="sr-only rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-fg focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50"
      >
        Skip to content
      </a>

      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
          <Link
            href="/"
            className="rounded-sm text-sm font-semibold tracking-tight text-text hover:text-accent"
          >
            AI Workspace
          </Link>
          {/* Navigation lands here in task 1.4. */}
        </div>
      </header>

      <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">
        {children}
      </main>
    </div>
  );
}
