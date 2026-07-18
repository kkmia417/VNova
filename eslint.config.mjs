import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      ".pytest-tmp/**",
      ".pytest-tmp-*/**",
      ".venv/**",
      "**/coverage/**",
      "**/dist/**",
      "**/generated/**",
      "node_modules/**",
    ],
  },
  {
    files: ["**/*.{js,mjs}"],
    ...eslint.configs.recommended,
  },
  {
    files: ["**/*.ts"],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.strictTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/consistent-type-exports": "error",
      "@typescript-eslint/consistent-type-imports": ["error", { fixStyle: "inline-type-imports" }],
      "@typescript-eslint/no-import-type-side-effects": "error",
      "@typescript-eslint/no-restricted-types": [
        "error",
        {
          types: {
            Object: { message: "Use object or a specific record type." },
            Function: { message: "Use an explicit function signature." },
          },
        },
      ],
      eqeqeq: ["error", "always"],
    },
  },
);
