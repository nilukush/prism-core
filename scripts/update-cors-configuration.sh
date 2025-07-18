#!/bin/bash

# Update CORS Configuration for PRISM Backend
# This script updates the CORS configuration to allow both Vercel URLs

echo "🔧 Updating CORS Configuration for PRISM Backend"
echo "================================================"

# Define the allowed origins
ALLOWED_ORIGINS="https://prism-9z5biinym-nilukushs-projects.vercel.app,https://prism-frontend-kappa.vercel.app,http://localhost:3000,http://localhost:3100"

echo ""
echo "📋 New CORS Allowed Origins:"
echo "  - https://prism-9z5biinym-nilukushs-projects.vercel.app (new production)"
echo "  - https://prism-frontend-kappa.vercel.app (old domain)"
echo "  - http://localhost:3000 (local development)"
echo "  - http://localhost:3100 (alternative local port)"

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo ""
    echo "⚠️  Render CLI not found. Please install it first:"
    echo "   curl -L https://render.com/install | sh"
    echo ""
    echo "Or update the environment variable manually in Render dashboard:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Select your 'prism-backend' service"
    echo "3. Go to Environment tab"
    echo "4. Update CORS_ORIGINS with:"
    echo "   $ALLOWED_ORIGINS"
    exit 1
fi

echo ""
echo "🔄 Updating environment variable on Render..."

# Update the environment variable
render env:set CORS_ORIGINS="$ALLOWED_ORIGINS" --service prism-backend

if [ $? -eq 0 ]; then
    echo "✅ CORS configuration updated successfully!"
    echo ""
    echo "🚀 The backend will automatically redeploy with the new configuration."
    echo ""
    echo "📝 Note: The backend expects CORS_ORIGINS, not CORS_ALLOWED_ORIGINS"
    echo "   Make sure to use the correct variable name."
else
    echo "❌ Failed to update CORS configuration"
    echo ""
    echo "Please update manually in the Render dashboard:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Select 'prism-backend' service"
    echo "3. Go to Environment tab"
    echo "4. Add/Update CORS_ORIGINS with:"
    echo "   $ALLOWED_ORIGINS"
fi

echo ""
echo "🔍 Testing CORS configuration..."
echo "Once the service redeploys, you can test with:"
echo ""
echo "curl -H 'Origin: https://prism-9z5biinym-nilukushs-projects.vercel.app' \\"
echo "     -H 'Access-Control-Request-Method: GET' \\"
echo "     -H 'Access-Control-Request-Headers: X-Requested-With' \\"
echo "     -X OPTIONS https://prism-backend-bwfx.onrender.com/health -v"