import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier/flat";
import boundaries from "eslint-plugin-boundaries";

/**
 * Layering is documented in docs/ARCHITECTURE.md:
 *
 *     app → features → components → lib
 *
 * `boundaries` turns that from a convention into a build failure. The capture on
 * the feature element is what lets a feature import itself while still being
 * blocked from reaching into a sibling feature's internals.
 */
const layering = {
  files: ["src/**/*.{ts,tsx}"],
  plugins: { boundaries },
  settings: {
    "boundaries/include": ["src/**/*"],
    "boundaries/elements": [
      { type: "app", pattern: "src/app/**" },
      { type: "feature", pattern: "src/features/*", capture: ["feature"] },
      { type: "component", pattern: "src/components/**" },
      { type: "lib", pattern: "src/lib/**" },
    ],
  },
  rules: {
    "boundaries/dependencies": [
      "error",
      {
        default: "disallow",
        message:
          "{{from.element.type}} may not import {{to.element.type}} — see docs/ARCHITECTURE.md",
        policies: [
          // Third-party packages are everyone's business.
          { allow: { to: { module: { origin: "external" } } } },
          // Routing composes features; it does not implement them.
          {
            from: { element: { type: "app" } },
            allow: {
              to: { element: { types: { anyOf: ["app", "feature", "component", "lib"] } } },
            },
          },
          // A feature may reach downward, and into itself...
          {
            from: { element: { type: "feature" } },
            allow: { to: { element: { types: { anyOf: ["component", "lib"] } } } },
          },
          {
            from: { element: { type: "feature" } },
            allow: {
              to: { element: { type: "feature", captured: { feature: "{{from.feature}}" } } },
            },
          },
          // ...but never into a sibling feature's internals.
          // Primitives know nothing about product features or routing.
          {
            from: { element: { type: "component" } },
            allow: { to: { element: { types: { anyOf: ["component", "lib"] } } } },
          },
          { from: { element: { type: "lib" } }, allow: { to: { element: { type: "lib" } } } },
        ],
      },
    ],
  },
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  layering,
  // Must stay last: switches off every rule Prettier owns.
  prettier,
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
