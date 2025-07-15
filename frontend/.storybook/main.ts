import type { StorybookConfig } from '@storybook/nextjs'
import path from 'path'

const config: StorybookConfig = {
  stories: [
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-onboarding',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
    '@storybook/addon-viewport',
    {
      name: '@storybook/addon-styling',
      options: {
        postCss: {
          implementation: require('postcss'),
        },
      },
    },
  ],
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  staticDirs: ['../public'],
  webpackFinal: async (config) => {
    // Add path aliases
    config.resolve = config.resolve || {}
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, '../src'),
      '@/components': path.resolve(__dirname, '../src/components'),
      '@/lib': path.resolve(__dirname, '../src/lib'),
      '@/hooks': path.resolve(__dirname, '../src/hooks'),
      '@/types': path.resolve(__dirname, '../src/types'),
      '@/utils': path.resolve(__dirname, '../src/utils'),
      '@/features': path.resolve(__dirname, '../src/features'),
      '@/store': path.resolve(__dirname, '../src/store'),
      '@/services': path.resolve(__dirname, '../src/services'),
      '@/styles': path.resolve(__dirname, '../src/styles'),
    }
    return config
  },
}

export default config