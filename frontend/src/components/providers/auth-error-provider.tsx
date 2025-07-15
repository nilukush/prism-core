'use client'

import { useAuthErrorHandler } from '@/hooks/use-auth-error-handler'
import { AuthErrorType } from '@/lib/auth-utils'
import { ReactNode } from 'react'

interface AuthErrorProviderProps {
  children: ReactNode
}

/**
 * Provider component that monitors and handles authentication errors
 * This should be placed in your root layout after SessionProvider
 */
export function AuthErrorProvider({ children }: AuthErrorProviderProps) {
  // Monitor auth errors and handle them automatically
  useAuthErrorHandler({
    autoHandle: true,
    showNotifications: true,
    onError: (error: AuthErrorType) => {
      // Log to monitoring service in production
      if (process.env.NODE_ENV === 'production') {
        // Example: Send to your monitoring service
        console.error('[AuthErrorProvider] Authentication error detected:', {
          error,
          timestamp: new Date().toISOString(),
          // Add any additional context like user ID if available
        })
      }
    }
  })
  
  return <>{children}</>
}