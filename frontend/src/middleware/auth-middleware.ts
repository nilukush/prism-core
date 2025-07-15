import { NextRequest, NextResponse } from 'next/server'
import { getToken } from 'next-auth/jwt'

/**
 * Auth middleware to validate sessions and handle expired tokens
 */
export async function authMiddleware(request: NextRequest) {
  // Skip auth checks for auth routes
  if (request.nextUrl.pathname.startsWith('/auth/') || 
      request.nextUrl.pathname.startsWith('/api/auth/')) {
    return NextResponse.next()
  }

  try {
    // Get the token from the request
    const token = await getToken({ 
      req: request,
      secret: process.env.NEXTAUTH_SECRET!,
    })

    // Check if token exists and is valid
    if (!token) {
      console.log('[Auth Middleware] No token found, redirecting to login')
      return redirectToLogin(request)
    }

    // Check for auth errors in the token
    if (token.error) {
      console.log('[Auth Middleware] Token has error:', token.error)
      
      // For certain errors, clear session and redirect
      if (token.error === 'RefreshTokenExpired' || 
          token.error === 'TokenFamilyInvalidated' ||
          token.error === 'RefreshAccessTokenError') {
        
        // Clear session cookies
        const response = redirectToLogin(request)
        clearAuthCookies(response)
        return response
      }
    }

    // Check if access token is about to expire (within 5 minutes)
    if (token.accessTokenExpires) {
      const expiresAt = token.accessTokenExpires as number
      const now = Date.now()
      const timeUntilExpiry = expiresAt - now
      
      if (timeUntilExpiry < 5 * 60 * 1000) { // 5 minutes
        console.log('[Auth Middleware] Access token expiring soon, will trigger refresh on next request')
        // Don't block the request, but add a header to indicate refresh is needed
        const response = NextResponse.next()
        response.headers.set('X-Token-Refresh-Needed', 'true')
        return response
      }
    }

    // Token is valid, continue
    return NextResponse.next()
  } catch (error) {
    console.error('[Auth Middleware] Error checking auth:', error)
    // On error, allow the request to continue but log it
    return NextResponse.next()
  }
}

/**
 * Redirect to login page with return URL
 */
function redirectToLogin(request: NextRequest): NextResponse {
  const url = request.nextUrl.clone()
  url.pathname = '/auth/login'
  
  // Preserve the original URL as a callback
  const callbackUrl = request.nextUrl.pathname + request.nextUrl.search
  if (callbackUrl && callbackUrl !== '/') {
    url.searchParams.set('callbackUrl', callbackUrl)
  }
  
  return NextResponse.redirect(url)
}

/**
 * Clear all auth-related cookies
 */
function clearAuthCookies(response: NextResponse): void {
  const cookiesToClear = [
    'next-auth.session-token',
    '__Secure-next-auth.session-token',
    'next-auth.csrf-token',
    '__Secure-next-auth.csrf-token',
    'next-auth.callback-url',
    '__Secure-next-auth.callback-url',
    'refresh-token',
    '__Host-next-auth.csrf-token',
  ]

  cookiesToClear.forEach(cookieName => {
    response.cookies.set({
      name: cookieName,
      value: '',
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/',
    })
  })
}

/**
 * Check if a path should be protected
 */
export function shouldProtectPath(pathname: string): boolean {
  // Public paths that don't require authentication
  const publicPaths = [
    '/',
    '/auth/login',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/auth/error',
    '/api/auth/signin',
    '/api/auth/signout',
    '/api/auth/session',
    '/api/auth/csrf',
    '/api/auth/providers',
    '/api/auth/callback',
    '/api/auth/refresh',
    '/api/auth/clear-session',
  ]

  // Check if path is public
  if (publicPaths.includes(pathname)) {
    return false
  }

  // Check if path starts with a public prefix
  const publicPrefixes = ['/auth/', '/api/auth/', '/_next/', '/static/']
  if (publicPrefixes.some(prefix => pathname.startsWith(prefix))) {
    return false
  }

  // All other paths are protected
  return true
}