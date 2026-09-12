/**
 * Theme preference, shared by the inline script and the React control.
 *
 * Three values, and "system" is the default: an explicit choice should be the
 * user's, not ours. "system" stores nothing and leaves `data-theme` unset, so the
 * CSS media-query fallback in globals.css takes over.
 */
export const THEMES = ["light", "dark", "system"] as const;
export type Theme = (typeof THEMES)[number];

export const THEME_STORAGE_KEY = "ai-workspace-theme";

export function isTheme(value: unknown): value is Theme {
  return typeof value === "string" && (THEMES as readonly string[]).includes(value);
}

/**
 * Runs before first paint, inlined into <head>, so the document never renders in
 * one theme and then swaps. Kept as a string because it must execute before React
 * exists — deliberately small, and it must not throw: localStorage is unavailable
 * in some privacy modes, and a failure here would block the whole page.
 */
export const THEME_INIT_SCRIPT = `
(function(){try{
var t=localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});
if(t==="light"||t==="dark"){document.documentElement.dataset.theme=t}
}catch(e){}})();
`.trim();

/**
 * A minimal external store for the preference.
 *
 * `useSyncExternalStore` rather than `useState` in an effect: the value lives
 * outside React (localStorage plus a DOM attribute), the server cannot know it,
 * and this is the API that hydrates a server snapshot and then swaps to the
 * client's without a mismatch — or a cascading render.
 */
const listeners = new Set<() => void>();

export function subscribeToTheme(onChange: () => void): () => void {
  listeners.add(onChange);
  // Keep other tabs in step.
  window.addEventListener("storage", onChange);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return isTheme(stored) ? stored : "system";
  } catch {
    // Unavailable in some privacy modes. Following the device is a fine default.
    return "system";
  }
}

/** The server has no preference to read; hydration starts from this. */
export function readServerTheme(): Theme {
  return "system";
}

export function writeTheme(theme: Theme): void {
  try {
    if (theme === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // The choice still applies to this page view via the store notification.
  }
  for (const listener of listeners) listener();
}

/** Applies the resolved preference to the document. Called from an effect. */
export function applyTheme(theme: Theme): void {
  if (theme === "system") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
}
