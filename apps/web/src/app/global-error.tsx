"use client";

/**
 * Last resort: the root layout itself failed, so this replaces <html> entirely
 * and cannot use the app's fonts, tokens or layout. Inline styles only.
 */
export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          padding: "1.5rem",
          background: "#ffffff",
          color: "#171c23",
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        }}
      >
        <div style={{ maxWidth: "32rem" }}>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0 }}>
            AI Workspace could not start
          </h1>
          <p style={{ fontSize: "0.875rem", color: "#58616e", marginTop: "0.5rem" }}>
            An unexpected error stopped the application from rendering.
            {error.digest ? ` Reference: ${error.digest}.` : ""}
          </p>
          <button
            type="button"
            onClick={retry}
            style={{
              marginTop: "1.25rem",
              padding: "0.375rem 0.75rem",
              fontSize: "0.875rem",
              fontWeight: 500,
              color: "#ffffff",
              background: "#2a4bc4",
              border: 0,
              borderRadius: "0.375rem",
              cursor: "pointer",
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
