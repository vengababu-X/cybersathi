import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  // Build output and vendored assets are not ours to lint.
  { ignores: ['dist/**', 'node_modules/**', 'public/fonts/**', 'scripts/**'] },

  js.configs.recommended,
  ...tseslint.configs.recommended,

  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Vite's fast refresh only works when a module exports components alone. The
      // contexts deliberately export a provider and a hook together, so this is a
      // reminder rather than an error.
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // An underscore prefix is the agreed marker for "intentionally unused".
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },

  {
    files: ['**/*.test.{ts,tsx}', 'src/test/**/*.{ts,tsx}'],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },

  {
    // The service worker runs in a worker scope, not a window.
    files: ['public/sw.js'],
    languageOptions: { globals: { ...globals.serviceworker } },
  },

  {
    files: ['vite.config.ts', '*.config.{js,ts}'],
    languageOptions: { globals: { ...globals.node } },
  },
)
