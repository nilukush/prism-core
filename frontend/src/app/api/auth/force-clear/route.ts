import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function POST(_request: NextRequest) {
  console.log('[Force Clear] Clearing all auth data')
  
  // Get cookie store
  const cookieStore = cookies()
  
  // List of auth cookies to clear
  const authCookies = [
    'next-auth.session-token',
    'next-auth.csrf-token',
    'next-auth.callback-url',
    '__Secure-next-auth.session-token',
    '__Secure-next-auth.csrf-token',
    '__Secure-next-auth.callback-url',
    '__Host-next-auth.session-token',
    '__Host-next-auth.csrf-token',
    '__Host-next-auth.callback-url'
  ]
  
  // Clear each cookie
  authCookies.forEach(name => {
    try {
      cookieStore.delete(name)
      cookieStore.delete({
        name,
        path: '/',
      })
    } catch (e) {
      // Cookie might not exist, that's ok
    }
  })
  
  // Return response with cookie clearing headers
  const response = NextResponse.json({ success: true, message: 'Auth data cleared' })
  
  // Set cookies to expire in the response
  authCookies.forEach(name => {
    response.cookies.set(name, '', {
      expires: new Date(0),
      path: '/',
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    })
  })
  
  return response
}

export async function GET(_request: NextRequest) {
  // For browser-based clearing
  return POST(_request)
}