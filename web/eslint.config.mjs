import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "next-env.d.ts"]),
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
