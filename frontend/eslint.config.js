import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

const browserGlobals = {
  cancelIdleCallback: "readonly",
  cancelAnimationFrame: "readonly",
  clearInterval: "readonly",
  clearTimeout: "readonly",
  console: "readonly",
  document: "readonly",
  performance: "readonly",
  requestAnimationFrame: "readonly",
  requestIdleCallback: "readonly",
  setInterval: "readonly",
  setTimeout: "readonly",
  window: "readonly",
};

export default [
  {
    ignores: ["dist/**", "node_modules/**"],
  },
  {
    files: ["src/**/*.{js,jsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: browserGlobals,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "no-undef": "error",
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^[A-Z]" }],
      "react-hooks/set-state-in-effect": "off",
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
  },
];
