import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-2xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">Error 404</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-text">Page not found</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        This address does not match anything in the workspace. It may have been moved, or the link
        may be out of date.
      </p>
      <div className="mt-6">
        <Link
          href="/"
          className="inline-block rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors hover:bg-accent-hover"
        >
          Back to the workspace
        </Link>
      </div>
    </div>
  );
}
