import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()

    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      )
    }

    // Call backend API to initiate password reset
    const response = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Failed to initiate password reset' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({
      message: data.message || 'Password reset instructions sent to your email',
    })
  } catch (error) {
    console.error('Password reset error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}