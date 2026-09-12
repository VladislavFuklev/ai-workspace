import type { Metadata } from "next";

export const metadata: Metadata = { title: "Usage" };

export default function UsagePage() {
  return (
    <div className="mx-auto max-w-content px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Usage</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        Token consumption and AI cost for the organisation. Phase 10.
      </p>
    </div>
  );
}
