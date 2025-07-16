# 🚨 URGENT: Vercel NPM Fix

## The Issue
npm is URL-encoding package names incorrectly:
- `@radix-ui/react-skeleton` → `@radix-ui%2freact-skeleton`
- This causes 404 errors

## IMMEDIATE FIX in Vercel Dashboard

### Option 1: Force npm to use legacy resolution
1. Go to Vercel Dashboard → Settings → Build & Development
2. Change Install Command to:
   ```
   npm install --legacy-peer-deps --force
   ```

### Option 2: Use Yarn
1. Change Install Command to:
   ```
   yarn install
   ```

### Option 3: Use pnpm
1. Change Install Command to:
   ```
   npx pnpm install
   ```

### Option 4: Skip problematic packages
1. Create a custom install script
2. Change Install Command to:
   ```
   npm install --legacy-peer-deps || true
   ```

## Root Cause
This is a known issue when:
- npm version mismatch between local and deployment
- Proxy or CDN incorrectly encodes URLs
- Package registry configuration issues

## Quick Test
Try deploying with this in Build Command:
```
npm --version && npm config get registry && npm run build
```

This will show what npm version and registry Vercel is using.

---

**TRY OPTION 1 FIRST** - It's the quickest fix!