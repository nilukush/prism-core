import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const { token, password, confirmPassword } = await request.json()

    // Validate input
    if (!token || !password) {
      return NextResponse.json(
        { error: 'Token and password are required' },
        { status: 400 }
      )
    }

    if (password !== confirmPassword) {
      return NextResponse.json(
        { error: 'Passwords do not match' },
        { status: 400 }
      )
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: 'Password must be at least 8 characters long' },
        { status: 400 }
      )
    }

    // Call backend API to reset password
    const response = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, password }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Failed to reset password' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({
      message: data.message || 'Password reset successfully',
    })
  } catch (error) {
    console.error('Password reset error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}