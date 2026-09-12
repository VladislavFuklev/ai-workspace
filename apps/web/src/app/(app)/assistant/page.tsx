import type { Metadata } from "next";

export const metadata: Metadata = { title: "Assistant" };

export default function AssistantPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Assistant</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        Ask questions about the knowledge base and get cited answers. Phase 7.
      </p>
    </div>
  );
}
