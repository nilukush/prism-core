# 🚀 PRISM User Onboarding Guide

## Complete Flow: Registration → Organization → Project

### 📋 Prerequisites
- Backend deployed with latest code
- Environment variables set (CORS_ORIGINS, AUTO_ACTIVATE_USERS, etc.)

## 🔄 Step-by-Step User Journey

### 1️⃣ Register New Account
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePass123@",
    "confirm_password": "SecurePass123@"
  }'
```

### 2️⃣ Login (Auto-Activation Enabled)
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=newuser@example.com&password=SecurePass123@"
```

Save the `access_token` from response.

### 3️⃣ Create Your First Organization
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/organizations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "slug": "my-company",
    "description": "My awesome organization"
  }'
```

Save the organization `id` from response.

### 4️⃣ Create Your First Project
```bash
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/projects/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "key": "MFP",
    "description": "My first PRISM project",
    "organization_id": YOUR_ORG_ID
  }'
```

## 🌐 Web UI Flow

### After Login:
1. **No Organization?** You'll see an empty state
2. **Create Organization** button/form will appear
3. **Fill in**:
   - Organization Name
   - Slug (URL-friendly name)
   - Description (optional)

### After Creating Organization:
1. **Projects Page** becomes accessible
2. **Create Project** with:
   - Project Name
   - Project Key (3-4 letters)
   - Description
   - Select your organization

## 🔍 API Testing Script

Save this as `test-full-flow.sh`:

```bash
#!/bin/bash

# Configuration
API_URL="https://prism-backend-bwfx.onrender.com"
TIMESTAMP=$(date +%s)
TEST_USER="testuser$TIMESTAMP"
TEST_EMAIL="test$TIMESTAMP@example.com"
TEST_PASS="Test123456@"

echo "🚀 Testing PRISM Full User Flow"
echo "================================"

# 1. Register
echo -e "\n1️⃣  Registering user: $TEST_EMAIL"
REGISTER=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$TEST_USER\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASS\",
    \"confirm_password\": \"$TEST_PASS\"
  }")

if echo "$REGISTER" | grep -q "id"; then
  echo "✅ Registration successful"
else
  echo "❌ Registration failed: $REGISTER"
  exit 1
fi

# 2. Login
echo -e "\n2️⃣  Logging in..."
LOGIN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=$TEST_PASS")

TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ -n "$TOKEN" ]; then
  echo "✅ Login successful"
else
  echo "❌ Login failed: $LOGIN"
  exit 1
fi

# 3. Create Organization
echo -e "\n3️⃣  Creating organization..."
ORG=$(curl -s -X POST "$API_URL/api/v1/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Org $TIMESTAMP\",
    \"slug\": \"test-org-$TIMESTAMP\",
    \"description\": \"Test organization\"
  }")

ORG_ID=$(echo "$ORG" | grep -o '"id":[0-9]*' | cut -d':' -f2)
if [ -n "$ORG_ID" ]; then
  echo "✅ Organization created (ID: $ORG_ID)"
else
  echo "❌ Organization creation failed: $ORG"
  exit 1
fi

# 4. Create Project
echo -e "\n4️⃣  Creating project..."
PROJECT=$(curl -s -X POST "$API_URL/api/v1/projects/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Project\",
    \"key\": \"TP$TIMESTAMP\",
    \"description\": \"Test project\",
    \"organization_id\": $ORG_ID
  }")

if echo "$PROJECT" | grep -q "id"; then
  echo "✅ Project created successfully"
else
  echo "❌ Project creation failed: $PROJECT"
  exit 1
fi

echo -e "\n🎉 Full flow completed successfully!"
echo "User: $TEST_EMAIL"
echo "Organization ID: $ORG_ID"
```

## ❗ Common Issues & Solutions

### 1. CORS Error on Organization/Project Creation
**Solution**: Ensure `CORS_ORIGINS` includes your frontend URL in Render env vars

### 2. 403 Forbidden on Project Creation
**Cause**: No organization exists
**Solution**: Create organization first

### 3. 401 Unauthorized
**Cause**: JWT token expired or invalid
**Solution**: Re-login to get fresh token

### 4. Organization Slug Already Exists
**Solution**: Use unique slug (add timestamp or random string)

## 🎯 Frontend Integration

For frontend developers, here's the flow:

```javascript
// 1. After successful login
const checkUserOrganizations = async () => {
  const response = await api.get('/organizations/');
  if (response.data.total === 0) {
    // Show organization creation form
    showCreateOrgModal();
  }
};

// 2. Create organization
const createOrganization = async (orgData) => {
  const response = await api.post('/organizations/', {
    name: orgData.name,
    slug: orgData.slug.toLowerCase().replace(/\s+/g, '-'),
    description: orgData.description
  });
  return response.data;
};

// 3. Create project
const createProject = async (projectData, orgId) => {
  const response = await api.post('/projects/', {
    ...projectData,
    organization_id: orgId
  });
  return response.data;
};
```

## 📊 Database State After Onboarding

After completing the flow, the database will have:

1. **User** (status='active', email_verified=true)
2. **Organization** (owner_id=user.id)
3. **OrganizationMember** (user as 'admin' role)
4. **Project** (linked to organization)

## 🔐 Security Notes

- Organizations have limits (max_users, max_projects)
- Project keys must be unique within organization
- Users can only create projects in their organizations
- Auto-activation is temporary - implement email verification for production

---

**Last Updated**: 2025-01-18
**Next**: Deploy frontend changes to handle organization creation UI