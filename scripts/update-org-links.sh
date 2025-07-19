#!/bin/bash

# Script to update any hardcoded links to /app/organizations

echo "🔍 Searching for hardcoded organization links..."
echo ""

# Find all references to /app/organizations
echo "Files containing '/app/organizations' references:"
grep -r "/app/organizations" src --include="*.tsx" --include="*.ts" | grep -v "organizations/new" | grep -v "node_modules" || echo "✅ No hardcoded links found"

echo ""
echo "📝 Manual Update Guide:"
echo ""
echo "If you find any hardcoded links, update them as follows:"
echo ""
echo "OLD: /app/organizations"
echo "NEW: /app/account?tab=organizations"
echo ""
echo "OLD: /app/organizations/[id]"
echo "NEW: /app/account?tab=organizations&org=[id]"
echo ""
echo "Note: Links to /app/organizations/new should remain unchanged"
echo ""
echo "✨ The redirect at /app/organizations will handle backward compatibility"