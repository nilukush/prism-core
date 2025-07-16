import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getToken } from 'next-auth/jwt'

// Paths that require authentication
const protectedPaths = [
  '/dashboard',
  '/app',
  '/settings',
  '/workspaces',
  '/agents',
  '/projects',
  '/analytics',
  '/generate-prd',
  '/prd',
]

// Paths that should redirect to dashboard if authenticated
const authPaths = ['/auth/login', '/auth/register', '/auth/forgot-password']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Skip middleware for NextAuth API routes (except our custom ones)
  if (pathname.startsWith('/api/auth') && 
      !pathname.startsWith('/api/auth/refresh') &&
      !pathname.startsWith('/api/auth/logout') &&
      !pathname.startsWith('/api/auth/clear-session')) {
    return NextResponse.next()
  }

  // Check if the path requires authentication
  const isProtectedPath = protectedPaths.some((path) =>
    pathname.startsWith(path)
  )

  // Check if the path is an auth page
  const isAuthPath = authPaths.some((path) => pathname.startsWith(path))

  // Get the token to check authentication status
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET!,
  })

  // Check for auth errors in the token
  const hasError = token?.error && [
    'NoRefreshToken', 
    'RefreshTokenExpired', 
    'RefreshAccessTokenError',
    'TokenFamilyInvalidated',
    'RefreshError_401',
    'Token reuse detected'
  ].includes(token.error as string)
  
  const isUnrecoverableError = token?.error && [
    'RefreshTokenExpired',
    'TokenFamilyInvalidated',
    'Token reuse detected'
  ].includes(token.error as string)

  // Clear session for unrecoverable errors
  if (isUnrecoverableError) {
    console.log('[Middleware] Unrecoverable auth error detected:', token?.error)
    
    // If on a protected path, redirect to login with cleared session
    if (isProtectedPath) {
      const url = new URL('/auth/login', request.url)
      url.searchParams.set('callbackUrl', pathname)
      url.searchParams.set('error', 'session_expired')
      
      const response = NextResponse.redirect(url)
      
      // Clear all auth cookies
      clearAuthCookies(response)
      
      return response
    }
  }

  // Redirect logic for protected paths
  if (isProtectedPath && (!token || isUnrecoverableError)) {
    const url = new URL('/auth/login', request.url)
    url.searchParams.set('callbackUrl', pathname)
    
    // Add error info to help with user communication
    if (isUnrecoverableError) {
      url.searchParams.set('error', 'session_expired')
    } else if (!token) {
      url.searchParams.set('error', 'not_authenticated')
    }
    
    return NextResponse.redirect(url)
  }

  // For recoverable errors on protected paths, allow access but add warning header
  if (isProtectedPath && hasError && !isUnrecoverableError) {
    console.warn(`[Middleware] User accessing protected path with auth error: ${token?.error}`)
    const response = NextResponse.next()
    response.headers.set('X-Auth-Warning', token.error as string)
    return addSecurityHeaders(response)
  }

  // Redirect authenticated users away from auth pages
  // But allow access if they have an unrecoverable error (need to re-login)
  if (isAuthPath && token && !isUnrecoverableError && !hasError) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Check if access token needs refresh (within 5 minutes of expiry)
  if (token && token.accessTokenExpires) {
    const expiresAt = token.accessTokenExpires as number
    const now = Date.now()
    const timeUntilExpiry = expiresAt - now
    
    if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) { // 5 minutes
      console.log('[Middleware] Access token expiring soon, marking for refresh')
      const response = NextResponse.next()
      response.headers.set('X-Token-Refresh-Needed', 'true')
      return addSecurityHeaders(response)
    }
  }

  // Default: continue with security headers
  const response = NextResponse.next()
  return addSecurityHeaders(response)
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
 * Add security headers to response
 */
function addSecurityHeaders(response: NextResponse): NextResponse {
  // Security headers
  response.headers.set('X-DNS-Prefetch-Control', 'on')
  response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload')
  response.headers.set('X-Frame-Options', 'SAMEORIGIN')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin')
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), browsing-topics=()'
  )

  // Add CSP header for production
  if (process.env.NODE_ENV === 'production') {
    response.headers.set(
      'Content-Security-Policy',
      "default-src 'self'; " +
        "script-src 'self' 'unsafe-eval' 'unsafe-inline' *.vercel-scripts.com; " +
        "style-src 'self' 'unsafe-inline'; " +
        "img-src 'self' blob: data: https:; " +
        "font-src 'self' data:; " +
        "connect-src 'self' https://api.prism.ai wss://api.prism.ai; " +
        "frame-ancestors 'none'; " +
        "base-uri 'self'; " +
        "form-action 'self'"
    )
  }

  return response
}

// Configure which paths the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * Note: We removed 'api' from exclusions to allow middleware to run on some API routes
     * but we'll handle auth API routes specially in the middleware
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
}