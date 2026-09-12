import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Design tokens · AI Workspace",
  description: "Every colour, type, spacing, radius and elevation token, in both themes.",
};

/**
 * Reference surface for the design system. Not part of the product: it exists so
 * the tokens can be inspected together and reviewed at real breakpoints. Task
 * 1.10 decides whether it grows into a component gallery.
 *
 * Class names are written out in full rather than composed from a token name.
 * Tailwind scans source as text, so `bg-${token}` produces no CSS at all — a
 * mistake that builds and typechecks cleanly and renders unstyled.
 */

const SURFACES = [
  { name: "bg", swatch: "bg-bg", use: "page background" },
  { name: "surface", swatch: "bg-surface", use: "cards, panels" },
  { name: "surface-muted", swatch: "bg-surface-muted", use: "secondary panels, table headers" },
  { name: "surface-sunken", swatch: "bg-surface-sunken", use: "wells, code blocks" },
];

const TEXT = [
  { name: "text", cls: "text-text", use: "body and headings" },
  { name: "text-muted", cls: "text-text-muted", use: "secondary information" },
  { name: "text-subtle", cls: "text-text-subtle", use: "placeholders, metadata" },
];

const STATUS = [
  {
    name: "accent",
    solid: "bg-accent text-accent-fg",
    tint: "bg-accent-subtle text-accent",
    text: "text-accent",
    use: "primary action, links",
  },
  {
    name: "success",
    solid: "bg-success text-success-fg",
    tint: "bg-success-subtle text-success",
    text: "text-success",
    use: "completed processing",
  },
  {
    name: "warning",
    solid: "bg-warning text-warning-fg",
    tint: "bg-warning-subtle text-warning",
    text: "text-warning",
    use: "degraded, needs attention",
  },
  {
    name: "danger",
    solid: "bg-danger text-danger-fg",
    tint: "bg-danger-subtle text-danger",
    text: "text-danger",
    use: "failure, destructive action",
  },
];

const TYPE = [
  { name: "text-3xl", cls: "text-3xl", sample: "Page title", size: "1.875rem" },
  { name: "text-2xl", cls: "text-2xl", sample: "Section heading", size: "1.5rem" },
  { name: "text-xl", cls: "text-xl", sample: "Subsection", size: "1.25rem" },
  { name: "text-lg", cls: "text-lg", sample: "Emphasised body", size: "1rem" },
  { name: "text-base", cls: "text-base", sample: "Body — the default", size: "0.875rem" },
  { name: "text-sm", cls: "text-sm", sample: "Secondary, table cells", size: "0.8125rem" },
  { name: "text-xs", cls: "text-xs", sample: "Metadata, labels", size: "0.75rem" },
];

const SPACING = [
  { name: "1", cls: "size-1" },
  { name: "2", cls: "size-2" },
  { name: "3", cls: "size-3" },
  { name: "4", cls: "size-4" },
  { name: "6", cls: "size-6" },
  { name: "8", cls: "size-8" },
  { name: "12", cls: "size-12" },
  { name: "16", cls: "size-16" },
];

const SHAPES = [
  { name: "rounded-sm", cls: "size-16 rounded-sm border border-border bg-surface-muted" },
  { name: "rounded-md", cls: "size-16 rounded-md border border-border bg-surface-muted" },
  { name: "rounded-lg", cls: "size-16 rounded-lg border border-border bg-surface-muted" },
  { name: "rounded-xl", cls: "size-16 rounded-xl border border-border bg-surface-muted" },
  { name: "shadow-sm", cls: "size-16 rounded-lg bg-surface shadow-sm" },
  { name: "shadow-md", cls: "size-16 rounded-lg bg-surface shadow-md" },
];

const LAYERS = [
  { name: "z-sticky", value: "10", use: "a row or toolbar that pins while scrolling" },
  { name: "z-header", value: "30", use: "the application header" },
  { name: "z-backdrop", value: "40", use: "dimmed ground behind a modal" },
  { name: "z-drawer", value: "50", use: "the navigation drawer" },
  { name: "z-popover", value: "60", use: "menus, tooltips, comboboxes" },
  { name: "z-toast", value: "70", use: "transient notifications" },
  { name: "z-skip-link", value: "80", use: "above everything, or it cannot be used" },
];

const MOTION = [
  { name: "duration-fast", value: "120ms", use: "hover, focus, colour changes" },
  { name: "duration-slow", value: "240ms", use: "a panel entering or leaving" },
  { name: "ease-out", value: "cubic-bezier(0.16, 1, 0.3, 1)", use: "something arriving" },
  {
    name: "ease-in-out",
    value: "cubic-bezier(0.65, 0, 0.35, 1)",
    use: "something moving in place",
  },
];

const METRICS = [
  { name: "h-header", value: "3.5rem", use: "application header height" },
  { name: "w-sidebar", value: "15rem", use: "sidebar at lg and up" },
  { name: "w-drawer", value: "18rem", use: "navigation drawer below lg" },
  { name: "max-w-content", value: "64rem", use: "reading width of a content column" },
];

function TokenTable({ rows }: { rows: { name: string; value: string; use: string }[] }) {
  return (
    <div className="divide-y divide-border rounded-lg border border-border">
      {rows.map((row) => (
        <div
          key={row.name}
          className="flex flex-col gap-0.5 px-4 py-2.5 sm:flex-row sm:items-baseline sm:gap-6"
        >
          <span className="font-mono text-xs text-text sm:w-40 sm:shrink-0">{row.name}</span>
          <span className="font-mono text-xs text-text-muted sm:w-56 sm:shrink-0">{row.value}</span>
          <span className="text-xs text-text-subtle">{row.use}</span>
        </div>
      ))}
    </div>
  );
}

function Section({
  title,
  note,
  children,
}: {
  title: string;
  note: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-t border-border pt-8">
      <h2 className="text-xl font-semibold tracking-tight text-text">{title}</h2>
      <p className="mt-1 max-w-prose text-sm text-text-muted">{note}</p>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function DesignTokensPage() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      <header className="pb-8">
        <p className="font-mono text-xs tracking-wide text-text-subtle uppercase">Design system</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text">Tokens</h1>
        <p className="mt-2 max-w-prose text-sm text-text-muted">
          Every value the interface is allowed to use. Components reference these semantic names,
          never a raw colour, so a theme change happens in one file. Contrast is measured by{" "}
          <code className="font-mono text-xs text-text">scripts/check-contrast.mjs</code>, not
          estimated.
        </p>
      </header>

      <div className="flex flex-col gap-10">
        <Section
          title="Surfaces"
          note="Four levels of ground. Regions are separated by a border first and elevation second — depth is for things that float, not for decoration."
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {SURFACES.map((surface) => (
              <div key={surface.name} className="overflow-hidden rounded-lg border border-border">
                <div className={`h-16 ${surface.swatch}`} />
                <div className="border-t border-border bg-surface px-3 py-2">
                  <p className="font-mono text-xs text-text">{surface.name}</p>
                  <p className="mt-0.5 text-xs text-text-muted">{surface.use}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section
          title="Text"
          note="Three levels of emphasis. A fourth would fall below the contrast floor, which is why there is not one."
        >
          <dl className="divide-y divide-border rounded-lg border border-border">
            {TEXT.map((entry) => (
              <div
                key={entry.name}
                className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-baseline sm:gap-6"
              >
                <dt className="font-mono text-xs text-text-muted sm:w-40 sm:shrink-0">
                  {entry.name}
                </dt>
                <dd className={`flex-1 ${entry.cls}`}>
                  The quick brown fox jumps over the lazy dog
                  <span className="ml-2 text-xs text-text-subtle">— {entry.use}</span>
                </dd>
              </div>
            ))}
          </dl>
        </Section>

        <Section
          title="Accent and status"
          note="One accent used sparingly, plus three status colours. Each has a solid form for fills and a tint for backgrounds. Colour never carries meaning alone — every status also gets a label."
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {STATUS.map((status) => (
              <div key={status.name} className="rounded-lg border border-border p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-md px-2.5 py-1 text-xs font-medium ${status.solid}`}>
                    Solid
                  </span>
                  <span className={`rounded-md px-2.5 py-1 text-xs font-medium ${status.tint}`}>
                    Tint
                  </span>
                  <span className={`text-sm font-medium ${status.text}`}>Text</span>
                </div>
                <p className="mt-3 font-mono text-xs text-text">{status.name}</p>
                <p className="mt-0.5 text-xs text-text-muted">{status.use}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section
          title="Type scale"
          note="Seven rungs, and a screen should use no more than three. A short scale makes hierarchy a decision rather than an accident."
        >
          <div className="divide-y divide-border rounded-lg border border-border">
            {TYPE.map((entry) => (
              <div
                key={entry.name}
                className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-baseline sm:gap-6"
              >
                <span className="font-mono text-xs text-text-muted sm:w-28 sm:shrink-0">
                  {entry.name}
                </span>
                <span className={`flex-1 tracking-tight text-text ${entry.cls}`}>
                  {entry.sample}
                </span>
                <span className="font-mono text-xs text-text-subtle">{entry.size}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section
          title="Spacing"
          note="A 0.25rem base. Consistent spacing is the clearest signal that an interface was designed rather than assembled."
        >
          <div className="flex flex-wrap items-end gap-4">
            {SPACING.map((step) => (
              <div key={step.name} className="flex flex-col items-center gap-1.5">
                <div className={`rounded-sm bg-accent ${step.cls}`} />
                <span className="font-mono text-xs text-text-muted">{step.name}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section
          title="Radius and elevation"
          note="Four radii and two shadows. Anything rounder reads as a toy, and a third shadow level has never been the answer to a layout problem."
        >
          <div className="flex flex-wrap gap-4">
            {SHAPES.map((shape) => (
              <div key={shape.name} className="flex flex-col items-center gap-1.5">
                <div className={shape.cls} />
                <span className="font-mono text-xs text-text-muted">{shape.name}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section
          title="Layering"
          note="Every stacking context the product has. A raw z-index is a number nobody can reason about three screens later, so there are no raw z-indexes."
        >
          <TokenTable rows={LAYERS} />
        </Section>

        <Section
          title="Motion"
          note="Two durations and two easings. Anything slower than slow reads as lag. Under prefers-reduced-motion the tokens themselves collapse to nothing, so code reading them directly is covered too."
        >
          <TokenTable rows={MOTION} />
        </Section>

        <Section
          title="Frame metrics"
          note="The dimensions of the application shell, so the layout does not repeat them and a change lands in one place."
        >
          <TokenTable rows={METRICS} />
        </Section>

        <Section
          title="Interactive states"
          note="Tab through this row: every control is reachable, and the focus ring is the token rather than a browser default that a reset removed."
        >
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-fg transition-colors hover:bg-accent-hover"
            >
              Primary
            </button>
            <button
              type="button"
              className="rounded-md border border-border-strong px-3 py-1.5 text-sm font-medium text-text transition-colors hover:bg-surface-muted"
            >
              Secondary
            </button>
            <button
              type="button"
              className="rounded-md bg-danger px-3 py-1.5 text-sm font-medium text-danger-fg"
            >
              Destructive
            </button>
            <button
              type="button"
              disabled
              className="cursor-not-allowed rounded-md border border-border px-3 py-1.5 text-sm font-medium text-text-subtle"
            >
              Disabled
            </button>
            <a
              href="#top"
              className="rounded-sm text-sm font-medium text-accent underline underline-offset-2"
            >
              A link
            </a>
          </div>
        </Section>
      </div>
    </main>
  );
}
