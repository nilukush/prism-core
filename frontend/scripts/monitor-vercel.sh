#!/bin/bash

echo "=== Vercel Deployment Monitor ==="
echo ""

# Check current git status
echo "📍 Current Git Status:"
git status --short
echo ""

# Show current commit
echo "📝 Current Commit:"
git log --oneline -1
echo ""

# Check if vercel.json has the correct install command
echo "🔧 Vercel Configuration (vercel.json):"
grep -A1 -B1 "installCommand" vercel.json
echo ""

# Check package.json for any issues
echo "📦 Package.json scripts:"
grep -A5 '"scripts"' package.json
echo ""

# Check if package-lock.json exists and its modification time
echo "🔒 Package-lock.json status:"
if [ -f "package-lock.json" ]; then
    ls -la package-lock.json
    echo "Last modified: $(stat -f "%Sm" package-lock.json 2>/dev/null || stat -c "%y" package-lock.json 2>/dev/null)"
else
    echo "package-lock.json not found!"
fi
echo ""

# Try to run npm install with the same command Vercel would use
echo "🔄 Testing npm install command:"
echo "Running: npm install --legacy-peer-deps --force --dry-run"
npm install --legacy-peer-deps --force --dry-run 2>&1 | head -20
echo ""

# Check for any npm cache issues
echo "💾 NPM Cache info:"
npm cache verify
echo ""

# If logged into Vercel, try to get deployment info
if command -v vercel &> /dev/null; then
    echo "🚀 Attempting to get Vercel deployment info..."
    echo "(This requires being logged into Vercel CLI)"
    vercel ls --limit 5 2>&1 || echo "Not logged into Vercel CLI"
fi