#!/bin/bash

# Emergency fix for Vercel npm issue

cd frontend

echo "Removing problematic package and using pnpm..."

# Remove the package-lock.json that might be corrupted
rm -f package-lock.json

# Use pnpm which handles scoped packages better
npm install -g pnpm

# Install with pnpm
pnpm install

# Commit the changes
cd ..
git add -A
git commit -m "Fix: Switch to pnpm to resolve npm URL encoding issue

- npm was encoding @radix-ui package URLs incorrectly
- Switched to pnpm which handles scoped packages properly
- This fixes Vercel deployment npm 404 errors"
git push

echo "Done! Now redeploy on Vercel with pnpm"