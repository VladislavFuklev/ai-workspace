import type { Metadata } from "next";

export const metadata: Metadata = { title: "Documents" };

export default function DocumentsPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Documents</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        Upload, browse and inspect documents. Phase 5.
      </p>
    </div>
  );
}
