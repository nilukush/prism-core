import type { Preview } from '@storybook/react'
import React from 'react'
import { Inter } from 'next/font/google'
import '../src/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    nextjs: {
      appDirectory: true,
    },
    docs: {
      theme: {
        brandTitle: 'PRISM Components',
        brandUrl: 'https://prism.ai',
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#0a0a0a',
        },
        {
          name: 'gray',
          value: '#f3f4f6',
        },
      ],
    },
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
        tablet: {
          name: 'Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        desktop: {
          name: 'Desktop',
          styles: {
            width: '1920px',
            height: '1080px',
          },
        },
      },
    },
  },
  decorators: [
    (Story) => (
      <div className={inter.className}>
        <Story />
      </div>
    ),
  ],
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        icon: 'circlehollow',
        items: ['light', 'dark'],
        showName: true,
        dynamicTitle: true,
      },
    },
  },
}

export default preview