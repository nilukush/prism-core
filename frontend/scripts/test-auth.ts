#!/usr/bin/env node

/**
 * Enterprise-grade authentication testing script
 * Tests the OAuth2 password flow authentication end-to-end
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8100'
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3100'

// Test credentials - replace with your test user
const TEST_EMAIL = 'test@example.com'
const TEST_PASSWORD = 'testpassword123'

console.log('🔍 Authentication Debug Test Script')
console.log('===================================')
console.log(`API URL: ${API_URL}`)
console.log(`APP URL: ${APP_URL}`)
console.log('')

async function testBackendAuth() {
  console.log('1️⃣  Testing Backend Authentication...')
  
  try {
    // Test OAuth2 password flow
    const formData = new URLSearchParams()
    formData.append('username', TEST_EMAIL)
    formData.append('password', TEST_PASSWORD)
    formData.append('grant_type', 'password')

    console.log('   Request:', {
      url: `${API_URL}/api/v1/auth/login`,
      method: 'POST',
      contentType: 'application/x-www-form-urlencoded',
      body: formData.toString()
    })

    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    })

    const responseText = await response.text()
    console.log('   Response Status:', response.status)
    console.log('   Response Headers:', Object.fromEntries(response.headers.entries()))

    if (response.ok) {
      const data = JSON.parse(responseText)
      console.log('   ✅ Authentication successful!')
      console.log('   Response:', {
        access_token: data.access_token ? `${data.access_token.substring(0, 20)}...` : 'Missing',
        refresh_token: data.refresh_token ? 'Present' : 'Missing',
        token_type: data.token_type,
        expires_in: data.expires_in,
      })
      return data
    } else {
      console.log('   ❌ Authentication failed!')
      console.log('   Response:', responseText)
      return null
    }
  } catch (error) {
    console.log('   ❌ Error:', error)
    return null
  }
}

async function testUserInfo(accessToken: string) {
  console.log('\n2️⃣  Testing User Info Endpoint...')
  
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    })

    const data = await response.json()
    console.log('   Response Status:', response.status)
    
    if (response.ok) {
      console.log('   ✅ User info retrieved successfully!')
      console.log('   User:', {
        id: data.id,
        email: data.email,
        username: data.username,
        full_name: data.full_name,
      })
      return data
    } else {
      console.log('   ❌ Failed to get user info!')
      console.log('   Response:', data)
      return null
    }
  } catch (error) {
    console.log('   ❌ Error:', error)
    return null
  }
}

async function testNextAuthDebug() {
  console.log('\n3️⃣  Testing NextAuth Debug Endpoint...')
  
  try {
    const response = await fetch(`${APP_URL}/api/debug-auth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: TEST_EMAIL,
        password: TEST_PASSWORD,
      }),
    })

    const data = await response.json()
    console.log('   Response Status:', response.status)
    
    if (response.ok) {
      console.log('   ✅ Debug info retrieved!')
      console.log('   Summary:', data.summary)
      console.log('   Tests:')
      data.tests.forEach((test: any) => {
        const icon = test.status === 'success' ? '✅' : '❌'
        console.log(`     ${icon} ${test.name}: ${test.status}`)
        if (test.error) {
          console.log(`        Error: ${test.error}`)
        }
      })
      
      if (data.summary.recommendations.length > 0) {
        console.log('\n   📋 Recommendations:')
        data.summary.recommendations.forEach((rec: string) => {
          console.log(`     • ${rec}`)
        })
      }
    } else {
      console.log('   ❌ Debug endpoint failed!')
      console.log('   Response:', data)
    }
  } catch (error) {
    console.log('   ❌ Error:', error)
  }
}

async function testNextAuthSignIn() {
  console.log('\n4️⃣  Testing NextAuth SignIn...')
  
  try {
    // Get CSRF token first
    const csrfResponse = await fetch(`${APP_URL}/api/auth/csrf`)
    const { csrfToken } = await csrfResponse.json()
    console.log('   CSRF Token:', csrfToken ? 'Retrieved' : 'Missing')

    // Attempt sign in
    const formData = new URLSearchParams()
    formData.append('email', TEST_EMAIL)
    formData.append('password', TEST_PASSWORD)
    formData.append('csrfToken', csrfToken)

    const response = await fetch(`${APP_URL}/api/auth/callback/credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
      redirect: 'manual',
    })

    console.log('   Response Status:', response.status)
    console.log('   Location:', response.headers.get('location'))
    
    if (response.status === 302 || response.status === 307) {
      console.log('   ✅ SignIn redirect received!')
    } else {
      console.log('   ❌ Unexpected response status!')
      const text = await response.text()
      console.log('   Response:', text.substring(0, 200))
    }
  } catch (error) {
    console.log('   ❌ Error:', error)
  }
}

// Run all tests
async function runTests() {
  console.log('Starting authentication tests...\n')
  
  // Test 1: Backend auth
  const authData = await testBackendAuth()
  
  // Test 2: User info (if auth succeeded)
  if (authData?.access_token) {
    await testUserInfo(authData.access_token)
  }
  
  // Test 3: NextAuth debug
  await testNextAuthDebug()
  
  // Test 4: NextAuth sign in
  await testNextAuthSignIn()
  
  console.log('\n✅ All tests completed!')
  console.log('\nTroubleshooting tips:')
  console.log('1. Ensure backend is running and accessible')
  console.log('2. Check NEXTAUTH_SECRET is set in .env.local')
  console.log('3. Verify NEXT_PUBLIC_API_URL points to correct backend')
  console.log('4. Check backend logs for any authentication errors')
  console.log('5. Ensure passwords are handled consistently (encoding)')
}

// Execute tests
runTests().catch(console.error)