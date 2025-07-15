# Authentication Error Handling Guide

This document describes the enterprise-grade authentication error handling implementation for the PRISM platform.

## Overview

The authentication system now gracefully handles "No refresh token available" errors and other authentication issues without throwing console errors. The implementation follows NextAuth.js best practices and includes:

- Graceful error handling without console errors
- Session cleanup utilities
- Multi-tab refresh token deduplication
- Comprehensive error monitoring
- User-friendly error recovery

## Error Types

The system handles three main authentication error types:

1. **NoRefreshToken**: Occurs when a refresh token is not available (common with some OAuth providers)
2. **RefreshTokenExpired**: The refresh token has expired and the user must re-authenticate
3. **RefreshAccessTokenError**: Generic error during token refresh (might be temporary)

## Implementation Details

### 1. Auth Configuration (`/src/lib/auth.ts`)

The auth configuration has been updated to:
- Handle missing refresh tokens gracefully without throwing errors
- Add request IDs for debugging multi-tab scenarios
- Implement a 5-minute buffer before token expiry
- Provide detailed logging with `[Auth]` prefix
- Return specific error types instead of generic errors

### 2. Authentication Utilities (`/src/lib/auth-utils.ts`)

Provides utility functions for:
- Checking session errors
- Determining if errors are recoverable
- Clearing sessions and redirecting
- Managing refresh deduplication across tabs

### 3. Error Handler Hook (`/src/hooks/use-auth-error-handler.ts`)

A React hook that:
- Monitors sessions for authentication errors
- Automatically handles errors based on type
- Provides manual error handling methods
- Integrates with your notification system

### 4. Auth Error Provider (`/src/components/providers/auth-error-provider.tsx`)

A provider component that should be added to your root layout:

```tsx
import { AuthErrorProvider } from '@/components/providers/auth-error-provider'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <SessionProvider>
          <AuthErrorProvider>
            {children}
          </AuthErrorProvider>
        </SessionProvider>
      </body>
    </html>
  )
}
```

### 5. Session Clear API (`/src/app/api/auth/clear-session/route.ts`)

An API endpoint for forcefully clearing all authentication cookies:
- POST `/api/auth/clear-session`
- Clears all NextAuth-related cookies
- Handles different cookie domains
- Prevents response caching

### 6. Updated Middleware (`/middleware.ts`)

The middleware now:
- Checks for authentication errors in tokens
- Distinguishes between recoverable and unrecoverable errors
- Allows access with warnings for recoverable errors
- Redirects with error parameters for unrecoverable errors

## Usage

### Manual Session Clearing

You can clear sessions in several ways:

1. **Via npm script**:
   ```bash
   npm run auth:clear-session
   ```

2. **Programmatically**:
   ```ts
   import { clearSessionAndRedirect } from '@/lib/auth-utils'
   
   // Clear session and redirect to login
   await clearSessionAndRedirect('/auth/login')
   ```

3. **Using the hook**:
   ```tsx
   import { useAuthErrorHandler } from '@/hooks/use-auth-error-handler'
   
   function MyComponent() {
     const { forceClearSession } = useAuthErrorHandler()
     
     const handleLogout = async () => {
       await forceClearSession()
     }
   }
   ```

### Handling Auth Errors in Components

```tsx
import { useAuthErrorHandler } from '@/hooks/use-auth-error-handler'

function MyComponent() {
  const { hasError, error, handleError } = useAuthErrorHandler({
    onError: (error) => {
      console.log('Auth error detected:', error)
    },
    showNotifications: true,
    autoHandle: true
  })
  
  if (hasError) {
    return <div>Authentication error: {error}</div>
  }
  
  // ... rest of component
}
```

## Error Flow

1. **Token Refresh Attempt**:
   - JWT callback checks if token needs refresh (5 min before expiry)
   - If no refresh token available, returns `NoRefreshToken` error
   - If refresh fails, returns appropriate error type

2. **Error Detection**:
   - Session callback passes error to client
   - Middleware checks for unrecoverable errors
   - AuthErrorProvider monitors for errors

3. **Error Handling**:
   - Recoverable errors: User continues but may see warnings
   - Unrecoverable errors: User is redirected to login
   - All errors are logged for monitoring

## Debugging

Enable debug logging by setting:
```env
NODE_ENV=development
```

Look for `[Auth]` prefixed messages in console:
- `[Auth] No refresh token available for token refresh`
- `[Auth] Attempting token refresh (request: xyz123)`
- `[Auth] Token refresh successful/failed`

## Best Practices

1. **Always use the AuthErrorProvider** in your root layout
2. **Monitor auth errors** in production using the onError callback
3. **Clear sessions** when users report authentication issues
4. **Use request IDs** to track issues across multiple tabs
5. **Handle errors gracefully** without disrupting user experience

## Troubleshooting

### "No refresh token available" errors

This typically happens when:
1. OAuth provider doesn't provide refresh tokens
2. Session was created before refresh token support
3. Session data is corrupted

**Solution**: Clear the session using the provided utilities

### Multiple tab refresh issues

The implementation includes deduplication to prevent race conditions when multiple tabs try to refresh simultaneously.

### Persistent authentication loops

If users experience authentication loops:
1. Clear all sessions: `npm run auth:clear-all`
2. Check for cookie domain issues
3. Verify NEXTAUTH_SECRET hasn't changed

## Security Considerations

1. **Refresh tokens are never exposed to the client**
2. **All cookies use httpOnly and secure flags**
3. **Error messages don't expose sensitive information**
4. **Session clearing requires authentication** (except via direct cookie manipulation)

## Future Enhancements

1. Implement database-based session clearing for `--all` option
2. Add metrics for authentication error rates
3. Implement automatic retry with exponential backoff
4. Add support for custom error pages