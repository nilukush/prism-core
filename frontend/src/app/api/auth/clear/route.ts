import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET() {
  // Clear all auth-related cookies
  const cookiesList = cookies()
  
  // NextAuth session cookies
  const authCookies = [
    'next-auth.session-token',
    '__Secure-next-auth.session-token',
    'next-auth.csrf-token',
    '__Secure-next-auth.csrf-token',
    'next-auth.callback-url',
    '__Secure-next-auth.callback-url',
  ]
  
  authCookies.forEach(cookieName => {
    cookiesList.delete(cookieName)
  })
  
  return NextResponse.json({ 
    success: true, 
    message: 'Session cleared. Please login again.' 
  })
}