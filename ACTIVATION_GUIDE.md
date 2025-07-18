# PRISM User Activation Guide

## Overview

This guide explains how to activate user accounts in PRISM when email verification is not available or configured. This is particularly useful for:
- Development and testing environments
- Production deployments without email service
- Emergency activation when email service is down
- Batch activation of multiple users

## Production Deployment Status

PRISM is currently deployed on:
- **Frontend**: Vercel (https://prism-frontend-kappa.vercel.app)
- **Backend**: Render (https://prism-backend-bwfx.onrender.com)
- **Database**: Neon PostgreSQL
- **Cache**: Upstash Redis

## Activation Methods

### Method 1: Simple Activation Endpoint (Development/Staging)

For non-production environments, use the simple activation endpoint:

```bash
# Activate a user by email
curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/activation/activate/user@example.com
```

### Method 2: Secure Activation (Production)

For production, you need to provide either an activation token or admin key:

```bash
# With admin key
curl -X POST "https://prism-backend-bwfx.onrender.com/api/v1/activation/activate?email=user@example.com" \
  -H "X-Admin-Key: your-admin-key"

# With activation token
curl -X POST "https://prism-backend-bwfx.onrender.com/api/v1/activation/activate?email=user@example.com&token=activation-token"
```

### Method 3: Generate Activation Link (Admin Only)

Generate an activation link that users can click:

```bash
curl -X POST "https://prism-backend-bwfx.onrender.com/api/v1/activation/generate-activation-link?email=user@example.com" \
  -H "X-Admin-Key: your-admin-key"
```

### Method 4: Batch Activation (Admin Only)

Activate multiple pending users at once:

```bash
# Activate up to 100 pending users
curl -X POST "https://prism-backend-bwfx.onrender.com/api/v1/activation/batch-activate" \
  -H "X-Admin-Key: your-admin-key"

# Activate specific number of users
curl -X POST "https://prism-backend-bwfx.onrender.com/api/v1/activation/batch-activate?limit=10" \
  -H "X-Admin-Key: your-admin-key"
```

### Method 5: Check User Status

Check if a user needs activation:

```bash
curl -X GET https://prism-backend-bwfx.onrender.com/api/v1/activation/status/user@example.com
```

## Setting Up Admin Access

### 1. Set Admin API Key (Production)

In your production environment (Render), set the following environment variable:

```bash
ADMIN_API_KEY=your-secure-admin-key-here
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Set Admin Activation Key (Alternative)

For the simple activation endpoint, set:

```bash
ADMIN_ACTIVATION_KEY=your-activation-key-here
```

## Security Considerations

### Production Environment

1. **Always use HTTPS** for all activation requests
2. **Set strong admin keys** using cryptographically secure random values
3. **Monitor activation logs** for suspicious activity
4. **Rate limit activation endpoints** to prevent abuse
5. **Use IP whitelisting** for admin endpoints if possible

### Development Environment

1. **AUTO_ACTIVATE_USERS**: Set to `true` to auto-activate on login
2. **EMAIL_VERIFICATION_REQUIRED**: Set to `false` to skip email verification
3. **Use simple activation endpoint** without authentication

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check if the activation endpoint is properly imported in router.py
   - Verify database connection is working
   - Check backend logs for specific errors

2. **User not found**
   - Verify the email address is correct
   - Check if user exists in database
   - Ensure user registration was successful

3. **Already active**
   - User is already activated
   - No action needed

4. **Invalid admin key**
   - Verify ADMIN_API_KEY is set in environment
   - Check you're using the correct key
   - Ensure no extra spaces or characters

## Quick Activation Scripts

### Activate Single User
```bash
#!/bin/bash
EMAIL="user@example.com"
API_URL="https://prism-backend-bwfx.onrender.com"

# For development
curl -X POST "$API_URL/api/v1/activation/activate/$EMAIL"

# For production with admin key
curl -X POST "$API_URL/api/v1/activation/activate?email=$EMAIL" \
  -H "X-Admin-Key: $ADMIN_API_KEY"
```

### List and Activate Pending Users
```bash
#!/bin/bash
API_URL="https://prism-backend-bwfx.onrender.com"
ADMIN_KEY="your-admin-key"

# List pending users
echo "Pending users:"
curl -X GET "$API_URL/api/v1/activation/pending-users" \
  -H "X-Admin-Key: $ADMIN_KEY"

# Activate all pending users
echo -e "\n\nActivating pending users..."
curl -X POST "$API_URL/api/v1/activation/batch-activate" \
  -H "X-Admin-Key: $ADMIN_KEY"
```

## Best Practices

1. **For Production Deployments**:
   - Configure proper email service (SendGrid, AWS SES, etc.)
   - Use activation endpoints only as backup
   - Implement proper audit logging
   - Set up monitoring for failed activations

2. **For Development**:
   - Use AUTO_ACTIVATE_USERS=true
   - Disable email verification requirement
   - Use simple activation endpoint

3. **For Testing**:
   - Create test users with known emails
   - Use batch activation for multiple test accounts
   - Clear test data regularly

## Environment Variables Reference

```bash
# Email verification settings
EMAIL_VERIFICATION_REQUIRED=true  # Set to false to disable
AUTO_ACTIVATE_USERS=false        # Set to true in dev to auto-activate

# Admin access
ADMIN_API_KEY=secure-key-here    # For production admin endpoints
ADMIN_ACTIVATION_KEY=dev-key     # For simple activation endpoint

# Email service (when available)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Next Steps

1. **Configure Email Service**: Set up proper email verification for production
2. **Monitor Activations**: Set up logging and monitoring for activation events
3. **Implement Rate Limiting**: Protect activation endpoints from abuse
4. **Add 2FA**: Consider two-factor authentication for enhanced security
5. **Audit Trail**: Implement comprehensive audit logging for compliance