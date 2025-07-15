#!/usr/bin/env python3
"""Test login for user nilukush@gmail.com"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8100/api/v1/auth/login"

# Test credentials
username = "nilukush@gmail.com"  # Using email as username
password = input("Enter password for nilukush@gmail.com: ")

# Login data
login_data = {
    "username": username,
    "password": password,
    "grant_type": "password"
}

print(f"\nTesting login for: {username}")
print("-" * 50)

try:
    # Make the login request
    response = requests.post(
        API_URL,
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        data = response.json()
        print(f"\nAccess Token: {data.get('access_token', '')[:50]}...")
        print(f"Token Type: {data.get('token_type', '')}")
        print(f"Expires In: {data.get('expires_in', '')} seconds")
        print(f"Refresh Token: {data.get('refresh_token', '')[:50]}...")
    else:
        print("❌ Login failed!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")