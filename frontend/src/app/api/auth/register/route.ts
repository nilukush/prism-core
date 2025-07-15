import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8100'

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
    }

    console.log('Registering user:', { email: registrationData.email, username: registrationData.username })

    // Forward request to backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(registrationData),
    })

    const data = await backendResponse.json()

    // Handle backend errors
    if (!backendResponse.ok) {
      console.error('Backend registration failed:', data)
      return NextResponse.json(
        { 
          error: data.detail || 'Registration failed',
          message: data.detail || 'Failed to create account',
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