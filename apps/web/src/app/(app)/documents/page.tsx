import type { Metadata } from "next";

import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Documents" };

export default function DocumentsPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Documents</h1>
      <div className="mt-6">
        <EmptyState
          title="No documents yet"
          description="Upload a PDF, Word file or plain text and it will be processed, chunked and made searchable."
          action={
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text-subtle"
            >
              Upload a document — Phase 5
            </button>
          }
        />
      </div>
    </div>
  );
}
