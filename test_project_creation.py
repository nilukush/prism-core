#!/usr/bin/env python3
"""
Test script to verify project creation endpoint.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test@example.com"  # Update with a valid test user email
PASSWORD = "password123"    # Update with the test user password

def login():
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": EMAIL,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        return data.get("access_token")
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def list_organizations(token):
    """List organizations to get an ID for project creation."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    
    if response.status_code == 200:
        orgs = response.json()
        print(f"\n✅ Found {len(orgs)} organizations:")
        for org in orgs:
            print(f"  - {org['name']} (ID: {org['id']})")
        return orgs[0]['id'] if orgs else None
    else:
        print(f"❌ Failed to list organizations: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_project(token, org_id):
    """Create a new project."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Generate unique project key
    timestamp = datetime.now().strftime("%H%M%S")
    project_key = f"TST{timestamp[-3:]}"
    
    project_data = {
        "name": f"Test Project {timestamp}",
        "key": project_key,
        "description": "Created via test script",
        "status": "planning",
        "organization_id": org_id
    }
    
    print(f"\n📝 Creating project with data:")
    print(json.dumps(project_data, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/projects",
        headers=headers,
        json=project_data
    )
    
    if response.status_code == 200:
        project = response.json()
        print(f"\n✅ Project created successfully!")
        print(f"  - ID: {project['id']}")
        print(f"  - Name: {project['name']}")
        print(f"  - Key: {project['key']}")
        return project['id']
    else:
        print(f"\n❌ Failed to create project: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def list_projects(token):
    """List all projects."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        projects = data.get('projects', [])
        print(f"\n✅ Found {len(projects)} projects:")
        for project in projects:
            print(f"  - {project['name']} (Key: {project['key']}, ID: {project['id']})")
    else:
        print(f"\n❌ Failed to list projects: {response.status_code}")
        print(f"Response: {response.text}")

def main():
    """Main test flow."""
    print("🚀 Testing PRISM Project Creation API")
    print("=" * 50)
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n⚠️  Cannot proceed without authentication")
        return
    
    # Step 2: Get organization ID
    org_id = list_organizations(token)
    if not org_id:
        print("\n⚠️  Cannot create project without organization")
        return
    
    # Step 3: Create project
    project_id = create_project(token, org_id)
    
    # Step 4: List projects to verify
    if project_id:
        list_projects(token)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()