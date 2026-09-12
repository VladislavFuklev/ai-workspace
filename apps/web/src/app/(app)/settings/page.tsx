import type { Metadata } from "next";

import { EmptyState } from "@/components/ui";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Settings</h1>
      <div className="mt-6">
        <EmptyState
          title="No organisation yet"
          description="Create an organisation to invite members, assign roles and control who can see which documents."
          action={
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text-subtle"
            >
              Create an organisation — Phase 4
            </button>
          }
        />
      </div>
    </div>
  );
}
