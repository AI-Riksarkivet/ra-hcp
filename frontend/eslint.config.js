import js from '@eslint/js';
import ts from 'typescript-eslint';
import svelte from 'eslint-plugin-svelte';
import prettier from 'eslint-config-prettier';
import globals from 'globals';
import svelteConfig from './svelte.config.js';

// Flat config (ESLint 10). Non-type-checked recommended sets — fast, no tsconfig
// project service needed; `svelte-check` + `tsc` remain the type gate. The
// prettier config is last so it disables all formatting-related lint rules
// (prettier owns formatting).
export default ts.config(
	{ ignores: ['build/', '.svelte-kit/', 'dist/', 'node_modules/', 'storybook-static/'] },
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	prettier,
	...svelte.configs.prettier,
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node },
		},
	},
	{
		files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
		languageOptions: {
			parserOptions: {
				parser: ts.parser,
				extraFileExtensions: ['.svelte'],
				svelteConfig,
			},
		},
	},
	{
		rules: {
			// No base path in this app — plain `href` / `goto()` are correct.
			'svelte/no-navigation-without-resolve': 'off',
			// TypeScript already reports undefined identifiers; `no-undef` only adds
			// false positives on global *types*. Standard for TS projects.
			'no-undef': 'off',
			// Empty `catch {}` blocks are intentional best-effort guards.
			'no-empty': ['error', { allowEmptyCatch: true }],
			// Allow intentional `_`-prefixed unused vars/args/caught errors.
			'@typescript-eslint/no-unused-vars': [
				'error',
				{
					argsIgnorePattern: '^_',
					varsIgnorePattern: '^_',
					caughtErrorsIgnorePattern: '^_',
				},
			],
			// Storybook/table generics legitimately need `any` in a few spots.
			'@typescript-eslint/no-explicit-any': 'warn',
			// `{@html}` is used only for self-generated search-highlight markup.
			'svelte/no-at-html-tags': 'warn',
			// `let x = 0` then branch-assign is a fine pattern — flag, don't block.
			'no-useless-assignment': 'warn',
			// Plain Date/Set/Map are only reactive via SvelteDate/Set/Map — flag, don't block.
			'svelte/prefer-svelte-reactivity': 'warn',
		},
	},
);
