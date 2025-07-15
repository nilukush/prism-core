import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function POST(request: NextRequest) {
  try {
    // Clear all auth-related cookies
    const cookieStore = cookies()
    const cookiesToClear = [
      'next-auth.session-token',
      '__Secure-next-auth.session-token',
      'next-auth.csrf-token', 
      '__Secure-next-auth.csrf-token',
      'next-auth.callback-url',
      '__Secure-next-auth.callback-url',
      '__Host-next-auth.csrf-token',
    ]

    // Create response
    const response = NextResponse.json({ success: true })

    // Clear each cookie
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

    console.log('[Logout] Session cleared successfully')
    
    return response
  } catch (error) {
    console.error('[Logout] Error clearing session:', error)
    return NextResponse.json(
      { error: 'Failed to clear session' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  // Support GET for easier testing
  return POST(request)
}