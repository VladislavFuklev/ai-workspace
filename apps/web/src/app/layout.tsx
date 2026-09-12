import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import "./globals.css";

// next/font self-hosts the files and emits a size-adjusted fallback, so there is
// no third-party request at runtime and no layout shift when the face swaps in.
const sans = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AI Workspace",
    template: "%s · AI Workspace",
  },
  description: "Multi-tenant AI document intelligence platform",
};

export const viewport: Viewport = {
  // Matches --color-bg in each theme, so the browser chrome does not flash a
  // different colour than the page behind it.
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0d1116" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // suppressHydrationWarning: task 1.5 will set data-theme on this element
    // before hydration, which the server render cannot know about.
    <html lang="en" className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
