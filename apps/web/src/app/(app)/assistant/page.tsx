import type { Metadata } from "next";

import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Assistant" };

export default function AssistantPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Assistant</h1>
      <div className="mt-6">
        <EmptyState
          title="No conversations yet"
          description="Ask a question about your documents and the answer comes back with the passages it came from."
          action={
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text-subtle"
            >
              Start a conversation — Phase 7
            </button>
          }
        />
      </div>
    </div>
  );
}
