import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "next-env.d.ts"]),
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["**/*.test.*"],
    rules: {
      complexity: ["error", 6],
      "max-depth": ["error", 2],
      "max-lines": ["error", { max: 120, skipBlankLines: true }],
      "max-lines-per-function": ["error", { max: 40, skipBlankLines: true, skipComments: true }],
      "max-params": ["error", 4],
      "no-console": "error",
    },
  },
  {
    files: ["src/features/chat/**/*.ts"],
    ignores: ["**/*.test.*"],
    rules: { "max-lines-per-function": ["error", { max: 30, skipBlankLines: true, skipComments: true }] },
  },
  {
    rules: {
      "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "never" }],
      "import/no-default-export": "error",
      "no-else-return": "error",
      "no-restricted-syntax": ["error", "SwitchStatement"],
    },
  },
  {
    files: ["src/app/page.tsx", "src/app/layout.tsx", "src/app/not-found.tsx", "src/app/error.tsx", "*.config.*"],
    rules: { "import/no-default-export": "off" },
  },
]);

export default eslintConfig;
