import { NextRequest, NextResponse } from 'next/server'

/**
 * Force logout by clearing all authentication state
 * This is more aggressive than the regular logout
 */
export async function POST(_request: NextRequest) {
  try {
    // Create response
    const response = NextResponse.json({ 
      success: true,
      message: 'Forced logout completed'
    })
    
    // List of ALL possible auth-related cookies
    const authCookies = [
      'next-auth.session-token',
      '__Secure-next-auth.session-token',
      '__Host-next-auth.session-token',
      'next-auth.csrf-token',
      '__Secure-next-auth.csrf-token',
      '__Host-next-auth.csrf-token',
      'next-auth.callback-url',
      '__Secure-next-auth.callback-url',
      'refresh-token',
      'next-auth.session-token.sig',
      '__Secure-next-auth.session-token.sig',
    ]
    
    // Clear each cookie with multiple attempts
    authCookies.forEach(cookieName => {
      // Multiple clearing attempts with different configurations
      const configs = [
        { name: cookieName, value: '', maxAge: 0, path: '/' },
        { name: cookieName, value: '', maxAge: 0, path: '/', httpOnly: true },
        { name: cookieName, value: '', maxAge: 0, path: '/', secure: true },
        { name: cookieName, value: '', maxAge: 0, path: '/', sameSite: 'lax' as const },
        { name: cookieName, value: '', maxAge: 0, path: '/', sameSite: 'strict' as const },
        { name: cookieName, value: '', maxAge: 0, path: '/', sameSite: 'none' as const, secure: true },
      ]
      
      configs.forEach(config => {
        try {
          response.cookies.set(config)
        } catch (e) {
          // Ignore errors for incompatible configurations
        }
      })
    })
    
    // Also try to clear with domain variations
    if (process.env.NEXTAUTH_URL) {
      try {
        const url = new URL(process.env.NEXTAUTH_URL)
        const domains = [
          url.hostname,
          'localhost',
          '.localhost',
          '',
        ]
        
        domains.forEach(domain => {
          authCookies.forEach(cookieName => {
            try {
              response.cookies.set({
                name: cookieName,
                value: '',
                maxAge: 0,
                path: '/',
                domain: domain || undefined,
              })
            } catch (e) {
              // Ignore domain errors
            }
          })
        })
      } catch (error) {
        console.error('[Auth] Error parsing NEXTAUTH_URL:', error)
      }
    }
    
    // Set aggressive cache headers
    response.headers.set('Cache-Control', 'no-store, no-cache, max-age=0, must-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
    response.headers.set('Clear-Site-Data', '"cookies", "storage"')
    
    console.info('[Auth] Forced logout completed')
    
    return response
  } catch (error) {
    console.error('[Auth] Force logout error:', error)
    return NextResponse.json(
      { 
        success: false,
        error: 'Failed to force logout',
      },
      { status: 500 }
    )
  }
}