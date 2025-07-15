'use client'

import { useEffect, useCallback } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { 
  hasAuthError, 
  getAuthError, 
  handleAuthError,
  clearSessionAndRedirect,
  AuthErrorType 
} from '@/lib/auth-utils'

interface UseAuthErrorHandlerOptions {
  /**
   * Called when an auth error is detected
   */
  onError?: (error: AuthErrorType) => void
  
  /**
   * Whether to automatically handle errors (default: true)
   */
  autoHandle?: boolean
  
  /**
   * Whether to show user-facing notifications (default: true)
   */
  showNotifications?: boolean
  
  /**
   * Custom redirect URL for unrecoverable errors
   */
  redirectUrl?: string
}

/**
 * Custom hook for handling authentication errors
 * Monitors the session for auth errors and handles them appropriately
 */
export function useAuthErrorHandler(options: UseAuthErrorHandlerOptions = {}) {
  const { data: session, status } = useSession()
  const router = useRouter()
  
  const {
    onError,
    autoHandle = true,
    showNotifications = true,
    redirectUrl = '/auth/login'
  } = options
  
  const handleError = useCallback(async (error: AuthErrorType) => {
    console.debug('[Auth] Handling error in hook:', error)
    
    // Call custom handler if provided
    if (onError) {
      onError(error)
    }
    
    // Show user notification if enabled
    if (showNotifications) {
      switch (error) {
        case AuthErrorType.RefreshTokenExpired:
          // You can integrate with your toast/notification system here
          console.info('Your session has expired. Please sign in again.')
          break
        case AuthErrorType.NoRefreshToken:
          console.info('Session refresh not available. You may need to sign in again soon.')
          break
        case AuthErrorType.RefreshAccessTokenError:
          console.warn('There was an issue refreshing your session. Please try again.')
          break
      }
    }
    
    // Auto-handle the error if enabled
    if (autoHandle) {
      const handled = await handleAuthError(error, {
        silent: !showNotifications,
        autoRedirect: true,
        onError
      })
      
      if (!handled) {
        // If error wasn't handled, clear session as fallback
        await clearSessionAndRedirect(redirectUrl)
      }
    }
  }, [onError, showNotifications, autoHandle, redirectUrl])
  
  // Monitor session for errors
  useEffect(() => {
    if (status === 'loading') return
    
    if (hasAuthError(session)) {
      const error = getAuthError(session)
      if (error) {
        handleError(error)
      }
    }
  }, [session, status, handleError])
  
  // Return utility functions for manual error handling
  return {
    /**
     * Manually check if session has an error
     */
    hasError: hasAuthError(session),
    
    /**
     * Get the current error type if any
     */
    error: getAuthError(session),
    
    /**
     * Manually trigger error handling
     */
    handleError,
    
    /**
     * Force clear session and redirect
     */
    clearSession: async () => {
      await clearSessionAndRedirect(redirectUrl)
    },
    
    /**
     * Call the clear-session API endpoint
     */
    forceClearSession: async () => {
      try {
        await fetch('/api/auth/clear-session', { method: 'POST' })
        router.push(redirectUrl)
      } catch (error) {
        console.error('[Auth] Failed to clear session via API:', error)
        // Fallback to client-side clear
        await clearSessionAndRedirect(redirectUrl)
      }
    }
  }
}