# User Activation Guide for PRISM

## Quick Start - Activate a User

### Method 1: Using the API (Recommended for Development)

```bash
# For development environment
curl -X POST "http://localhost:8000/api/v1/activation/activate/dev/user@example.com"

# Check activation status
curl "http://localhost:8000/api/v1/activation/status/user@example.com"
```

### Method 2: Using the CLI Script

```bash
# Activate a specific user
python scripts/activate_user.py --email user@example.com

# List all pending users
python scripts/activate_user.py --list-pending

# Activate all pending users (use with caution)
python scripts/activate_user.py --activate-all
```

### Method 3: Using the General Activation Endpoint

```bash
# Development mode - direct email activation
curl -X POST "http://localhost:8000/api/v1/activation/activate" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Admin override (requires ADMIN_ACTIVATION_KEY in environment)
curl -X POST "http://localhost:8000/api/v1/activation/activate" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "admin_key": "your-admin-key"}'
```

## Environment Configuration

Add these to your `.env` file:

```bash
# Development settings
ENVIRONMENT=development
AUTO_ACTIVATE_USERS=true          # Auto-activate on login
EMAIL_VERIFICATION_REQUIRED=false # Skip email verification
ALLOW_UNVERIFIED_LOGIN=true       # Allow pending users to login

# Admin activation key (for manual activation)
ADMIN_ACTIVATION_KEY=your-secret-admin-key

# Email verification secret (for token-based activation)
EMAIL_VERIFICATION_SECRET=your-email-verification-secret
```

## How It Works

### 1. **Development Mode**
- Users can be activated directly without email verification
- Pending users can login and are auto-activated if `AUTO_ACTIVATE_USERS=true`
- The `/activate/dev/{email}` endpoint is available

### 2. **Staging Mode**
- Similar to development but with optional restrictions
- Can require admin key for manual activation
- Useful for testing production-like scenarios

### 3. **Production Mode**
- Email verification is required
- Only token-based activation is allowed
- Dev endpoints are disabled
- Strict security checks are enforced

## API Endpoints

### 1. **POST /api/v1/activation/activate**
Main activation endpoint with multiple methods:
- **Token-based**: Use JWT token from email
- **Admin override**: Use admin key
- **Development mode**: Direct email activation

### 2. **POST /api/v1/activation/activate/dev/{email}**
Development-only quick activation endpoint

### 3. **GET /api/v1/activation/status/{email}**
Check user activation status (available in all environments)

## Troubleshooting

### User Can't Login After Registration

1. Check user status:
```bash
curl "http://localhost:8000/api/v1/activation/status/user@example.com"
```

2. If status is "pending", activate the user:
```bash
python scripts/activate_user.py --email user@example.com
```

3. Or enable auto-activation in `.env`:
```bash
AUTO_ACTIVATE_USERS=true
```

### Internal Server Error on Activation

1. Check if the old hardcoded endpoint is being used
2. Ensure the new activation router is properly imported
3. Check server logs for detailed error messages

### Email Verification Not Working

1. In development, set:
```bash
EMAIL_VERIFICATION_REQUIRED=false
AUTO_ACTIVATE_USERS=true
```

2. For production, ensure email service is configured properly

## Security Best Practices

1. **Never use development settings in production**
2. **Keep ADMIN_ACTIVATION_KEY secure and rotate regularly**
3. **Monitor activation logs for suspicious activity**
4. **Use token-based activation in production**
5. **Implement rate limiting on activation endpoints**

## Migration from Old System

If you have the old `temp_activate.py` endpoint:

1. Remove the old import from `router.py`
2. Import the new activation router
3. Update any scripts or tools using the old endpoint
4. Test thoroughly before deploying

## Example Workflows

### Development Workflow
1. User registers
2. User is automatically activated (if AUTO_ACTIVATE_USERS=true)
3. User can login immediately

### Production Workflow
1. User registers
2. Email with verification link is sent
3. User clicks link (contains JWT token)
4. Token is validated and user is activated
5. User can now login

### Admin Override Workflow
1. User reports activation issue
2. Admin verifies user identity
3. Admin uses activation endpoint with admin key
4. User is manually activated

This system provides flexibility for development while maintaining security in production environments.