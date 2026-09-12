import type { Metadata } from "next";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Settings</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        Organisation, members and roles. Phase 4.
      </p>
    </div>
  );
}
