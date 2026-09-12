import type { Metadata } from "next";

import { EmptyState, ErrorState, Skeleton, SkeletonText, Spinner } from "@/components/ui";

export const metadata: Metadata = { title: "Components" };

/**
 * Every reusable component in the states it actually ships in.
 *
 * The point is the awkward ones. A component gallery that shows only the happy
 * path is where empty states go to be forgotten, and empty and error are the two
 * that reach users broken.
 *
 * Copy here is deliberately untranslated: this is an internal reference surface,
 * and running it through the catalogue would fill the catalogue with strings no
 * user ever sees.
 */
function Case({
  title,
  note,
  children,
}: {
  title: string;
  note: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-t border-border pt-6">
      <h2 className="text-sm font-semibold text-text">{title}</h2>
      <p className="mt-1 max-w-prose text-xs text-text-muted">{note}</p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function ComponentsPage() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">Design system</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text">Components</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        The shared components, in the states they ship in. Loading, empty and error are here
        deliberately: they are the ones that reach users broken.
      </p>

      <div className="mt-8 flex flex-col gap-8">
        <Case
          title="Skeleton"
          note="Shaped like the content it replaces, so nothing moves when the real thing arrives. Hidden from assistive technology — the region announces busy instead."
        >
          <div className="max-w-md rounded-lg border border-border p-4">
            <Skeleton className="h-8 w-40" />
            <SkeletonText className="mt-4" lines={3} />
          </div>
        </Case>

        <Case
          title="Empty state"
          note="Says what the place is, why it is empty, and the one action that fills it. Never a bare “No data”."
        >
          <EmptyState
            title="No documents yet"
            description="Upload a PDF, Word file or plain text and it will be processed, chunked and made searchable."
            action={
              <button
                type="button"
                className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors duration-fast hover:bg-accent-hover"
              >
                Upload a document
              </button>
            }
          />
        </Case>

        <Case
          title="Empty state — no action"
          note="Some surfaces fill themselves. Offering a button that does nothing is worse than offering none."
        >
          <EmptyState
            title="No usage recorded"
            description="Token consumption and AI cost appear here once the workspace starts processing documents."
          />
        </Case>

        <Case
          title="Error state"
          note="Written for the reader, never carrying raw error text. The reference is what support can actually use."
        >
          <ErrorState
            title="Something went wrong"
            description="This could not be loaded. Trying again is often enough."
            reference="req-7f3a9c21"
          />
        </Case>

        <Case
          title="Error state — long content"
          note="Deliberately awkward: a long message and a long reference must not break the layout."
        >
          <ErrorState
            title="The document could not be processed"
            description="Extraction failed after three attempts. The file may be encrypted, corrupt, or a scan with no text layer — re-uploading a text-based version usually resolves it."
            reference="req-0f8e2a41-9c7b-4d3e-a1f5-6b2c8d9e0a3f"
          />
        </Case>

        <Case title="Spinner" note="For a pending control, never as a whole-page loading state.">
          <div className="flex items-center gap-4">
            <Spinner label="Loading" />
            <span className="text-sm text-text-muted">Inline, with a visually hidden label</span>
          </div>
        </Case>
      </div>
    </main>
  );
}
