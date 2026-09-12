/**
 * The root layout cannot render `<html>`: the `lang` attribute depends on the
 * locale, which only exists inside `[locale]`. This passes children straight
 * through, and `[locale]/layout.tsx` produces the document.
 */
export default function RootLayout({ children }: LayoutProps<"/">) {
  return children;
}
