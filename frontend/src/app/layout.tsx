import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { GeistMono } from 'geist/font/mono'

import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/sonner'
import { cn } from '@/lib/utils'

import '@/styles/globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
})

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3100'),
  title: {
    default: 'PRISM - AI-Powered Product Management Platform',
    template: '%s | PRISM',
  },
  description: 'Transform your product development with AI-powered user story generation, sprint planning, and intelligent analytics',
  keywords: [
    'Product Management',
    'AI',
    'User Stories',
    'Sprint Planning',
    'Agile',
    'Scrum',
    'Project Management',
    'Analytics',
    'Roadmap',
  ],
  authors: [
    {
      name: 'PRISM Team',
      url: 'https://github.com/prism',
    },
  ],
  creator: 'PRISM Team',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://prism.io',
    title: 'PRISM - AI-Powered Product Management Platform',
    description: 'Transform your product development with AI-powered user story generation, sprint planning, and intelligent analytics',
    siteName: 'PRISM',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'PRISM - AI-Powered Product Management Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PRISM - AI-Powered Product Management Platform',
    description: 'Transform your product development with AI-powered user story generation, sprint planning, and intelligent analytics',
    images: ['/og-image.png'],
    creator: '@prism_ai',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png' },
    ],
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          inter.variable,
          GeistMono.variable,
        )}
      >
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}