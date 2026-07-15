import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import ts from 'typescript-eslint'

export default ts.config(
  // app/core/static/** holds build output plus pre-existing hand-written/vendored JS
  // (HTMX/Alpine/Konva glue, vendor libs) that predates this TS/Vue toolchain and is
  // out of scope for it. .venv/** is the Python virtualenv, which vendors its own JS
  // (e.g. pywebview's polyfill) that this toolchain has no business linting.
  { ignores: ['app/core/static/**', 'node_modules/**', '.venv/**'] },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: { parserOptions: { parser: ts.parser } },
  },
  {
    rules: {
      // Islands are single-purpose; core/module component filenames are intentionally short.
      'vue/multi-word-component-names': 'off',
    },
  },
)
