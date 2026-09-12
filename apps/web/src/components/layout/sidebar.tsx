/**
 * The navigation region. Deliberately empty: task 1.4 supplies the items and
 * active states. It exists now so the frame has something to lay out, and so the
 * landmark and its label are settled.
 *
 * Rendered twice — inline on large screens, inside the drawer below that — so the
 * `id` is passed in and given only to the instance the toggle controls.
 */
export function Sidebar({ id }: { id?: string }) {
  return (
    <nav id={id} aria-label="Main" className="flex h-full flex-col gap-1 p-3">
      <p className="px-2 py-1.5 text-xs text-text-subtle">Navigation arrives in task 1.4.</p>
    </nav>
  );
}
