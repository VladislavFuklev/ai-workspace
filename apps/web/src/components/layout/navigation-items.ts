/**
 * The product's top-level destinations, in one place so the sidebar, the drawer
 * and anything later (a command palette, a mobile tab bar) cannot disagree.
 *
 * `segment` is what `useSelectedLayoutSegment` returns for the route — the first
 * path segment under the (app) group.
 */
export type NavigationItem = {
  segment: string;
  href: string;
  label: string;
  /** A 20×20 path, so every icon shares one grid and one stroke weight. */
  icon: string;
};

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    segment: "workspace",
    href: "/workspace",
    label: "Overview",
    icon: "M3 3.75A.75.75 0 0 1 3.75 3h5.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-5.5A.75.75 0 0 1 3 8.25zM10.75 3.75A.75.75 0 0 1 11.5 3h4.75a.75.75 0 0 1 .75.75v2.5a.75.75 0 0 1-.75.75H11.5a.75.75 0 0 1-.75-.75zM3 11.75a.75.75 0 0 1 .75-.75h5.5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-.75.75h-5.5a.75.75 0 0 1-.75-.75zM10.75 9.75a.75.75 0 0 1 .75-.75h4.75a.75.75 0 0 1 .75.75v6.5a.75.75 0 0 1-.75.75H11.5a.75.75 0 0 1-.75-.75z",
  },
  {
    segment: "documents",
    href: "/documents",
    label: "Documents",
    icon: "M4.5 3.5A1.5 1.5 0 0 1 6 2h4.94a1.5 1.5 0 0 1 1.06.44l3.06 3.06A1.5 1.5 0 0 1 15.5 6.56V16.5A1.5 1.5 0 0 1 14 18H6a1.5 1.5 0 0 1-1.5-1.5zM11 3.62V6a.5.5 0 0 0 .5.5h2.38zM7 9.75A.75.75 0 0 1 7.75 9h4.5a.75.75 0 0 1 0 1.5h-4.5A.75.75 0 0 1 7 9.75m0 3A.75.75 0 0 1 7.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1-.75-.75",
  },
  {
    segment: "assistant",
    href: "/assistant",
    label: "Assistant",
    icon: "M10 2.5c-4.14 0-7.5 2.85-7.5 6.37 0 1.98 1.07 3.75 2.74 4.92-.12.99-.5 1.9-1.1 2.66a.5.5 0 0 0 .46.8 7.2 7.2 0 0 0 3.5-1.42c.6.13 1.24.2 1.9.2 4.14 0 7.5-2.85 7.5-6.37S14.14 2.5 10 2.5M7 8.12a.94.94 0 1 1 0 1.88.94.94 0 0 1 0-1.88m3 0a.94.94 0 1 1 0 1.88.94.94 0 0 1 0-1.88m3 0a.94.94 0 1 1 0 1.88.94.94 0 0 1 0-1.88",
  },
  {
    segment: "usage",
    href: "/usage",
    label: "Usage",
    icon: "M3.75 16.5a.75.75 0 0 1-.75-.75V4.25a.75.75 0 0 1 1.5 0v10.75h11.75a.75.75 0 0 1 0 1.5zM7 13.25a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0zm3.25 0a.75.75 0 0 1-1.5 0V7.5a.75.75 0 0 1 1.5 0zm3.25 0a.75.75 0 0 1-1.5 0V9.25a.75.75 0 0 1 1.5 0zm3.25 0a.75.75 0 0 1-1.5 0V5.75a.75.75 0 0 1 1.5 0z",
  },
  {
    segment: "settings",
    href: "/settings",
    label: "Settings",
    icon: "M8.34 2.94a1.5 1.5 0 0 1 1.48-1.25h.36a1.5 1.5 0 0 1 1.48 1.25l.1.6c.4.15.78.37 1.12.63l.57-.21a1.5 1.5 0 0 1 1.82.66l.18.31a1.5 1.5 0 0 1-.34 1.9l-.46.39a5.6 5.6 0 0 1 0 1.3l.46.39a1.5 1.5 0 0 1 .34 1.9l-.18.31a1.5 1.5 0 0 1-1.82.66l-.57-.21c-.34.26-.72.48-1.12.63l-.1.6a1.5 1.5 0 0 1-1.48 1.25h-.36a1.5 1.5 0 0 1-1.48-1.25l-.1-.6a5.5 5.5 0 0 1-1.12-.63l-.57.21a1.5 1.5 0 0 1-1.82-.66l-.18-.31a1.5 1.5 0 0 1 .34-1.9l.46-.39a5.6 5.6 0 0 1 0-1.3l-.46-.39a1.5 1.5 0 0 1-.34-1.9l.18-.31a1.5 1.5 0 0 1 1.82-.66l.57.21c.34-.26.72-.48 1.12-.63zM10 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5",
  },
];
