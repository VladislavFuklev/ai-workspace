import type { Metadata } from "next";

import { DemoForm } from "./demo-form";

export const metadata: Metadata = { title: "Forms" };

export default function FormsPage() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">Design system</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text">Forms</h1>
      <p className="mt-2 max-w-prose text-sm text-text-muted">
        React Hook Form with a Zod resolver. One schema validates in the browser and describes what
        the API is sent. Server-side field errors are placed back on their fields rather than
        summarised in a banner.
      </p>
      <div className="mt-8">
        <DemoForm />
      </div>
    </main>
  );
}
