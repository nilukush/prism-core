import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getToken } from 'next-auth/jwt'

export async function GET(request: NextRequest) {
  try {
    // Get session from NextAuth
    const session = await getServerSession(authOptions)
    
    // Get JWT token
    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    })
    
    // Get cookies
    const cookies = request.cookies.getAll()
    const authCookies = cookies.filter(c => c.name.includes('next-auth'))
    
    return NextResponse.json({
      session: session || null,
      token: token ? {
        sub: token.sub,
        email: token.email,
        error: token.error,
        hasAccessToken: !!token.accessToken,
        hasRefreshToken: !!token.refreshToken,
        tokenExpiry: token.accessTokenExpires,
      } : null,
      cookies: authCookies.map(c => ({
        name: c.name,
        hasValue: !!c.value,
        valueLength: c.value?.length || 0,
      })),
      env: {
        hasNextAuthSecret: !!process.env.NEXTAUTH_SECRET,
        nextAuthUrl: process.env.NEXTAUTH_URL,
        nodeEnv: process.env.NODE_ENV,
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    return NextResponse.json({
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    }, { status: 500 })
  }
}