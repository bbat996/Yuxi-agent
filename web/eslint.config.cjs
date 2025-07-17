const vue = require('eslint-plugin-vue')
const js = require('@eslint/js')

module.exports = [
  js.configs.recommended,
  ...vue.configs['flat/vue3-essential'],
  {
    files: ['**/*.{js,mjs,cjs,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        navigator: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly'
      }
    },
    rules: {
      // Vue specific rules
      'vue/multi-word-component-names': 'off',
      'vue/no-unused-vars': 'error',
      'vue/no-v-model-argument': 'off'
    }
  },
  {
    ignores: [
      'dist/**', 
      'node_modules/**',
      'logs',
      '*.log',
      'npm-debug.log*',
      'yarn-debug.log*',
      'yarn-error.log*',
      'pnpm-debug.log*',
      'lerna-debug.log*',
      '.DS_Store',
      'dist-ssr',
      'coverage',
      '*.local',
      'cypress/videos/',
      'cypress/screenshots/',
      '.vscode/',
      '.idea/',
      '*.suo',
      '*.ntvs*',
      '*.njsproj',
      '*.sln',
      '*.sw?'
    ]
  }
] 