/**
 * For a pending action inside a control, where a skeleton makes no sense — a
 * submit button, an inline refresh. Never as a whole-page loading state.
 *
 * The animation is suppressed under prefers-reduced-motion by the base layer, so
 * the label is what conveys "working", not the movement.
 */
export function Spinner({
  label = "Loading",
  className = "",
}: {
  label?: string;
  className?: string;
}) {
  return (
    <span role="status" className={`inline-flex items-center ${className}`}>
      <svg aria-hidden="true" viewBox="0 0 20 20" className="size-4 animate-spin" fill="none">
        <circle
          cx="10"
          cy="10"
          r="7.5"
          stroke="currentColor"
          strokeOpacity="0.25"
          strokeWidth="2.5"
        />
        <path
          d="M17.5 10a7.5 7.5 0 0 0-7.5-7.5"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </span>
  );
}
