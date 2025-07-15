'use client'

import { useSession } from 'next-auth/react'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from '@/components/ui/use-toast'
import { authBroadcast, forceClearAuthData, validateSession } from '@/lib/auth-utils'

export function AuthErrorBoundary({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === 'loading') return

    // Check for auth errors
    if (session?.error) {
      console.warn('[AuthErrorBoundary] Session error detected:', session.error)
      
      switch (session.error) {
        case 'RefreshTokenExpired':
        case 'NoRefreshToken':
          // Clear session and redirect to login
          toast({
            title: 'Session Expired',
            description: 'Please sign in again to continue.',
            variant: 'destructive',
          })
          
          // Broadcast to other tabs
          authBroadcast?.broadcast('session-error', { error: session.error })
          
          // Force clear and redirect
          setTimeout(async () => {
            await forceClearAuthData()
            router.push('/auth/login?error=session_expired')
          }, 1000)
          break
          
        case 'NetworkError':
          // Network error - show message but don't logout
          toast({
            title: 'Connection Error',
            description: 'Unable to connect to server. Please check your internet connection.',
            variant: 'destructive',
          })
          break
          
        case 'EmptyResponse':
        case 'InvalidResponse':
          // Server issues - try to recover
          console.log('[AuthErrorBoundary] Server response issue, attempting recovery')
          validateSession().then(isValid => {
            if (!isValid) {
              toast({
                title: 'Server Error',
                description: 'Unable to verify your session. Please try again.',
                variant: 'destructive',
              })
            }
          })
          break
          
        default:
          // Unknown error - log it
          console.error('[AuthErrorBoundary] Unknown session error:', session.error)
      }
    }
  }, [session, status, router])

  return <>{children}</>
}