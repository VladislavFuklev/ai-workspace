"use client";

import { useEffect, useRef, useState } from "react";

/**
 * The authenticated frame: sidebar beside the content on large screens, a modal
 * drawer below that.
 *
 * The drawer is a native <dialog>. The browser then owns focus trapping, Escape,
 * and making the background inert — three things a hand-written implementation
 * gets subtly wrong. Only opening, closing and returning focus are ours.
 */
export function AppShell({
  sidebar,
  drawerSidebar,
  header,
  children,
}: {
  /** Rendered inline at lg and up. */
  sidebar: React.ReactNode;
  /** Rendered inside the drawer below lg. A separate node because the two are in
   *  the DOM at the same time and only one may carry the id the toggle controls. */
  drawerSidebar: React.ReactNode;
  header: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // Escape and backdrop dismissal both fire the dialog's own close event, so this
  // is the single place state and focus are restored.
  const handleClose = () => {
    setOpen(false);
    toggleRef.current?.focus();
  };

  return (
    <div className="min-h-dvh bg-bg">
      <a
        href="#main"
        className="sr-only rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-fg focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-30 h-14 border-b border-border bg-surface">
        <div className="flex h-full items-center gap-3 px-4 sm:px-6">
          <button
            ref={toggleRef}
            type="button"
            onClick={() => setOpen(true)}
            aria-expanded={open}
            aria-controls="app-navigation"
            className="-ml-1 rounded-md p-2 text-text-muted transition-colors hover:bg-surface-muted hover:text-text lg:hidden"
          >
            <span className="sr-only">Open navigation</span>
            <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5" fill="currentColor">
              <path d="M3 5.5h14v1.5H3zM3 9.25h14v1.5H3zM3 13h14v1.5H3z" />
            </svg>
          </button>
          {header}
        </div>
      </header>

      <div className="flex">
        {/* Rendered inline only at lg and up; below that the drawer holds it. */}
        <div className="sticky top-14 hidden h-[calc(100dvh-3.5rem)] w-60 shrink-0 border-r border-border bg-surface lg:block">
          {sidebar}
        </div>

        <main id="main" tabIndex={-1} className="min-w-0 flex-1 focus:outline-none">
          {children}
        </main>
      </div>

      <dialog
        ref={dialogRef}
        onClose={handleClose}
        // A native dialog's click target covers the backdrop, so compare against
        // the element itself to tell a backdrop click from a click inside.
        onClick={(event) => {
          if (event.target === dialogRef.current) dialogRef.current?.close();
        }}
        aria-label="Navigation"
        className="m-0 h-dvh max-h-dvh w-72 max-w-[85vw] border-r border-border bg-surface p-0 text-text backdrop:bg-neutral-950/40 lg:hidden"
      >
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <span className="text-sm font-semibold tracking-tight text-text">AI Workspace</span>
          <button
            type="button"
            onClick={() => dialogRef.current?.close()}
            className="-mr-1 rounded-md p-2 text-text-muted transition-colors hover:bg-surface-muted hover:text-text"
          >
            <span className="sr-only">Close navigation</span>
            <svg aria-hidden="true" viewBox="0 0 20 20" className="size-5" fill="currentColor">
              <path d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L8.94 10l-4.72 4.72a.75.75 0 1 0 1.06 1.06L10 11.06l4.72 4.72a.75.75 0 1 0 1.06-1.06L11.06 10l4.72-4.72a.75.75 0 0 0-1.06-1.06L10 8.94z" />
            </svg>
          </button>
        </div>
        {drawerSidebar}
      </dialog>
    </div>
  );
}
