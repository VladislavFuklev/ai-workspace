/**
 * Internal reference surfaces — the design token page today, a component gallery
 * from task 1.10. Not part of the product; grouped so it is never mistaken for
 * one, and so a single place can gate it later.
 */
export default function DevLayout({ children }: LayoutProps<"/">) {
  return <div className="min-h-dvh bg-bg">{children}</div>;
}
