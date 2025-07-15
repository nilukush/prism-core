import { NextRequest, NextResponse } from 'next/server'

// Singleton to prevent multiple simultaneous refreshes
let refreshPromise: Promise<any> | null = null
let lastRefreshTime = 0
const REFRESH_COOLDOWN = 2000 // 2 seconds between refreshes

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { refresh_token } = body
    
    if (!refresh_token) {
      return NextResponse.json(
        { error: 'Refresh token required' },
        { status: 400 }
      )
    }
    
    // Prevent rapid refresh attempts
    const now = Date.now()
    if (now - lastRefreshTime < REFRESH_COOLDOWN && refreshPromise) {
      console.log('[Refresh] Waiting for ongoing refresh...')
      try {
        const result = await refreshPromise
        return NextResponse.json(result)
      } catch (error) {
        // If the ongoing refresh failed, allow this request to proceed
        refreshPromise = null
      }
    }
    
    // Create new refresh promise
    refreshPromise = performRefresh(refresh_token)
    lastRefreshTime = now
    
    try {
      const result = await refreshPromise
      return NextResponse.json(result)
    } finally {
      // Keep the promise for a short time to handle concurrent requests
      setTimeout(() => {
        refreshPromise = null
      }, 100)
    }
    
  } catch (error) {
    console.error('[Refresh] Error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

async function performRefresh(refreshToken: string): Promise<any> {
  try {
    // Forward the refresh request to the backend
    // Use backend URL from environment variable
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
    const response = await fetch(`${backendUrl}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    })
    
    // Check if response has content before parsing
    const text = await response.text()
    let data: any = {}
    
    if (text) {
      try {
        data = JSON.parse(text)
      } catch (parseError) {
        console.error('[Refresh] Failed to parse response:', text)
        return {
          error: 'Invalid response format',
          status: response.status,
          rawResponse: text
        }
      }
    }
    
    if (!response.ok) {
      // Token is invalid or reused
      if (response.status === 401) {
        // Clear the token from our manager
        console.log('[Refresh] Invalid token, clearing session')
      }
      
      return {
        error: data.detail || 'Token refresh failed',
        status: response.status
      }
    }
    
    // Successful refresh
    console.log('[Refresh] Token refreshed successfully')
    
    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_in: data.expires_in,
      refresh_expires_in: data.refresh_expires_in
    }
    
  } catch (error) {
    console.error('[Refresh] Network error:', error)
    throw error
  }
}