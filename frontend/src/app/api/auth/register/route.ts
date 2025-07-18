import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env['NEXT_PUBLIC_API_URL'] || process.env['BACKEND_URL'] || 'http://localhost:8100'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Extract email username from email (enterprise pattern)
    const username = body.email.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '')
    
    // Prepare registration data with all required fields
    const registrationData = {
      email: body.email,
      username: username,
      password: body.password,
      full_name: body.full_name || body.fullName,
      organization_name: body.organizationName || body.organization_name,
    }

    console.log('Registering user:', { 
      email: registrationData.email, 
      username: registrationData.username,
      backend_url: BACKEND_URL,
      full_url: `${BACKEND_URL}/api/v1/auth/register`
    })

    // Forward request to backend with timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout
    
    let backendResponse
    try {
      backendResponse = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationData),
        signal: controller.signal,
      })
    } catch (fetchError) {
      console.error('Fetch error:', fetchError)
      if (fetchError instanceof Error && fetchError.name === 'AbortError') {
        return NextResponse.json(
          { 
            error: 'Request timeout',
            message: 'The server took too long to respond. Please try again.',
          },
          { status: 408 }
        )
      }
      return NextResponse.json(
        { 
          error: 'Network error',
          message: 'Could not connect to the server. Please check your connection and try again.',
          details: fetchError instanceof Error ? fetchError.message : 'Unknown error'
        },
        { status: 503 }
      )
    } finally {
      clearTimeout(timeoutId)
    }

    let data
    try {
      data = await backendResponse.json()
    } catch (jsonError) {
      console.error('Failed to parse backend response:', jsonError)
      data = { detail: 'Invalid response from server' }
    }

    // Handle backend errors
    if (!backendResponse.ok) {
      console.error('Backend registration failed:', {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        data: data,
        url: `${BACKEND_URL}/api/v1/auth/register`
      })
      return NextResponse.json(
        { 
          error: data.detail || data.message || 'Registration failed',
          message: data.detail || data.message || 'Failed to create account',
          details: data
        },
        { status: backendResponse.status }
      )
    }

    // Success response
    return NextResponse.json({
      message: 'Account created successfully',
      user: data,
    }, { status: 201 })

  } catch (error) {
    console.error('Registration error:', error)
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'Something went wrong. Please try again.',
      },
      { status: 500 }
    )
  }
}