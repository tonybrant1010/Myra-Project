
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  { files: ['scripts/**/*.js', '*.config.js'], languageOptions: { globals: { __dirname: 'readonly', require: 'readonly', module: 'readonly', process: 'readonly', Buffer: 'readonly' } } },
  {
    ignores: ['dist/*'],
  },
]);
