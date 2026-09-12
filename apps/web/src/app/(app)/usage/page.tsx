import type { Metadata } from "next";

import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Usage" };

export default function UsagePage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Usage</h1>
      <div className="mt-6">
        <EmptyState
          title="No usage recorded"
          description="Token consumption and AI cost appear here once the workspace starts processing documents."
        />
      </div>
    </div>
  );
}
