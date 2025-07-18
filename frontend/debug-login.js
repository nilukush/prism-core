// Debug script to test login functionality
// Run this in the browser console on the login page

async function debugLogin() {
  console.log('=== Starting Login Debug ===');
  
  // Test 1: Check if the backend is reachable
  console.log('\n1. Testing backend connectivity...');
  try {
    const healthResponse = await fetch('http://localhost:8100/api/v1/health');
    console.log('Backend health check:', {
      status: healthResponse.status,
      ok: healthResponse.ok,
      data: await healthResponse.json()
    });
  } catch (error) {
    console.error('Backend unreachable:', error);
  }
  
  // Test 2: Direct login API call
  console.log('\n2. Testing direct login API call...');
  const formData = new URLSearchParams();
  formData.append('username', 'nilukush@gmail.com');
  formData.append('password', 'testpassword123');  // Replace with your actual password
  formData.append('grant_type', 'password');
  
  try {
    const loginResponse = await fetch('http://localhost:8100/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    console.log('Direct login response:', {
      status: loginResponse.status,
      ok: loginResponse.ok,
      headers: Object.fromEntries(loginResponse.headers.entries())
    });
    
    const loginData = await loginResponse.json();
    console.log('Login data:', loginData);
    
    if (loginData.access_token) {
      // Test 3: Verify token with /me endpoint
      console.log('\n3. Testing /me endpoint with token...');
      const meResponse = await fetch('http://localhost:8100/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${loginData.access_token}`
        }
      });
      
      console.log('Me endpoint response:', {
        status: meResponse.status,
        ok: meResponse.ok,
        data: await meResponse.json()
      });
    }
  } catch (error) {
    console.error('Login API error:', error);
  }
  
  // Test 4: Check NextAuth session endpoint
  console.log('\n4. Testing NextAuth session endpoint...');
  try {
    const sessionResponse = await fetch('/api/auth/session');
    console.log('NextAuth session:', {
      status: sessionResponse.status,
      ok: sessionResponse.ok,
      data: await sessionResponse.json()
    });
  } catch (error) {
    console.error('Session check error:', error);
  }
  
  // Test 5: Check NextAuth CSRF token
  console.log('\n5. Testing NextAuth CSRF token...');
  try {
    const csrfResponse = await fetch('/api/auth/csrf');
    console.log('CSRF token:', {
      status: csrfResponse.status,
      ok: csrfResponse.ok,
      data: await csrfResponse.json()
    });
  } catch (error) {
    console.error('CSRF token error:', error);
  }
  
  console.log('\n=== Debug Complete ===');
  console.log('Instructions:');
  console.log('1. Replace "testpassword123" with your actual password');
  console.log('2. Run debugLogin() in the browser console');
  console.log('3. Check the console output for any errors');
  console.log('4. Share the output to diagnose the issue');
}

// Instructions to run:
console.log('Debug script loaded. Run debugLogin() to start debugging.');
console.log('Make sure to update the password in the script first!');