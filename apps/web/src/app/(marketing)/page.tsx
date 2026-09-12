import Link from "next/link";

/**
 * Placeholder for the public landing page (task 14.1). It exists now so `/` is
 * owned by the marketing group: the authenticated product lives under concrete
 * routes such as `/workspace`, which keeps the two from colliding at the root.
 */
export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">AI Workspace</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-text sm:text-3xl">
        Document intelligence for teams
      </h1>
      <p className="mt-3 max-w-prose text-sm text-text-muted">
        Upload documents, search them semantically, and ask questions that come back with citations.
        This page is a placeholder until task 14.1.
      </p>
      <div className="mt-7 flex flex-wrap gap-3">
        <Link
          href="/workspace"
          className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors hover:bg-accent-hover"
        >
          Open the workspace
        </Link>
        <Link
          href="/design"
          className="rounded-md border border-border-strong px-3 py-1.5 text-sm font-medium text-text transition-colors hover:bg-surface-muted"
        >
          Design tokens
        </Link>
      </div>
    </main>
  );
}
