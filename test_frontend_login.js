#!/usr/bin/env node
/**
 * Test frontend login implementation
 * This script tests the login flow as implemented in the frontend
 */

const API_URL = 'http://localhost:8100';

async function testLogin() {
  console.log('Testing frontend login implementation...\n');
  
  // Test credentials
  const email = 'nilukush@gmail.com';
  const password = 'n1i6Lu!8';
  
  // Prepare form data (as OAuth2PasswordRequestForm expects)
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  formData.append('grant_type', 'password');
  
  console.log('Request details:');
  console.log('- URL:', `${API_URL}/api/v1/auth/login`);
  console.log('- Method: POST');
  console.log('- Content-Type: application/x-www-form-urlencoded');
  console.log('- Body:', formData.toString());
  console.log('-'.repeat(50));
  
  try {
    // Make the login request
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    console.log(`Status Code: ${response.status}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Login successful!');
      console.log(`\nAccess Token: ${data.access_token.substring(0, 50)}...`);
      console.log(`Token Type: ${data.token_type}`);
      console.log(`Expires In: ${data.expires_in} seconds`);
      console.log(`Refresh Token: ${data.refresh_token.substring(0, 50)}...`);
      
      // Now test the /me endpoint with the access token
      console.log('\n' + '-'.repeat(50));
      console.log('Testing /me endpoint with access token...\n');
      
      const meResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });
      
      if (meResponse.ok) {
        const userData = await meResponse.json();
        console.log('✅ User data retrieved successfully!');
        console.log(`User ID: ${userData.id}`);
        console.log(`Email: ${userData.email}`);
        console.log(`Username: ${userData.username || 'N/A'}`);
        console.log(`Full Name: ${userData.full_name || 'N/A'}`);
      } else {
        console.log('❌ Failed to retrieve user data');
        const errorText = await meResponse.text();
        console.log(`Error: ${errorText}`);
      }
    } else {
      console.log('❌ Login failed!');
      const errorText = await response.text();
      console.log(`Error: ${errorText}`);
    }
  } catch (error) {
    console.log('❌ Request failed!');
    console.log(`Error: ${error.message}`);
  }
}

// Run the test
testLogin();