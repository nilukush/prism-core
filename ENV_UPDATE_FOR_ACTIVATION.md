# Environment Configuration Update for User Activation

## Quick Fix - Add to Your .env File

Add these lines to your `.env` file to enable easy user activation in development:

```bash
# User Activation Settings
ENVIRONMENT=development
AUTO_ACTIVATE_USERS=true
EMAIL_VERIFICATION_REQUIRED=false
ALLOW_UNVERIFIED_LOGIN=true
ADMIN_ACTIVATION_KEY=prism-admin-activation-2024
DISABLE_DEV_ACTIVATION=false
```

## What Each Setting Does

- **ENVIRONMENT=development**: Enables development mode features
- **AUTO_ACTIVATE_USERS=true**: Automatically activates users when they try to login
- **EMAIL_VERIFICATION_REQUIRED=false**: Skips email verification requirement
- **ALLOW_UNVERIFIED_LOGIN=true**: Allows pending users to login
- **ADMIN_ACTIVATION_KEY**: Secret key for manual admin activation
- **DISABLE_DEV_ACTIVATION=false**: Enables the /activate/dev endpoint

## For Different Environments

### Development (.env.development)
```bash
ENVIRONMENT=development
AUTO_ACTIVATE_USERS=true
EMAIL_VERIFICATION_REQUIRED=false
ALLOW_UNVERIFIED_LOGIN=true
DISABLE_DEV_ACTIVATION=false
```

### Staging (.env.staging)
```bash
ENVIRONMENT=staging
AUTO_ACTIVATE_USERS=false
EMAIL_VERIFICATION_REQUIRED=true
ALLOW_UNVERIFIED_LOGIN=false
ADMIN_ACTIVATION_KEY=staging-admin-key-change-this
DISABLE_DEV_ACTIVATION=true
```

### Production (.env.production)
```bash
ENVIRONMENT=production
AUTO_ACTIVATE_USERS=false
EMAIL_VERIFICATION_REQUIRED=true
ALLOW_UNVERIFIED_LOGIN=false
ADMIN_ACTIVATION_KEY=<strong-random-key>
DISABLE_DEV_ACTIVATION=true
```

## After Adding These Settings

1. Restart your backend server
2. New users will be auto-activated on login (in development)
3. You can manually activate users using the CLI or API

## Test It Works

```bash
# Check if auto-activation is enabled
curl http://localhost:8000/api/v1/activation/status/test@example.com

# The response will show the current environment
```