import { NextRequest, NextResponse } from 'next/server'
import { getApiUrl } from '@/lib/url-utils'

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()
    
    if (!email || !password) {
      return NextResponse.json({
        error: 'Email and password are required',
        status: 'error'
      }, { status: 400 })
    }

    const results: any = {
      timestamp: new Date().toISOString(),
      environment: {
        apiUrl: getApiUrl(),
        nodeEnv: process.env.NODE_ENV,
        nextAuthUrl: process.env.NEXTAUTH_URL,
        hasNextAuthSecret: !!process.env.NEXTAUTH_SECRET
      },
      tests: {}
    }

    // Test 1: Direct backend authentication
    console.log('Testing direct backend auth...')
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      formData.append('grant_type', 'password')

      const backendResponse = await fetch(`${getApiUrl()}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      })

      const responseText = await backendResponse.text()
      let responseData: any = {}
      
      if (responseText) {
        try {
          responseData = JSON.parse(responseText)
        } catch (e) {
          responseData = { rawResponse: responseText }
        }
      }

      results.tests.backendAuth = {
        success: backendResponse.ok,
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: Object.fromEntries(backendResponse.headers.entries()),
        data: responseData,
        formDataSent: {
          username: email,
          password: '***hidden***',
          grant_type: 'password'
        }
      }

      // Test 2: If backend auth succeeded, test /me endpoint
      if (backendResponse.ok && responseData.access_token) {
        console.log('Testing /me endpoint with token...')
        const meResponse = await fetch(`${getApiUrl()}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${responseData.access_token}`,
          },
        })

        const meData = await meResponse.json()
        results.tests.meEndpoint = {
          success: meResponse.ok,
          status: meResponse.status,
          data: meData
        }
      }
    } catch (error) {
      results.tests.backendAuth = {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        type: 'network_error'
      }
    }

    // Test 3: Test the API client auth.login method
    console.log('Testing API client auth.login...')
    try {
      const { api } = await import('@/lib/api-client')
      const apiResponse = await api.auth.login({ email, password })
      
      results.tests.apiClient = {
        success: true,
        hasAccessToken: !!apiResponse.access_token,
        hasRefreshToken: !!apiResponse.refresh_token,
        tokenType: apiResponse.token_type,
        expiresIn: apiResponse.expires_in
      }
    } catch (error: any) {
      results.tests.apiClient = {
        success: false,
        error: error.message,
        status: error.status,
        data: error.data
      }
    }

    // Test 4: Test NextAuth provider
    console.log('Testing NextAuth provider...')
    try {
      const { authOptions } = await import('@/lib/auth')
      const credentialsProvider = authOptions.providers.find(
        (p: any) => p.type === 'credentials'
      )
      
      if (credentialsProvider && credentialsProvider.authorize) {
        const user = await credentialsProvider.authorize({
          email,
          password
        })
        
        results.tests.nextAuthProvider = {
          success: !!user,
          hasUser: !!user,
          userData: user ? {
            id: user.id,
            email: user.email,
            name: user.name,
            hasAccessToken: !!user.accessToken,
            hasRefreshToken: !!user.refreshToken
          } : null
        }
      }
    } catch (error: any) {
      results.tests.nextAuthProvider = {
        success: false,
        error: error.message
      }
    }

    // Generate recommendations
    results.recommendations = []
    
    if (!results.tests.backendAuth?.success) {
      if (results.tests.backendAuth?.status === 401) {
        results.recommendations.push(
          'Backend returned 401. Check if user exists and password is correct.',
          'Verify password hashing matches between registration and login.',
          'Check backend logs for detailed error messages.'
        )
      } else if (results.tests.backendAuth?.type === 'network_error') {
        results.recommendations.push(
          'Cannot connect to backend. Check if backend is running.',
          `Verify backend URL is correct: ${getApiUrl()}`,
          'Check Docker containers: docker compose ps'
        )
      }
    } else if (!results.tests.nextAuthProvider?.success) {
      results.recommendations.push(
        'Backend auth works but NextAuth provider fails.',
        'Check if /api/v1/auth/me endpoint returns user data.',
        'Verify NextAuth configuration in auth.ts'
      )
    }

    // Overall status
    results.overallStatus = results.tests.backendAuth?.success && 
                           results.tests.nextAuthProvider?.success ? 
                           'success' : 'failure'

    return NextResponse.json(results)
  } catch (error) {
    return NextResponse.json({
      error: 'Debug endpoint error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}