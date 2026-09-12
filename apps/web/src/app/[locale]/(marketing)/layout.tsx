/**
 * Public surface: the landing page and anything else reachable without an
 * account. Kept separate from `(app)` so the two never share a chrome by
 * accident. The landing page itself is task 14.1.
 */
export default function MarketingLayout({ children }: LayoutProps<"/[locale]">) {
  return <div className="min-h-dvh bg-bg">{children}</div>;
}
