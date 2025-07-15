import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { getToken } from 'next-auth/jwt'

export async function GET(request: NextRequest) {
  try {
    // Check Authorization header
    const authHeader = request.headers.get('authorization')
    
    // Get JWT token
    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    })
    
    // Get session
    const session = await getServerSession(authOptions)
    
    // Test backend API with token
    let backendTest = null
    if (token?.accessToken) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/me`, {
          headers: {
            Authorization: `Bearer ${token.accessToken}`,
          },
        })
        if (response.ok) {
          backendTest = await response.json()
        } else {
          backendTest = { error: `Backend returned ${response.status}` }
        }
      } catch (error) {
        backendTest = { error: error instanceof Error ? error.message : 'Backend fetch failed' }
      }
    }
    
    return NextResponse.json({
      authHeader: authHeader ? 'Present' : 'Missing',
      token: {
        exists: !!token,
        sub: token?.sub,
        email: token?.email,
        hasAccessToken: !!token?.accessToken,
        hasRefreshToken: !!token?.refreshToken,
        error: token?.error,
      },
      session: {
        exists: !!session,
        user: session?.user,
        hasAccessToken: !!session?.accessToken,
        error: session?.error,
      },
      backendTest,
      env: {
        hasSecret: !!process.env.NEXTAUTH_SECRET,
        secretLength: process.env.NEXTAUTH_SECRET?.length,
        nextAuthUrl: process.env.NEXTAUTH_URL,
      },
    })
  } catch (error) {
    return NextResponse.json({
      error: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 })
  }
}