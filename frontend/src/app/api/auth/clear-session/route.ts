import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

/**
 * API route to forcefully clear all authentication sessions
 * This is useful for handling corrupted sessions or missing refresh tokens
 * 
 * POST /api/auth/clear-session
 */
export async function POST(request: NextRequest) {
  try {
    const cookieStore = cookies()
    
    // List of all possible auth-related cookies
    const authCookies = [
      'next-auth.session-token',
      '__Secure-next-auth.session-token',
      'next-auth.csrf-token',
      '__Secure-next-auth.csrf-token',
      'next-auth.callback-url',
      '__Secure-next-auth.callback-url',
      'refresh-token',
      '__Host-next-auth.csrf-token',
      'next-auth.session-token.sig',
      '__Secure-next-auth.session-token.sig',
    ]
    
    // Create response
    const response = NextResponse.json({ 
      success: true,
      message: 'All authentication sessions cleared'
    })
    
    // Clear each cookie
    authCookies.forEach(cookieName => {
      // Try to get the cookie to see if it exists
      const cookie = cookieStore.get(cookieName)
      
      if (cookie) {
        console.debug(`[Auth] Clearing cookie: ${cookieName}`)
      }
      
      // Set cookie with maxAge 0 to delete it
      response.cookies.set({
        name: cookieName,
        value: '',
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 0,
        path: '/',
      })
      
      // Also try with domain variants for complete cleanup
      if (process.env.NEXTAUTH_URL) {
        try {
          const url = new URL(process.env.NEXTAUTH_URL)
          response.cookies.set({
            name: cookieName,
            value: '',
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 0,
            path: '/',
            domain: url.hostname,
          })
          
          // Also try with subdomain wildcard
          if (url.hostname.includes('.')) {
            const parts = url.hostname.split('.')
            const rootDomain = `.${parts.slice(-2).join('.')}`
            response.cookies.set({
              name: cookieName,
              value: '',
              httpOnly: true,
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax',
              maxAge: 0,
              path: '/',
              domain: rootDomain,
            })
          }
        } catch (error) {
          console.error('[Auth] Error parsing NEXTAUTH_URL for cookie cleanup:', error)
        }
      }
    })
    
    // Add cache headers to prevent caching of this response
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
    
    console.info('[Auth] Session cleared successfully')
    
    return response
  } catch (error) {
    console.error('[Auth] Error clearing session:', error)
    return NextResponse.json(
      { 
        success: false,
        error: 'Failed to clear session',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

// Also support GET for easy browser testing (in development only)
export async function GET(request: NextRequest) {
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: 'Method not allowed' },
      { status: 405 }
    )
  }
  
  return POST(request)
}